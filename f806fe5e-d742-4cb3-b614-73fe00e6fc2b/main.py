"""ORB v2 — core fixes (recommendations 1, 2, 4) + backtest logging.

Changes from v1:
  1. Enter once per session — no flips. First valid breakout wins.
  2. Breakout buffer = 10% of opening-range width (adaptive to volatility).
  4. Stop at the opposite side of the opening range — if stopped out,
     stay flat for the rest of the day (no re-entry).

Still uses SPXL (long) / SPXS (short) for 3x expression.

Logging surface (each event fires at most once per session, only when the
latest bar IS the event bar — surmount.run() is stateless and re-derives
the day every call, so this prevents duplicate emissions):

  [ORB-OR]    OR completion: bounds, buffer, OR-bar volume avg.
  [ORB-ENTRY] Entry trigger: bar OHLCV, breakout magnitude, breakout-bar
              volume vs post-OR rolling avg.
  [ORB-EXIT]  Stop-out OR EOD-hold (TYPE=stop|eod): self-contained trade
              record (entry context + exit context + signed P&L%).
  [ORB-NOSIG] No entry by 15:50 ET: max excess above OH / below OL across
              the session — quantifies how close we got.

The volume ratio (RATIO / ENTRY_RATIO / EXIT_RATIO) compares bar volume
to the rolling avg of post-OR bars BEFORE the bar. For the very first
post-OR bar, falls back to OR-bar avg (small-N caveat).
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

        opening_range_bars = 6        # first 30 min on 5-min candles
        flat_time = time(15, 55)
        eod_log_time = time(15, 50)   # last bar before flat — EOD log fires here

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
        or_width = opening_high - opening_low
        buffer = 0.10 * or_width
        or_complete_ts = todays[opening_range_bars - 1][0]
        or_volumes = [float(b.get("volume", 0)) for b in opening_slice]
        or_vol_avg = sum(or_volumes) / len(or_volumes) if or_volumes else 0.0

        if latest_ts == or_complete_ts:
            log(
                "[ORB-OR] {date} OH={oh:.2f} OL={ol:.2f} WIDTH={w:.4f} "
                "BUFFER={b:.4f} OR_VOL_AVG={va:.0f}".format(
                    date=session_date,
                    oh=opening_high,
                    ol=opening_low,
                    w=or_width,
                    b=buffer,
                    va=or_vol_avg,
                )
            )

        direction = None
        stopped_out = False
        entry_direction = None
        entry_ts = None
        entry_bar = None
        entry_close = None
        entry_post_or_avg_vol = None
        exit_ts = None
        exit_bar = None
        exit_post_or_avg_vol = None
        post_or_volumes = []
        max_up_excess = float("-inf")
        max_dn_excess = float("-inf")

        for ts, b in todays[opening_range_bars:]:
            if stopped_out:
                break
            close_px = float(b["close"])
            bar_vol = float(b.get("volume", 0))

            if post_or_volumes:
                rolling_avg = sum(post_or_volumes) / len(post_or_volumes)
            else:
                rolling_avg = or_vol_avg

            up_excess = close_px - opening_high - buffer
            dn_excess = opening_low - buffer - close_px
            if up_excess > max_up_excess:
                max_up_excess = up_excess
            if dn_excess > max_dn_excess:
                max_dn_excess = dn_excess

            if direction is None:
                if close_px > opening_high + buffer:
                    direction = "long"
                    entry_direction = "long"
                    entry_ts = ts
                    entry_bar = b
                    entry_close = close_px
                    entry_post_or_avg_vol = rolling_avg
                elif close_px < opening_low - buffer:
                    direction = "short"
                    entry_direction = "short"
                    entry_ts = ts
                    entry_bar = b
                    entry_close = close_px
                    entry_post_or_avg_vol = rolling_avg
            elif direction == "long":
                if close_px < opening_low - buffer:
                    exit_ts = ts
                    exit_bar = b
                    exit_post_or_avg_vol = rolling_avg
                    direction = None
                    stopped_out = True
            elif direction == "short":
                if close_px > opening_high + buffer:
                    exit_ts = ts
                    exit_bar = b
                    exit_post_or_avg_vol = rolling_avg
                    direction = None
                    stopped_out = True

            post_or_volumes.append(bar_vol)

        if entry_ts == latest_ts and entry_bar is not None:
            if entry_direction == "long":
                excess = entry_close - opening_high - buffer
            else:
                excess = opening_low - buffer - entry_close
            entry_vol = float(entry_bar.get("volume", 0))
            ratio = entry_vol / entry_post_or_avg_vol if entry_post_or_avg_vol else 0.0
            log(
                "[ORB-ENTRY] {ts} DIR={d} O={o:.2f} H={h:.2f} L={l:.2f} C={c:.2f} "
                "OH={oh:.2f} OL={ol:.2f} BUF={b:.4f} EXCESS={ex:.4f} "
                "VOL={v:.0f} POST_OR_AVG={pa:.0f} RATIO={r:.2f}".format(
                    ts=entry_ts,
                    d=entry_direction.upper(),
                    o=float(entry_bar["open"]),
                    h=float(entry_bar["high"]),
                    l=float(entry_bar["low"]),
                    c=entry_close,
                    oh=opening_high,
                    ol=opening_low,
                    b=buffer,
                    ex=excess,
                    v=entry_vol,
                    pa=entry_post_or_avg_vol or 0,
                    r=ratio,
                )
            )

        if exit_ts == latest_ts and exit_bar is not None and entry_close is not None:
            exit_close = float(exit_bar["close"])
            if entry_direction == "long":
                pnl_pct = (exit_close - entry_close) / entry_close
            else:
                pnl_pct = (entry_close - exit_close) / entry_close
            entry_vol = float(entry_bar.get("volume", 0))
            exit_vol = float(exit_bar.get("volume", 0))
            entry_ratio = entry_vol / entry_post_or_avg_vol if entry_post_or_avg_vol else 0.0
            exit_ratio = exit_vol / exit_post_or_avg_vol if exit_post_or_avg_vol else 0.0
            bars_in_trade = sum(
                1 for ts2, _ in todays[opening_range_bars:]
                if entry_ts < ts2 <= exit_ts
            )
            log(
                "[ORB-EXIT] {ts} TYPE=stop DIR={d} ENTRY_TS={ets} BARS={n} "
                "ENTRY_PX={ep:.2f} EXIT_PX={xp:.2f} PNL_PCT={pnl:.4f} "
                "ENTRY_RATIO={er:.2f} EXIT_RATIO={xr:.2f}".format(
                    ts=exit_ts,
                    d=entry_direction.upper(),
                    ets=entry_ts,
                    n=bars_in_trade,
                    ep=entry_close,
                    xp=exit_close,
                    pnl=pnl_pct,
                    er=entry_ratio,
                    xr=exit_ratio,
                )
            )

        if (
            latest_ts.time() == eod_log_time
            and direction is not None
            and entry_close is not None
        ):
            current_bar = todays[-1][1]
            exit_close = float(current_bar["close"])
            if entry_direction == "long":
                pnl_pct = (exit_close - entry_close) / entry_close
            else:
                pnl_pct = (entry_close - exit_close) / entry_close
            entry_vol = float(entry_bar.get("volume", 0))
            exit_vol = float(current_bar.get("volume", 0))
            prior_post_or = post_or_volumes[:-1]
            exit_avg = (
                sum(prior_post_or) / len(prior_post_or) if prior_post_or else or_vol_avg
            )
            entry_ratio = entry_vol / entry_post_or_avg_vol if entry_post_or_avg_vol else 0.0
            exit_ratio = exit_vol / exit_avg if exit_avg else 0.0
            bars_in_trade = sum(
                1 for ts2, _ in todays[opening_range_bars:]
                if entry_ts < ts2 <= latest_ts
            )
            log(
                "[ORB-EXIT] {ts} TYPE=eod DIR={d} ENTRY_TS={ets} BARS={n} "
                "ENTRY_PX={ep:.2f} EXIT_PX={xp:.2f} PNL_PCT={pnl:.4f} "
                "ENTRY_RATIO={er:.2f} EXIT_RATIO={xr:.2f}".format(
                    ts=latest_ts,
                    d=entry_direction.upper(),
                    ets=entry_ts,
                    n=bars_in_trade,
                    ep=entry_close,
                    xp=exit_close,
                    pnl=pnl_pct,
                    er=entry_ratio,
                    xr=exit_ratio,
                )
            )

        if latest_ts.time() == eod_log_time and entry_ts is None:
            log(
                "[ORB-NOSIG] {date} MAX_UP_EXCESS={mu:.4f} MAX_DN_EXCESS={md:.4f}".format(
                    date=session_date,
                    mu=max_up_excess if max_up_excess != float("-inf") else 0.0,
                    md=max_dn_excess if max_dn_excess != float("-inf") else 0.0,
                )
            )

        if direction == "long":
            return TargetAllocation({"SPXL": 1.0, "SPXS": 0.0, "SPY": 0.0})
        if direction == "short":
            return TargetAllocation({"SPXL": 0.0, "SPXS": 1.0, "SPY": 0.0})
        return TargetAllocation(flat)