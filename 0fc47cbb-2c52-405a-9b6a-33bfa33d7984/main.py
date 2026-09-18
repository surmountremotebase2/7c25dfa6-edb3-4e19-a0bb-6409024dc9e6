"""monday_ibs v1 -- Monday-down / IBS<0.5 mean-reversion, coworker exit. ARM C: tilt -- QQQ baseline, TQQQ on signal.

Rule (engine semantics, next-bar-open fills):
  * At the close of a Monday bar of SIGNAL: close < prior close AND IBS = (C-L)/(H-L) < IBS_MAX
    -> emit VEHICLE 100%  (fills at the next bar's open).
  * At the close of every held bar (the fill bar included): close > prior bar's high
    -> emit flat/baseline (fills at the next open). After the MAX_HOLD-th held bar closes with
    no trigger -> emit flat (cap). Signals while in a position are ignored.
  * An explicit target is emitted on every bar (never None).

Logging:
  [MIBS-SIG]  entry signal: date, close, prev close, IBS
  [MIBS-SKIP] a Monday that did not fire, with the reason
  [MIBS-XSIG] exit signal: type=target|cap, days held
  [MIBS-EXIT] the completed trade, logged on the bar whose OPEN is the exit fill:
              PNL_ACCT = open_exit/open_entry - 1 on VEHICLE; PNL_BASE = same on BASELINE
              (0 if cash); PNL_EXCESS = PNL_ACCT - PNL_BASE.
"""
from datetime import datetime

from surmount.base_class import Strategy, TargetAllocation
from surmount.logging import log

# ---- arm constants (the only lines that differ between arm files) ----
SIGNAL = "QQQ"      # bars the signal and exit are computed on
VEHICLE = "TQQQ"    # held while in a trade
BASELINE = "QQQ"    # held while flat
# ----------------------------------------------------------------------
IBS_MAX = 0.5
MAX_HOLD = 7        # held bars; exit fills at the open of bar e + MAX_HOLD at the latest


class TradingStrategy(Strategy):

    def __init__(self):
        self.in_pos = False
        self.entry_signal_date = None
        self.entry_fill_date = None
        self.entry_px = None
        self.base_entry_px = None
        self.days_held = 0
        self.pending_exit = None
        self.n_trades = 0

    @property
    def assets(self):
        out = [SIGNAL]
        for a in (VEHICLE, BASELINE):
            if a and a not in out:
                out.append(a)
        return out

    @property
    def interval(self):
        return "1day"

    @property
    def data(self):
        return []

    # ---- helpers ----
    @staticmethod
    def _date(bar):
        raw = bar.get("date")
        if isinstance(raw, datetime):
            return raw
        return datetime.strptime(str(raw)[:10], "%Y-%m-%d")

    def _target(self, invested):
        alloc = {a: 0.0 for a in self.assets}
        if invested:
            alloc[VEHICLE] = 1.0
        elif BASELINE:
            alloc[BASELINE] = 1.0
        return TargetAllocation(alloc)

    # ---- main ----
    def run(self, data):
        ohlcv = data.get("ohlcv") or []
        if len(ohlcv) < 2 or SIGNAL not in ohlcv[-1] or SIGNAL not in ohlcv[-2]:
            return self._target(self.in_pos)
        bar = ohlcv[-1][SIGNAL]
        prev = ohlcv[-2][SIGNAL]
        dt = self._date(bar)
        dstr = dt.strftime("%Y-%m-%d")
        vbar = ohlcv[-1].get(VEHICLE, bar)
        bbar = ohlcv[-1].get(BASELINE) if BASELINE else None

        # 1. A flat target emitted on the previous bar filled at THIS bar's open: log the trade.
        if self.pending_exit is not None:
            pe = self.pending_exit
            exit_px = float(vbar["open"])
            pnl = exit_px / pe["entry_px"] - 1.0
            if BASELINE and bbar is not None and pe["base_entry_px"]:
                pnl_base = float(bbar["open"]) / pe["base_entry_px"] - 1.0
            else:
                pnl_base = 0.0
            self.n_trades += 1
            log("[MIBS-EXIT] N=%d ENTRY_SIG=%s ENTRY_FILL=%s EXIT_SIG=%s EXIT_FILL=%s DAYS=%d TYPE=%s "
                "VEH=%s ENTRY_PX=%.4f EXIT_PX=%.4f PNL_ACCT=%.6f PNL_BASE=%.6f PNL_EXCESS=%.6f"
                % (self.n_trades, pe["entry_sig"], pe["entry_fill"], pe["exit_sig"], dstr,
                   pe["days"], pe["type"], VEHICLE, pe["entry_px"], exit_px, pnl, pnl_base,
                   pnl - pnl_base))
            self.pending_exit = None

        # 2. In a position: this bar is a held bar. Record the fill on the first one.
        if self.in_pos:
            if self.entry_fill_date is None:
                self.entry_fill_date = dstr
                self.entry_px = float(vbar["open"])
                self.base_entry_px = float(bbar["open"]) if (BASELINE and bbar is not None) else None
                self.days_held = 1
            else:
                self.days_held += 1
            trigger = float(bar["close"]) > float(prev["high"])
            cap = self.days_held >= MAX_HOLD
            if trigger or cap:
                self.pending_exit = dict(
                    entry_sig=self.entry_signal_date, entry_fill=self.entry_fill_date,
                    entry_px=self.entry_px, base_entry_px=self.base_entry_px,
                    days=self.days_held, type="target" if trigger else "cap", exit_sig=dstr)
                log("[MIBS-XSIG] DATE=%s TYPE=%s DAYS=%d CLOSE=%.4f PREV_HIGH=%.4f"
                    % (dstr, "target" if trigger else "cap", self.days_held,
                       float(bar["close"]), float(prev["high"])))
                self.in_pos = False
                self.entry_fill_date = None
                self.days_held = 0
                return self._target(False)
            return self._target(True)

        # 3. Flat: evaluate the Monday signal at this close.
        is_mon = dt.weekday() == 0
        if not is_mon:
            return self._target(False)
        c, h, lo = float(bar["close"]), float(bar["high"]), float(bar["low"])
        pc = float(prev["close"])
        down = c < pc
        ibs = (c - lo) / (h - lo) if (h - lo) > 0 else None
        if down and ibs is not None and ibs < IBS_MAX:
            self.in_pos = True
            self.entry_signal_date = dstr
            self.entry_fill_date = None
            self.days_held = 0
            log("[MIBS-SIG] DATE=%s CLOSE=%.4f PREV_CLOSE=%.4f IBS=%.3f -> LONG %s"
                % (dstr, c, pc, ibs, VEHICLE))
            return self._target(True)
        reason = "not_down" if not down else ("flat_bar" if ibs is None else "ibs_%.3f" % ibs)
        log("[MIBS-SKIP] DATE=%s REASON=%s" % (dstr, reason))
        return self._target(False)