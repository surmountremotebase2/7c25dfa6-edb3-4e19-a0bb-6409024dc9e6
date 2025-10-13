from surmount.base_class import Strategy, TargetAllocation
from surmount.logging import log
import pandas as pd
from datetime import datetime, time, timedelta
from collections import defaultdict


class TradingStrategy(Strategy):
    """
    Opening Range Breakout (ORB) for SPY.

    Core behavior
    -------------
    1) During the first ORB_WINDOW_MINUTES of RTH (09:30 ET), build the opening range [high, low].
    2) After the window closes:
       - Go LONG SPY on a close > OR_high.
       - Go SHORT (via SPXS) on a close < OR_low.
       Only ONE entry per day.
    3) Risk management:
       - Stop: 1x opening-range size.
       - Take-profit: RR_MULT * opening-range size (default 1.5R).
       - Exit all at 15:55 ET if still in a position.
       - Daily kill-switch after a win or loss (one trade/day).
       - Weekly kill-switch if too many losses this ISO week.

    Tweakable parameters at the top of __init__.
    """

    def __init__(self):
        # === Parameters you can tweak ===
        self.USE_INTERVAL = "1min"          # "1min" or "5min"
        self.ORB_WINDOW_MINUTES = 30        # 15 or 30 (tested with 30 by default)
        self.RR_MULT = 1.5                  # Risk:Reward, e.g., 1:1.5
        self.MAX_TRADES_PER_DAY = 1         # keep this to 1 for classic ORB
        self.EOD_EXIT_TIME = time(15, 55)   # Liquidate 5 minutes before cash close
        self.WEEKLY_MAX_STOP_OUTS = 3       # After this many stop-outs in a week, pause
        self.TIMEZONE_HINT = "America/New_York"  # For documentation/logging only

        # === Internal state ===
        self.state = {
            "today": None,
            "or_high": None,
            "or_low": None,
            "or_done": False,
            "entry_side": None,       # "long" / "short" / None
            "entry_price": None,
            "stop": None,
            "take_profit": None,
            "trades_taken_today": 0,
        }

        # Track weekly stop-outs by ISO year-week
        self.weekly_stops = defaultdict(int)

    @property
    def assets(self):
        # Long via SPY, short via SPXS (3x inverse). Swap SPXS->SH if you prefer 1x inverse.
        return ["SPY", "SPXS"]

    @property
    def interval(self):
        return self.USE_INTERVAL  # "1min" or "5min"

    # ---------- Helpers ----------
    def _parse_ts(self, s):
        # Surmount OHLCV examples show ISO-like strings; rely on pandas robustness
        return pd.to_datetime(s)

    def _today_filter(self, bars, today_date):
        # Return only today's bars by local date (naive compare on date component)
        out = []
        for row in bars:
            ts = self._parse_ts(row["SPY"]["date"])
            if ts.date() == today_date:
                out.append((ts, row))
        return out

    def _opening_range_ready(self, ts_list):
        # True if we have reached the end of the opening window (09:30 + window)
        # We assume RTH starts 09:30 ET.
        # Compute cutoff = date@09:30 + ORB_WINDOW_MINUTES
        if not ts_list:
            return False, None
        day = ts_list[-1][0].date()
        or_start = datetime.combine(day, time(9, 30))
        cutoff = or_start + timedelta(minutes=self.ORB_WINDOW_MINUTES)
        # We are "ready" once the *current* timestamp >= cutoff (window complete)
        ready = ts_list[-1][0] >= cutoff
        return ready, cutoff

    def _calc_opening_range(self, ts_rows, cutoff_ts):
        # Calculate high/low over [09:30, cutoff_ts]
        if not ts_rows:
            return None, None
        day = ts_rows[-1][0].date()
        or_start = datetime.combine(day, time(9, 30))
        hi = None
        lo = None
        for ts, row in ts_rows:
            if ts >= or_start and ts <= cutoff_ts:
                h = row["SPY"]["high"]
                l = row["SPY"]["low"]
                hi = h if hi is None else max(hi, h)
                lo = l if lo is None else min(lo, l)
        return hi, lo

    def _is_eod_exit(self, now_ts):
        return now_ts.time() >= self.EOD_EXIT_TIME

    def _current_price(self, row):
        # use close as latest tradable proxy
        return row["SPY"]["close"]

    def _week_key(self, ts):
        # ISO year-week
        iso = ts.isocalendar()  # (year, week, weekday)
        return (iso[0], iso[1])

    # ---------- Strategy ----------
    def run(self, data):
        ohlcv = data.get("ohlcv")
        if not ohlcv or len(ohlcv) < 5:
            return TargetAllocation({})  # not enough data yet

        last = ohlcv[-1]
        if "SPY" not in last:
            return TargetAllocation({})

        now_ts = self._parse_ts(last["SPY"]["date"])
        today_date = now_ts.date()

        # Day rollover: reset daily state
        if self.state["today"] != today_date:
            self.state.update({
                "today": today_date,
                "or_high": None,
                "or_low": None,
                "or_done": False,
                "entry_side": None,
                "entry_price": None,
                "stop": None,
                "take_profit": None,
                "trades_taken_today": 0,
            })

        # Weekly halt if too many stop-outs
        week_key = self._week_key(now_ts)
        if self.weekly_stops[week_key] >= self.WEEKLY_MAX_STOP_OUTS:
            # No trading this week; flatten
            return TargetAllocation({"SPY": 0.0, "SPXS": 0.0})

        # Filter today's bars for SPY
        today_rows = self._today_filter(ohlcv, today_date)
        if not today_rows:
            return TargetAllocation({})

        # If we’re not in a trade and the opening range isn’t done, build it
        if not self.state["or_done"]:
            ready, cutoff = self._opening_range_ready(today_rows)
            if ready:
                or_high, or_low = self._calc_opening_range(today_rows, cutoff)
                # If market opened late/holiday irregularities, guard
                if or_high is None or or_low is None or or_high <= or_low:
                    return TargetAllocation({})
                self.state["or_high"] = or_high
                self.state["or_low"] = or_low
                self.state["or_done"] = True
            # Don’t allocate during the window
            return TargetAllocation({})

        # We have an opening range defined
        or_high = self.state["or_high"]
        or_low = self.state["or_low"]
        price = self._current_price(today_rows[-1][1])

        # Manage an open position first (stops/TP/EOD)
        if self.state["entry_side"] is not None:
            # Check stop/TP
            stop = self.state["stop"]
            tp = self.state["take_profit"]

            exit_now = False
            # For simplicity, use close vs levels (intrabar touches not modeled here)
            if self.state["entry_side"] == "long":
                if price <= stop or price >= tp:
                    exit_now = True
            else:  # short (via SPXS)
                if price >= stop or price <= tp:
                    exit_now = True

            # EOD hard exit
            if self._is_eod_exit(now_ts):
                exit_now = True

            if exit_now:
                # Update weekly stop counter if stop was hit
                if (self.state["entry_side"] == "long" and price <= stop) or \
                   (self.state["entry_side"] == "short" and price >= stop):
                    self.weekly_stops[week_key] += 1

                # Flatten and lock out further trades today
                self.state["entry_side"] = None
                self.state["entry_price"] = None
                self.state["stop"] = None
                self.state["take_profit"] = None
                self.state["trades_taken_today"] = self.MAX_TRADES_PER_DAY
                return TargetAllocation({"SPY": 0.0, "SPXS": 0.0})

            # Maintain current allocation while in trade
            if self.state["entry_side"] == "long":
                return TargetAllocation({"SPY": 1.0, "SPXS": 0.0})
            else:
                return TargetAllocation({"SPY": 0.0, "SPXS": 1.0})

        # If we already took a trade today, stand down
        if self.state["trades_taken_today"] >= self.MAX_TRADES_PER_DAY:
            return TargetAllocation({})

        # No open trade; look for breakout entries AFTER the opening window
        rng = or_high - or_low
        if rng <= 0:
            return TargetAllocation({})

        # Breakout logic: enter on close beyond the range
        if price > or_high:
            # Long entry
            entry = price
            stop = entry - rng  # 1R
            tp = entry + (self.RR_MULT * rng)
            # Make sure stop < entry < tp
            if stop < entry < tp:
                self.state["entry_side"] = "long"
                self.state["entry_price"] = entry
                self.state["stop"] = stop
                self.state["take_profit"] = tp
                self.state["trades_taken_today"] += 1
                return TargetAllocation({"SPY": 1.0, "SPXS": 0.0})

        elif price < or_low:
            # Short entry via SPXS
            entry = price
            stop = entry + rng  # 1R
            tp = entry - (self.RR_MULT * rng)
            # Make sure tp < entry < stop
            if tp < entry < stop:
                self.state["entry_side"] = "short"
                self.state["entry_price"] = entry
                self.state["stop"] = stop
                self.state["take_profit"] = tp
                self.state["trades_taken_today"] += 1
                return TargetAllocation({"SPY": 0.0, "SPXS": 1.0})

        # No signal
        return TargetAllocation({})