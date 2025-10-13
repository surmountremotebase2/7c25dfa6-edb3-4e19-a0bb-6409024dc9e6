from surmount.base_class import Strategy, TargetAllocation
from surmount.logging import log
import pandas as pd
from datetime import datetime, time, timedelta
from collections import defaultdict


class TradingStrategy(Strategy):
    """
    ORB using SPY as the signal source; executions in SPXL/SPXS (intraday only).
    - Build SPY opening range on 1m/5m over first 15–30 minutes.
    - LONG signal: SPY breaks OR high  -> allocate SPXL
    - SHORT signal: SPY breaks OR low  -> allocate SPXS
    - Risk sized from SPY range: stop = RISK_FRACTION * SPY_range
    - TP = RR_MULT * risk_unit (also in SPY terms); all exits by EOD
    """

    def __init__(self):
        # === Tunables ===
        self.USE_INTERVAL = "1min"          # "1min" or "5min"
        self.ORB_WINDOW_MINUTES = 30        # 15 or 30
        self.RR_MULT = 1.25                 # TP in R; R = RISK_FRACTION * SPY opening range
        self.RISK_FRACTION = 0.5           # ~1/3 of SPY range to account for 3x leverage
        self.MAX_TRADES_PER_DAY = 1
        self.EOD_EXIT_TIME = time(15, 55)   # flatten 5 mins before close
        self.LAST_ENTRY_TIME = time(11, 0)  # avoid late-day entries
        self.MIN_RANGE_PCT = 0.15 / 100.0   # skip micro ranges (<0.15% of SPY price)
        self.WEEKLY_MAX_STOP_OUTS = 3       # pause after N stop-outs in ISO week

        # === State ===
        self.state = {
            "today": None,
            "or_high": None,        # SPY OR high
            "or_low": None,         # SPY OR low
            "or_done": False,
            "entry_side": None,     # "long" or "short"
            "entry_price_spy": None,
            "stop_spy": None,
            "tp_spy": None,
            "trades_taken_today": 0,
        }
        self.weekly_stops = defaultdict(int)

    @property
    def assets(self):
        # SPY for signals; SPXL/SPXS for executions
        return ["SPY", "SPXL", "SPXS"]

    @property
    def interval(self):
        return self.USE_INTERVAL

    # ---------- helpers ----------
    def _ts(self, s):
        return pd.to_datetime(s)

    def _today_rows(self, ohlcv, d):
        # Collect today's rows (by SPY timestamps)
        out = []
        for row in ohlcv:
            if "SPY" not in row:
                continue
            ts = self._ts(row["SPY"]["date"])
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

    def _opening_range_spy(self, ts_rows, cutoff):
        # Compute opening range on SPY
        day = ts_rows[-1][0].date()
        start = datetime.combine(day, time(9, 30))
        hi, lo = None, None
        for ts, row in ts_rows:
            if start <= ts <= cutoff:
                h = row["SPY"]["high"]
                l = row["SPY"]["low"]
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
        # Need SPY as signal, and tradables available
        if "SPY" not in last or "SPXL" not in last or "SPXS" not in last:
            return TargetAllocation({})

        now = self._ts(last["SPY"]["date"])
        today = now.date()

        # New trading day -> reset state
        if self.state["today"] != today:
            self.state = {
                "today": today,
                "or_high": None,
                "or_low": None,
                "or_done": False,
                "entry_side": None,
                "entry_price_spy": None,
                "stop_spy": None,
                "tp_spy": None,
                "trades_taken_today": 0,
            }

        # Weekly halt if too many stop-outs
        wk = self._week_key(now)
        if self.weekly_stops[wk] >= self.WEEKLY_MAX_STOP_OUTS:
            return TargetAllocation({"SPXL": 0.0, "SPXS": 0.0})

        rows = self._today_rows(ohlcv, today)
        if not rows:
            return TargetAllocation({})

        # Build opening range (SPY)
        if not self.state["or_done"]:
            ready, cutoff = self._opening_ready(rows)
            if ready:
                orh, orl = self._opening_range_spy(rows, cutoff)
                if orh is None or orl is None or orh <= orl:
                    return TargetAllocation({})
                self.state["or_high"], self.state["or_low"], self.state["or_done"] = orh, orl, True
            return TargetAllocation({})

        # We have an opening range on SPY
        orh, orl = self.state["or_high"], self.state["or_low"]
        price_spy = rows[-1][1]["SPY"]["close"]

        # Min range filter based on SPY
        rng_spy = orh - orl
        if rng_spy <= 0:
            return TargetAllocation({})
        if (rng_spy / max(price_spy, 1e-9)) < self.MIN_RANGE_PCT:
            return TargetAllocation({})

        # Manage open trade using SPY stop/tp
        if self.state["entry_side"] is not None:
            stop_spy = self.state["stop_spy"]
            tp_spy = self.state["tp_spy"]
            exit_now = False

            if self.state["entry_side"] == "long":
                if price_spy <= stop_spy or price_spy >= tp_spy:
                    exit_now = True
                alloc = {"SPXL": 1.0, "SPXS": 0.0}
            else:
                if price_spy >= stop_spy or price_spy <= tp_spy:
                    exit_now = True
                alloc = {"SPXL": 0.0, "SPXS": 1.0}

            if self._eod(now):
                exit_now = True

            if exit_now:
                # Count stop-outs (in SPY terms)
                if (self.state["entry_side"] == "long" and price_spy <= stop_spy) or \
                   (self.state["entry_side"] == "short" and price_spy >= stop_spy):
                    self.weekly_stops[wk] += 1

                # Flatten & lock day
                self.state["entry_side"] = None
                self.state["entry_price_spy"] = None
                self.state["stop_spy"] = None
                self.state["tp_spy"] = None
                self.state["trades_taken_today"] = self.MAX_TRADES_PER_DAY
                return TargetAllocation({"SPXL": 0.0, "SPXS": 0.0})

            return TargetAllocation(alloc)

        # No trade open; if already used daily quota, stand down
        if self.state["trades_taken_today"] >= self.MAX_TRADES_PER_DAY:
            return TargetAllocation({})

        # Disallow fresh entries after LAST_ENTRY_TIME
        if now.time() >= self.LAST_ENTRY_TIME:
            return TargetAllocation({})

        # Entry logic (SPY signal, SPXL/SPXS execution)
        risk_unit = rng_spy * self.RISK_FRACTION  # SPY-based risk sizing

        # Long: SPY breaks OR high -> buy SPXL
        if price_spy > orh:
            entry_spy = price_spy
            stop_spy = entry_spy - risk_unit
            tp_spy   = entry_spy + self.RR_MULT * risk_unit
            if stop_spy < entry_spy < tp_spy:
                self.state["entry_side"] = "long"
                self.state["entry_price_spy"] = entry_spy
                self.state["stop_spy"] = stop_spy
                self.state["tp_spy"] = tp_spy
                self.state["trades_taken_today"] += 1
                return TargetAllocation({"SPXL": 1.0, "SPXS": 0.0})

        # Short: SPY breaks OR low -> buy SPXS
        if price_spy < orl:
            entry_spy = price_spy
            stop_spy = entry_spy + risk_unit
            tp_spy   = entry_spy - self.RR_MULT * risk_unit
            if tp_spy < entry_spy < stop_spy:
                self.state["entry_side"] = "short"
                self.state["entry_price_spy"] = entry_spy
                self.state["stop_spy"] = stop_spy
                self.state["tp_spy"] = tp_spy
                self.state["trades_taken_today"] += 1
                return TargetAllocation({"SPXL": 0.0, "SPXS": 1.0})

        return TargetAllocation({})