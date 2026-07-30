"""v2.1 — Volatility-scaled intraday momentum. INSTRUMENTATION RELEASE.

Successor to spy_orb/v1 and intraday_momentum/v2. See v2/RESULTS.md for the
run this is responding to.

=== WHAT CHANGED FROM v2, AND WHY ONLY THIS ===

v2 returned +18.13% with Sharpe 1.06 and closed the overnight leak completely
(0 of 236 positions held overnight, vs v1's 189 of 245). But it failed its
pre-registered criteria: mean-trade t = 1.124, and dropping the best 3 of 119
trades took +18.57% to +1.42%. It tied QQQ buy-and-hold. No edge demonstrated.

The response to that is NOT to re-tune parameters on the same year — with 119
trades that is guaranteed to produce a better number and guaranteed to mean
nothing. So v2.1 makes exactly three changes, and then FREEZES:

  1. BUG FIX — counterfactual logging now happens BEFORE the volatility gate.
     In v2, run() returned early on vol-skipped sessions, so the 71 skipped
     sessions produced no counterfactual records and the volatility filter was
     unmeasurable. (Same class of bug as v1's unreachable exit logging.)

  2. RISK_PCT 1.5% -> 1.0%. Justified because 68.1% of v2's trades capped at
     ALLOC=1.0, so two-thirds ran at full notional exactly like v1 and the 1R
     sizing design was never actually exercised. This is "the design was not
     tested", not "1.0% backtests better".

  3. A PRE-SPECIFIED COUNTERFACTUAL GRID (see GRID below), logged but never
     traded. Four binary comparisons, fixed now and not to be extended.

=== THE EXPERIMENTAL DESIGN THIS ENABLES ===

Parameters are FROZEN as of this file. Every subsequent backtest window is
therefore a genuine out-of-sample test — not just of the traded rule, but of
all four grid variants simultaneously, because none of them can be tuned
between runs without invalidating the whole exercise.

This is what makes multiple 2-year windows worth more than one long backtest:
the modal failure mode for this strategy family is one strong period masking
flat or negative ones, and only separate windows expose it.

If a variant beats the traded configuration consistently ACROSS windows, that
is a real finding. If it wins in one window and loses in another, that is
noise, and we will be able to see the difference.

WHY THIS IS NOT JUST "ORB WITH BETTER PARAMETERS"
-------------------------------------------------
v1's +14.9% was not a trading result. Decomposing every bar of its equity curve:
overnight gaps +16.74%, intraday -1.57%, product = +14.9047% (its exact reported
total). 77% of its positions were unintended overnight 3x holds, because the
engine fills a target at the NEXT bar's open and v1 emitted "flat" at 15:55 —
the session's last bar. Worse, the entire overnight leg was 5 gaps: the top 5
contributed +20.71% and the remaining 184 contributed -3.29%.

An offline replay (validated 245/245 against v1's own logs) then screened 18
intraday-flat variants of v1. Every profit factor landed between 0.85 and 1.11.
There is no parameter setting of v1's rule that produces an edge on this data.

So v2 changes the *shape* of the signal rather than its parameters:

  1. ANCHOR: a volatility-scaled band around the session open, not a fixed
     30-minute range. This is the "intraday momentum" family, which has
     materially better evidence than ORB specifically (Gao, Han, Li & Zhou,
     Journal of Financial Economics 2018 — SPY 1993-2013, out-of-sample R^2
     1.4-2.0%, replicated in 12 of 16 developed markets). Unfiltered ORB, by
     contrast, returned Sharpe 0.48 across ~7,000 US stocks 2016-2023 — worse
     than buy-and-hold (Zarattini, Barbon & Aziz).

  2. ORB BECOMES A COMPARISON, NOT THE SIGNAL. TRIGGER selects which rule is
     traded ("band" or "orb"); the other is evaluated and logged every session
     regardless. They are deliberately NOT combined — at realistic volatility
     the band is strictly tighter than the opening range, so an "ORB
     confirmation" gate would never bind and would measure nothing. Running
     them side by side answers the question that actually matters: does the
     opening range add anything over a volatility band?

  3. VOLATILITY REGIME GATE. Lundström (S&P 500 futures, 1991-2010) found ORB
     returns significantly NEGATIVE in the lowest volatility deciles and
     positive in the highest, ~150bp/day decile spread. VOL_FLOOR skips dead
     sessions. The realised distribution is logged so the threshold can be set
     from data instead of guessed.

  4. RISK ARCHITECTURE — all four v1 defects fixed:
       a. Genuinely intraday. FLAT_TIME=15:45 emits flat with 2 bars to spare,
          so the fill lands at 15:50 the SAME DAY. v1 had no intraday exit at
          all: between 15:50 and the next 09:30 there was no exit path, i.e.
          17.5 hours (65+ across a weekend) of unhedged 3x exposure.
       b. Volatility-scaled stop, NOT the opposite side of the range. This is
          about reproducibility, not returns: Concretum ran identical ORB code
          across five data vendors and got $226k-$726k under opposite-side
          (high/low) stops, and convergence under ATR-style stops. A rule whose
          result swings 3x on your data vendor cannot be validated.
       c. 1R POSITION SIZING. v1 was always 100% notional, so risk per trade
          scaled with opening-range width (median 1.27% of account at 3x, max
          4.77%). v2 solves allocation for constant risk per trade.
       d. Entry cutoff, so a position always has time to resolve before flat.

  5. VEHICLE: QQQ family by default. This is a SWITCH, not an addition.
     SPY-QQQ correlation is 0.929 on 5-minute bars and the opening-range signal
     agrees on 84.6% of sessions — at rho=0.93 two instruments give ~1.04
     effective bets, not 2. Trading both is one bet at double size.
     QQQ carries 1.25-1.5x SPY's volatility (more move per fixed cost), and
     SQQQ costs ~1.35bps per dollar of exposure against SPXS's ~2.33bps
     (8.5x SPY) on $348M AUM. SPXS was the most expensive instrument available.

  6. EFFECTIVE LEVERAGE IS 2.8x, NOT 3x. Measured empirically from v1's own
     fills (2.81 long / 2.75 short). The mechanism is disclosed by Direxion:
     exposure is struck at the PRIOR CLOSE, so a mid-morning entry receives
     L(1+r)/(1+L*r), roughly -2% of leverage per +1% move since the prior
     close. Sizing uses the measured figure.

WHAT THIS RUN IS FOR
--------------------
One year and 245 trades cannot distinguish edge from noise (v1's mean trade was
+1.74bp, t=0.607, p=0.54). This strategy is therefore built to MEASURE, not just
to trade. The traded rule is deliberately simple; the complexity lives in the
logs, which cost nothing statistically. Every session logs the counterfactual
for each gate, so a single backtest tells us which component carries signal.

Read RESULTS_TEMPLATE.md before interpreting the output.

LOG SURFACE (key=value, one event per session, fires only when the latest bar
IS the event bar — run() is stateless and re-derives the session every call):
  [V2-SETUP] session context: vol regime, bands, OR bounds, gate outcomes
  [V2-ENTRY] entry: trigger prices, which gates passed, sizing math
  [V2-EXIT]  TYPE=stop|flat: full trade record + MAE/MFE/TRAIL_DD
  [V2-SKIP]  a band break occurred but a gate blocked it — WHICH gate
  [V2-NOSIG] no band break at all; how close we came
  [V2-ALT]   same signal on the OTHER underlying — the switch counterfactual
"""

