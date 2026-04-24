"""ORB v2 — core fixes (recommendations 1, 2, 4).

Changes from v1:
  1. Enter once per session — no flips. First valid breakout wins.
  2. Breakout buffer = 10% of opening-range width (adaptive to volatility).
  4. Stop at the opposite side of the opening range — if stopped out,
     stay flat for the rest of the day (no re-entry).

Still uses SPXL (long) / SPXS (short) for 3x expression.
"""

from datetime import datetime, time

from surmount.base_class import Strategy, TargetAllocation
from surmount.logging import log


class TradingStrategy(Strategy):

    @property
    def assets(self):
        return ["SPY", "SPXL", "SPXS"]

    @property
    def interval(self):
        return "5min"

    def _parse_bar_time(self, raw):
        if raw is None:
            return None
        if isinstance(raw, datetime):
            return raw
        value = str(raw).strip()
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                continue
        return None

    def run(self, data):
        flat = {"SPXL": 0.0, "SPXS": 0.0, "SPY": 0.0}

        ohlcv = data.get("ohlcv") if isinstance(data, dict) else None
        if not ohlcv:
            return TargetAllocation(flat)

        opening_range_bars = 6     # first 30 min on 5-min candles
        flat_time = time(15, 55)

        spy_bars = []
        for row in ohlcv:
            if not isinstance(row, dict):
                continue
            bar = row.get("SPY")
            if not bar:
                continue
            ts = self._parse_bar_time(bar.get("date"))
            if ts is None:
                continue
            spy_bars.append((ts, bar))

        if not spy_bars:
            return TargetAllocation(flat)

        latest_ts = spy_bars[-1][0]
        session_date = latest_ts.date()
        todays = [(ts, b) for ts, b in spy_bars if ts.date() == session_date]

        if latest_ts.time() >= flat_time:
            return TargetAllocation(flat)

        if len(todays) < opening_range_bars:
            return TargetAllocation(flat)

        opening_slice = [b for _, b in todays[:opening_range_bars]]
        opening_high = max(float(b["high"]) for b in opening_slice)
        opening_low = min(float(b["low"]) for b in opening_slice)
        # Adaptive buffer: 10% of opening-range width
        buffer = 0.10 * (opening_high - opening_low)

        direction = None
        stopped_out = False

        for _, b in todays[opening_range_bars:]:
            if stopped_out:
                break
            close_px = float(b["close"])

            if direction is None:
                if close_px > opening_high + buffer:
                    direction = "long"
                elif close_px < opening_low - buffer:
                    direction = "short"
            elif direction == "long":
                if close_px < opening_low - buffer:
                    direction = None
                    stopped_out = True
            elif direction == "short":
                if close_px > opening_high + buffer:
                    direction = None
                    stopped_out = True

        if direction == "long":
            return TargetAllocation({"SPXL": 1.0, "SPXS": 0.0, "SPY": 0.0})
        if direction == "short":
            return TargetAllocation({"SPXL": 0.0, "SPXS": 1.0, "SPY": 0.0})
        return TargetAllocation(flat)