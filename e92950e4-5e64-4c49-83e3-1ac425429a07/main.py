from surmount.base_class import Strategy, TargetAllocation
from surmount.logging import log
import pandas as pd
from datetime import datetime, time, timedelta
from collections import defaultdict


class TradingStrategy(Strategy):
    """
    ORB (Opening Range Breakout) using SPXL/SPXS for intraday only.
    - Builds opening range on 1m/5m bars over the first 15–30 minutes.
    - LONG: break above OR high -> SPXL
    - SHORT: break below OR low  -> SPXS
    - Risk scaled for 3x leverage: stop ≈ 0.33 * opening range
    - TP = RR_MULT * risk_unit; exit all by EOD
    - One trade per day; optional weekly stop-out guard
    """

    def __init__(self):
        # === Tunables ===
        self.USE_INTERVAL = "1min"         # "1min" or "5min"
        self.ORB_WINDOW_MINUTES = 30       # 15 or 30
        self.RR_MULT = 1.25                # Take-profit in R (R = 0.33 * opening range)
        self.RISK_FRACTION = 0.33          # 1/3 of OR to account for 3x leverage
        self.MAX_TRADES_PER_DAY = 1
        self.EOD_EXIT_TIME = time(15, 55)  # 5 mins before cash close
        self.LAST_ENTRY_TIME = time(11, 0) # avoid late-day entries
        self.MIN_RANGE_PCT = 0.15 / 100.0  # skip micro ranges (<0.15% of price)
        self.WEEKLY_MAX_STOP_OUTS = 3      # pause after N stop-outs in ISO week

        # === State ===
        self.state = {
            "today": None,
            "or_high": None,
            "or_low": None,
            "or_done": False,
            "entry_side": None,     # "long" or "short"
            "entry_price": None,
            "stop": None,
            "take_profit": None,
            "trades_taken_today": 0,
        }
        self.weekly_stops = defaultdict(int)

    @property
    def assets(self):
        return ["SPXL", "SPXS"]

    @property
    def interval(self):
        return self.USE_INTERVAL

    # ---------- helpers ----------
    def _ts(self, s):
        return pd.to_datetime(s)

    def _today_rows(self, ohlcv, d):
        out = []
        for row in ohlcv:
            if "SPXL" not in row:
                continue
            ts = self._ts(row["SPXL"]["date"])
            if ts.date() == d:
                out.append((ts, row))
        return out

    def _opening_ready(self, ts_rows):
        if not ts_rows:
            return False, None
        day = ts_rows[-1][0].date()
        start = datetime.combine(day, time(9, 30))
        cutoff = start + timedelta(minutes=self.ORB_WINDOW_MINUTES)
        return ts_rows[-1][0] >= cutoff, cutoff

    def _opening_range(self, ts_rows, cutoff):
        day = ts_rows[-1][0].date()
        start = datetime.combine(day, time(9, 30))
        hi, lo = None, None
        for ts, row in ts_rows:
            if start <= ts <= cutoff:
                h = row["SPXL"]["high"]   # SPXL mirrors SPY intraday shape; fine for range
                l = row["SPXL"]["low"]
                hi = h if hi is None else max(hi, h)
                lo = l if lo is None else min(lo, l)
        return hi, lo

    def _week_key(self, ts):
        iso = ts.isocalendar()
        return (iso[0], iso[1])

    def _eod(self, now_ts):
        return now_ts.time() >= self.EOD_EXIT_TIME

    # ---------- strategy ----------
    def run(self, data):
        ohlcv = data.get("ohlcv")
        if not ohlcv or len(ohlcv) < 5:
            return TargetAllocation({})

        last = ohlcv[-1]
        if "SPXL" not in last or "SPXS" not in last:
            return TargetAllocation({})

        now = self._ts(last["SPXL"]["date"])
        today = now.date()

        # New trading day -> reset state
        if self.state["today"] != today:
            self.state = {
                "today": today,
                "or_high": None,
                "or_low": None,
                "or_done": False,
                "entry_side": None,
                "entry_price": None,
                "stop": None,
                "take_profit": None,
                "trades_taken_today": 0,
            }

        # Weekly halt if too many stop-outs
        wk = self._week_key(now)
        if self.weekly_stops[wk] >= self.WEEKLY_MAX_STOP_OUTS:
            return TargetAllocation({"SPXL": 0.0, "SPXS": 0.0})

        rows = self._today_rows(ohlcv, today)
        if not rows:
            return TargetAllocation({})

        # Build opening range
        if not self.state["or_done"]:
            ready, cutoff = self._opening_ready(rows)
            if ready:
                orh, orl = self._opening_range(rows, cutoff)
                if orh is None or orl is None or orh <= orl:
                    return TargetAllocation({})
                self.state["or_high"], self.state["or_low"], self.state["or_done"] = orh, orl, True
            return TargetAllocation({})

        # We have an opening range
        orh, orl = self.state["or_high"], self.state["or_low"]
        price = rows[-1][1]["SPXL"]["close"]

        # Min range filter (use SPXL price; filter is tiny so it’s conservative)
        rng = orh - orl
        if rng <= 0:
            return TargetAllocation({})
        if (rng / max(price, 1e-9)) < self.MIN_RANGE_PCT:
            # skip micro-ranges entirely today
            return TargetAllocation({})

        # Manage open trade (stop/TP/EOD)
        if self.state["entry_side"] is not None:
            stop = self.state["stop"]
            tp = self.state["take_profit"]
            exit_now = False

            if self.state["entry_side"] == "long":
                if price <= stop or price >= tp:
                    exit_now = True
                alloc = {"SPXL": 1.0, "SPXS": 0.0}
            else:
                # For short, we allocate SPXS
                if price >= stop or price <= tp:
                    exit_now = True
                alloc = {"SPXL": 0.0, "SPXS": 1.0}

            if self._eod(now):
                exit_now = True

            if exit_now:
                # Count stop-outs
                if (self.state["entry_side"] == "long" and price <= stop) or \
                   (self.state["entry_side"] == "short" and price >= stop):
                    self.weekly_stops[wk] += 1

                # Flatten & lock day
                self.state["entry_side"] = None
                self.state["entry_price"] = None
                self.state["stop"] = None
                self.state["take_profit"] = None
                self.state["trades_taken_today"] = self.MAX_TRADES_PER_DAY
                return TargetAllocation({"SPXL": 0.0, "SPXS": 0.0})

            return TargetAllocation(alloc)

        # No trade open; if already used daily quota, stand down
        if self.state["trades_taken_today"] >= self.MAX_TRADES_PER_DAY:
            return TargetAllocation({})

        # Disallow fresh entries after LAST_ENTRY_TIME
        if now.time() >= self.LAST_ENTRY_TIME:
            return TargetAllocation({})

        # Entry logic (use SPXL price for breakout)
        risk_unit = rng * self.RISK_FRACTION  # scaled for 3x leverage

        # Long: break of OR high -> SPXL
        if price > orh:
            entry = price
            stop = entry - risk_unit
            tp   = entry + self.RR_MULT * risk_unit
            if stop < entry < tp:
                self.state["entry_side"] = "long"
                self.state["entry_price"] = entry
                self.state["stop"] = stop
                self.state["take_profit"] = tp
                self.state["trades_taken_today"] += 1
                return TargetAllocation({"SPXL": 1.0, "SPXS": 0.0})

        # Short: break of OR low -> SPXS
        if price < orl:
            entry = price
            stop = entry + risk_unit
            tp   = entry - self.RR_MULT * risk_unit
            if tp < entry < stop:
                self.state["entry_side"] = "short"
                self.state["entry_price"] = entry
                self.state["stop"] = stop
                self.state["take_profit"] = tp
                self.state["trades_taken_today"] += 1
                return TargetAllocation({"SPXL": 0.0, "SPXS": 1.0})

        return TargetAllocation({})