from datetime import datetime, time

from surmount.base_class import Strategy, TargetAllocation
from surmount.logging import log

# ============================== CONFIG ==============================
# Vehicle. TRADE_UNDERLYING drives the traded signal; the other is logged
# only, as a counterfactual, so one run measures both.
TRADE_UNDERLYING = "QQQ"
ALT_UNDERLYING = "SPY"
BULL, BEAR = "TQQQ", "SQQQ"

# Signal geometry
BAND_K = 0.50           # band = open * (1 +/- K * vol_ref)
OR_BARS = 6             # 30 min opening range

# Which trigger is TRADED: "band" (volatility-scaled) or "orb" (v1-style).
# The other one is evaluated and logged every session anyway, so a single
# backtest measures both. They are NOT combined: at realistic QQQ volatility
# the band sits ~0.85% from the open while the OR high sits ~0.25%, so the band
# is strictly the tighter constraint and an "ORB confirmation" gate would never
# bind. Nesting them would have measured nothing. Comparing them measures the
# thing actually in question: does ORB add anything over a volatility band?
TRIGGER = "band"

# Volatility regime
VOL_LOOKBACK_SESSIONS = 2    # hard cap: window=250 at 5min = ~2.2 prior sessions
VOL_FLOOR = 0.0100           # skip if 2-session avg range < 1.00% of open
MIN_SESSION_BARS = 60        # a prior session must be this complete to count

