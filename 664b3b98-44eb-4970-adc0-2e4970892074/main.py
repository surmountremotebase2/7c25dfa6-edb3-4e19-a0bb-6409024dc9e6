"""ORB v3 — full recommendations (1, 2, 3, 4, 5, 6).

Changes from v1:
  1. Enter once per session — no flips. First valid breakout wins.
  2. Breakout buffer = 10% of opening-range width (adaptive to volatility).
  3. Entry window: only enter within 90 min after opening range ends
     (i.e. signals before 11:30 ET). Afternoon breakouts are ignored.
  4. Stop at the opposite side of the opening range — if stopped out,
     stay flat for the rest of the day (no re-entry).
  5. Long-only. Dropped the short leg (SPXS).
  6. 1x expression via SPY directly. Validates the signal before layering
     leverage. If this has a real edge at 1x, swap SPY -> SPXL to scale.
"""

from datetime import datetime, time, timedelta

from surmount.base_class import Strategy, TargetAllocation
from surmount.logging import log


class TradingStrategy(Strategy):

    @property
    def assets(self):
        return ["SPY"]

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
        flat = {"SPY": 0.0}

        ohlcv = data.get("ohlcv") if isinstance(data, dict) else None
        if not ohlcv:
            return TargetAllocation(flat)

        opening_range_bars = 6        # first 30 min on 5-min candles
        entry_window_minutes = 90     # must enter within 90 min after OR ends
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
        buffer = 0.10 * (opening_high - opening_low)

        # Entry cutoff = last bar of opening range + entry_window
        opening_range_end_ts = todays[opening_range_bars - 1][0]
        entry_cutoff_ts = opening_range_end_ts + timedelta(minutes=entry_window_minutes)

        direction = None
        stopped_out = False

        for ts, b in todays[opening_range_bars:]:
            if stopped_out:
                break
            close_px = float(b["close"])

            if direction is None:
                if ts > entry_cutoff_ts:
                    break  # entry window closed, no more chances today
                if close_px > opening_high + buffer:
                    direction = "long"
                # long-only: ignore downside breakouts
            elif direction == "long":
                if close_px < opening_low - buffer:
                    direction = None
                    stopped_out = True

        if direction == "long":
            return TargetAllocation({"SPY": 1.0})
        return TargetAllocation(flat)