# Risk
RISK_PCT = 0.010        # target account risk per trade at 1R (v2 used 0.015,
                        # which capped 68.1% of trades at ALLOC=1.0 and left
                        # the 1R design effectively untested)
STOP_MULT = 0.35        # stop distance = STOP_MULT * vol_ref (underlying terms)
LEV_EFF = 2.80          # MEASURED effective leverage of the 3x ETFs, not 3.0
MAX_ALLOC = 1.00        # never exceed 100% notional

# Session clock (ET). FLAT_TIME must be >= 2 bars before the last bar (15:55)
# so the flat order fills SAME DAY under the engine's one-bar fill lag.
FLAT_TIME = time(15, 45)
ENTRY_CUTOFF = time(15, 0)   # no NEW entries after this

# ===================== PRE-SPECIFIED COUNTERFACTUAL GRID =====================
# Logged every session, NEVER traded. Fixed now; do not extend between windows
# — each addition is another multiple-testing shot and silently inflates the
# chance that something looks good by luck.
#
# (label, underlying, trigger, stop_mult, respect_vol_gate)
#   base      : the traded configuration, logged for a like-for-like baseline
#   orb       : is the opening range better than the volatility band?
#   spy       : is SPY better than QQQ? (v2 said no, decisively: -2.99% vs +18.57%)
#   wide_stop : 78% of v2's stop-outs had gone favourable first, suggesting the
#               stop fires on noise. Derived FROM v2's data, so it is only a
#               hypothesis until it survives a window it was not derived from.
#   no_gate   : does VOL_FLOOR earn its keep? UNMEASURABLE in v2 — this is the
#               comparison that bug cost us.
GRID = [
    ("base",      "QQQ", "band", 0.35, True),
    ("orb",       "QQQ", "orb",  0.35, True),
    ("spy",       "SPY", "band", 0.35, True),
    ("wide_stop", "QQQ", "band", 0.55, True),
    ("no_gate",   "QQQ", "band", 0.35, False),
]


class TradingStrategy(Strategy):

    @property
    def assets(self):
        # Signal sources + traded vehicles. SPY/SPXL/SPXS are carried so the
        # alt-underlying counterfactual and any future vehicle switch need no
        # data change.
        return ["QQQ", "SPY", "TQQQ", "SQQQ", "SPXL", "SPXS"]

    @property
    def interval(self):
        return "5min"

    # ---------------------------------------------------------------- utils
    def _parse_bar_time(self, raw):
        if raw is None:
            return None
        if isinstance(raw, datetime):
            return raw
        value = str(raw).strip()
        # ISO-8601 with a T separator is accepted here; v1 silently dropped
        # such bars, which would have shifted its opening range without warning.
        if "T" in value:
            value = value.replace("T", " ")
        if "." in value:
            value = value.split(".")[0]
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                continue
        return None

    def _series(self, ohlcv, ticker):
        """[(ts, bar)] ascending for one ticker, unparseable bars dropped."""
        out = []
        for row in ohlcv:
            if not isinstance(row, dict):
                continue
            bar = row.get(ticker)
            if not bar:
                continue
            ts = self._parse_bar_time(bar.get("date"))
            if ts is None:
                continue
            out.append((ts, bar))
        return out

    def _sessions(self, series):
        """Group into {date: [(ts, bar)]} preserving order."""
        sessions = {}
        for ts, bar in series:
            sessions.setdefault(ts.date(), []).append((ts, bar))
        return sessions

    def _vol_ref(self, sessions, today):
        """Mean (high-low)/open over the most recent COMPLETE prior sessions.

        Capped at VOL_LOOKBACK_SESSIONS because window=250 on 5-min bars only
        reaches ~2.2 sessions back. Truncated sessions are excluded rather than
        silently biasing the estimate downward.
        """
        prior = [d for d in sessions if d < today]
        prior.sort(reverse=True)
        ranges = []
        for d in prior:
            bars = sessions[d]
            if len(bars) < MIN_SESSION_BARS:
                continue
            hi = max(float(b["high"]) for _, b in bars)
            lo = min(float(b["low"]) for _, b in bars)
            op = float(bars[0][1]["open"])
            if op > 0:
                ranges.append((hi - lo) / op)
            if len(ranges) >= VOL_LOOKBACK_SESSIONS:
                break
        if not ranges:
            return None, 0
        return sum(ranges) / len(ranges), len(ranges)

    def _evaluate(self, todays, vol_ref, trigger, stop_mult=None):
        """Replay one session's rule. Pure function of the bars — no state.

        `trigger` selects which levels arm the entry: "band" (volatility-scaled
        around the open) or "orb" (v1-style opening-range break). Everything
        downstream — stop, sizing, exits — is identical, so the two are
        directly comparable.

        Returns a dict describing what happened, or None if the session is too
        short. Used for the traded underlying, the ORB counterfactual, and the
        alt-underlying counterfactual.
        """
        if len(todays) < OR_BARS:
            return None

        session_open = float(todays[0][1]["open"])
        upper = session_open * (1.0 + BAND_K * vol_ref)
        lower = session_open * (1.0 - BAND_K * vol_ref)

        or_slice = [b for _, b in todays[:OR_BARS]]
        or_high = max(float(b["high"]) for b in or_slice)
        or_low = min(float(b["low"]) for b in or_slice)

        # The armed trigger levels. v1's rule additionally required a buffer of
        # 10% of OR width; that is folded in here so "orb" is a faithful
        # reproduction of the v1 trigger rather than a weaker version of it.
        if trigger == "orb":
            or_buf = 0.10 * (or_high - or_low)
            up_trig, dn_trig = or_high + or_buf, or_low - or_buf
        else:
            up_trig, dn_trig = upper, lower

        sm = STOP_MULT if stop_mult is None else stop_mult
        stop_dist = sm * vol_ref                 # fraction of price
        alloc = RISK_PCT / (LEV_EFF * stop_dist) if stop_dist > 0 else 0.0
        alloc = min(alloc, MAX_ALLOC)

        st = {
            "session_open": session_open, "upper": upper, "lower": lower,
            "or_high": or_high, "or_low": or_low,
            "up_trig": up_trig, "dn_trig": dn_trig, "trigger": trigger,
            "stop_dist": stop_dist, "alloc": alloc,
            # `direction` persists after a stop so the exit can be logged.
            # `in_position` is what drives the ALLOCATION and must go False the
            # moment we stop out. v1 conflated these; keeping them separate is
            # what prevents "stopped out but still holding".
            "direction": None, "in_position": False,
            "entry_ts": None, "entry_px": None,
            "entry_bar": None, "stop_px": None, "stopped": False,
            "exit_ts": None, "exit_px": None, "exit_bar": None,
            "blocked_by": None, "blocked_ts": None,
            "max_up": float("-inf"), "max_dn": float("-inf"),
            "mae": None, "mfe": None, "peak": None, "trail_dd": 0.0,
            "bars_held": 0,
        }

        for ts, b in todays[OR_BARS:]:
            if st["stopped"]:
                break
            # Nothing after FLAT_TIME can affect the trade: the flat target is
            # emitted on that bar and fills on the next one. Evaluating past it
            # would invent stops on bars we were no longer holding through.
            if ts.time() > FLAT_TIME:
                break
            close_px = float(b["close"])

            st["max_up"] = max(st["max_up"], close_px - up_trig)
            st["max_dn"] = max(st["max_dn"], dn_trig - close_px)

            # ---- path stats, updated BEFORE the stop test so the stop bar counts
            if st["direction"] is not None and ts > st["entry_ts"]:
                if st["direction"] == "long":
                    pnl = (close_px - st["entry_px"]) / st["entry_px"]
                else:
                    pnl = (st["entry_px"] - close_px) / st["entry_px"]
                # Seed peak with the FIRST observed pnl. v1 seeded it at 0.0,
                # which made TRAIL_DD identical to |MAE| on every trade that
                # never went favourable (27 of 27 such trades) — carrying no
                # information independent of MAE.
                st["mae"] = pnl if st["mae"] is None else min(st["mae"], pnl)
                st["mfe"] = pnl if st["mfe"] is None else max(st["mfe"], pnl)
                st["peak"] = pnl if st["peak"] is None else max(st["peak"], pnl)
                st["trail_dd"] = max(st["trail_dd"], st["peak"] - pnl)
                st["bars_held"] += 1

            if st["direction"] is None:
                long_break = close_px > up_trig
                short_break = close_px < dn_trig
                if not (long_break or short_break):
                    continue
                # A break that arrives too late to resolve before flat is
                # recorded rather than silently dropped, so the cutoff's cost
                # is measurable instead of invisible.
                if ts.time() >= ENTRY_CUTOFF:
                    if st["blocked_by"] is None:
                        st["blocked_by"] = "cutoff"
                        st["blocked_ts"] = ts
                    continue
                st["direction"] = "long" if long_break else "short"
                st["in_position"] = True
                st["entry_ts"] = ts
                st["entry_px"] = close_px
                st["entry_bar"] = b
                st["stop_px"] = (close_px * (1 - stop_dist) if long_break
                                 else close_px * (1 + stop_dist))
            else:
                hit = (close_px <= st["stop_px"] if st["direction"] == "long"
                       else close_px >= st["stop_px"])
                if hit:
                    st["stopped"] = True
                    st["in_position"] = False     # go flat, and stay flat
                    st["exit_ts"] = ts
                    st["exit_px"] = close_px
                    st["exit_bar"] = b

        return st

    # ------------------------------------------------------------------ run
    def run(self, data):
        flat = {BULL: 0.0, BEAR: 0.0}

        ohlcv = data.get("ohlcv") if isinstance(data, dict) else None
        if not ohlcv:
            return TargetAllocation(flat)

        series = self._series(ohlcv, TRADE_UNDERLYING)
        if not series:
            return TargetAllocation(flat)

        latest_ts = series[-1][0]
        today = latest_ts.date()

        # Past FLAT_TIME we are flat and the FLAT_TIME bar has already emitted
        # its logs on an earlier call, so there is nothing left to do.
        # NOTE: this deliberately does NOT short-circuit the FLAT_TIME bar
        # itself. v1 returned flat before its own end-of-day logging block,
        # which made that block unreachable.
        if latest_ts.time() > FLAT_TIME:
            return TargetAllocation(flat)
        at_flat = latest_ts.time() == FLAT_TIME

        sessions = self._sessions(series)
        todays = sessions.get(today, [])
        if len(todays) < OR_BARS:
            return TargetAllocation(flat)

        vol_ref, n_vol = self._vol_ref(sessions, today)
        if vol_ref is None or vol_ref <= 0:
            return TargetAllocation(flat)

        or_complete_ts = todays[OR_BARS - 1][0]
        vol_ok = vol_ref >= VOL_FLOOR

        if latest_ts == or_complete_ts:
            st0 = self._evaluate(todays, vol_ref, TRIGGER)
            '''log(
                "[V2-SETUP] {d} UND={u} TRIG={tg} VOL_REF={v:.5f} N_SESS={n} "
                "VOL_OK={ok} FLOOR={f:.4f} OPEN={o:.2f} UPPER={up:.2f} "
                "LOWER={lo:.2f} OH={oh:.2f} OL={ol:.2f} UP_TRIG={ut:.2f} "
                "DN_TRIG={dt:.2f} STOP_DIST={sd:.5f} ALLOC={a:.4f}".format(
                    d=today, u=TRADE_UNDERLYING, tg=TRIGGER, v=vol_ref, n=n_vol,
                    ok=int(vol_ok), f=VOL_FLOOR, o=st0["session_open"],
                    up=st0["upper"], lo=st0["lower"], oh=st0["or_high"],
                    ol=st0["or_low"], ut=st0["up_trig"], dt=st0["dn_trig"],
                    sd=st0["stop_dist"], a=st0["alloc"],
                )
            )'''

        # Volatility gate.
        # *** THE v2 BUG WAS HERE. *** v2 returned early on a failed gate, so
        # the FLAT_TIME counterfactual block was never reached on skipped
        # sessions and the gate's own value was unmeasurable — 71 sessions with
        # no record. The gate now suppresses only the ALLOCATION and the
        # traded-trade logs. The counterfactual grid is emitted either way.
        if not vol_ok and latest_ts == or_complete_ts:
            '''log("[V2-SKIP] {d} GATE=vol VOL_REF={v:.5f} FLOOR={f:.4f}".format(
                d=today, v=vol_ref, f=VOL_FLOOR))'''

        st = self._evaluate(todays, vol_ref, TRIGGER)
        if st is None:
            return TargetAllocation(flat)

        # ------------------------------------------- traded-trade logging
        # Gated on vol_ok: these describe positions we actually took.
        if vol_ok and st["entry_ts"] == latest_ts and st["entry_bar"] is not None:
            b = st["entry_bar"]
            '''log(
                "[V2-ENTRY] {ts} UND={u} DIR={d} C={c:.2f} OPEN={o:.2f} "
                "BAND={bd:.2f} OR={orb:.2f} VOL_REF={v:.5f} STOP_PX={sp:.2f} "
                "STOP_DIST={sd:.5f} ALLOC={a:.4f} ACCT_RISK={ar:.4f} "
                "VOL={vol:.0f}".format(
                    ts=st["entry_ts"], u=TRADE_UNDERLYING,
                    d=st["direction"].upper(), c=st["entry_px"],
                    o=st["session_open"],
                    bd=st["upper"] if st["direction"] == "long" else st["lower"],
                    orb=st["or_high"] if st["direction"] == "long" else st["or_low"],
                    v=vol_ref, sp=st["stop_px"], sd=st["stop_dist"],
                    a=st["alloc"], ar=st["alloc"] * LEV_EFF * st["stop_dist"],
                    vol=float(b.get("volume", 0)),
                )
            )'''

        if vol_ok and st["exit_ts"] == latest_ts and st["exit_bar"] is not None:
            self._log_exit(st, "stop", st["exit_px"], st["exit_ts"])

        # Flat-time exit fires on the bar we emit flat, one bar before the fill.
        if vol_ok and at_flat and st["in_position"]:
            self._log_exit(st, "flat", float(todays[-1][1]["close"]), latest_ts)

        '''if at_flat and vol_ok:
            if st["entry_ts"] is None and st["blocked_by"] is None:
                log("[V2-NOSIG] {d} MAX_UP={mu:.4f} MAX_DN={md:.4f} "
                    "VOL_REF={v:.5f}".format(
                        d=today,
                        mu=st["max_up"] if st["max_up"] != float("-inf") else 0.0,
                        md=st["max_dn"] if st["max_dn"] != float("-inf") else 0.0,
                        v=vol_ref))
            elif st["entry_ts"] is None:
                log("[V2-SKIP] {d} GATE={g} TS={t} VOL_REF={v:.5f}".format(
                    d=today, g=st["blocked_by"], t=st["blocked_ts"], v=vol_ref))'''
        # The counterfactual grid — emitted on EVERY session, including
        # vol-gated ones. This placement is the whole point of v2.1.
        if at_flat:
            self._log_grid(ohlcv, today, vol_ok)

        # ------------------------------------------------------- allocation
        # Emit flat ON the FLAT_TIME bar so the fill lands at the next bar,
        # same day. Everything above this line has already been logged.
        if at_flat or not vol_ok or not st["in_position"]:
            return TargetAllocation(flat)
        if st["direction"] == "long":
            return TargetAllocation({BULL: st["alloc"], BEAR: 0.0})
        return TargetAllocation({BULL: 0.0, BEAR: st["alloc"]})

    # -------------------------------------------------------------- helpers
    def _log_exit(self, st, kind, exit_px, exit_ts):
        if st["direction"] == "long":
            pnl = (exit_px - st["entry_px"]) / st["entry_px"]
        else:
            pnl = (st["entry_px"] - exit_px) / st["entry_px"]
        '''log(
            "[V2-EXIT] {ts} TYPE={k} UND={u} DIR={d} ENTRY_TS={ets} BARS={n} "
            "ENTRY_PX={ep:.2f} EXIT_PX={xp:.2f} PNL_UND={p:.5f} "
            "PNL_ACCT={pa:.5f} ALLOC={a:.4f} MAE={mae:.5f} MFE={mfe:.5f} "
            "TRAIL_DD={td:.5f}".format(
                ts=exit_ts, k=kind, u=TRADE_UNDERLYING,
                d=st["direction"].upper(), ets=st["entry_ts"],
                n=st["bars_held"], ep=st["entry_px"], xp=exit_px, p=pnl,
                pa=pnl * LEV_EFF * st["alloc"], a=st["alloc"],
                mae=st["mae"] if st["mae"] is not None else 0.0,
                mfe=st["mfe"] if st["mfe"] is not None else 0.0,
                td=st["trail_dd"],
            )
        )'''

    def _log_grid(self, ohlcv, day, traded_vol_ok):
        """Evaluate the pre-specified GRID and log it. Never traded.

        Emitted on EVERY session including vol-gated ones, which is the fix
        v2.1 exists for. Each variant uses its own underlying's volatility, so
        the SPY row is a like-for-like vehicle comparison rather than QQQ's
        parameters imposed on SPY.

        `SKIPPED=1` marks a row the traded strategy did NOT take because of the
        volatility gate. Grouping on that field is what finally measures
        whether VOL_FLOOR earns its keep.
        """
        cache = {}
        for label, und, trigger, stop_mult, respect_gate in GRID:
            if und not in cache:
                s = self._series(ohlcv, und)
                if not s:
                    cache[und] = None
                else:
                    sess = self._sessions(s)
                    td = sess.get(day, [])
                    vr, _n = self._vol_ref(sess, day)
                    cache[und] = (td, vr) if (len(td) >= OR_BARS and vr) else None
            if cache[und] is None:
                continue
            todays, vol_ref = cache[und]
            gate_blocks = respect_gate and vol_ref < VOL_FLOOR
            st = self._evaluate(todays, vol_ref, trigger, stop_mult)
            if st is None:
                continue
            head = ("[V2-GRID] {d} VAR={L} UND={u} TRIG={tg} SM={sm:.2f} "
                    "VOL_REF={v:.5f} VOL_OK={ok} SKIPPED={sk}").format(
                d=day, L=label, u=und, tg=trigger, sm=stop_mult, v=vol_ref,
                ok=int(vol_ref >= VOL_FLOOR),
                sk=int(gate_blocks or not traded_vol_ok))
            if gate_blocks:
                '''log(head + " RESULT=gated")'''
                continue
            if st["entry_ts"] is None:
                '''log(head + " RESULT=none GATE={g}".format(g=st["blocked_by"]))'''
                continue
            exit_px = (st["exit_px"] if st["stopped"]
                       else float(todays[-1][1]["close"]))
            if st["direction"] == "long":
                pnl = (exit_px - st["entry_px"]) / st["entry_px"]
            else:
                pnl = (st["entry_px"] - exit_px) / st["entry_px"]
            '''log(head + (
                " RESULT={r} DIR={dir} ENTRY_TS={ets} BARS={n} "
                "ENTRY_PX={ep:.2f} EXIT_PX={xp:.2f} PNL_UND={p:.5f} "
                "PNL_ACCT={pa:.5f} ALLOC={a:.4f} MAE={mae:.5f} "
                "MFE={mfe:.5f}").format(
                    r="stop" if st["stopped"] else "flat",
                    dir=st["direction"].upper(), ets=st["entry_ts"],
                    n=st["bars_held"], ep=st["entry_px"], xp=exit_px, p=pnl,
                    pa=pnl * LEV_EFF * st["alloc"], a=st["alloc"],
                    mae=st["mae"] if st["mae"] is not None else 0.0,
                    mfe=st["mfe"] if st["mfe"] is not None else 0.0,
                ))
'''