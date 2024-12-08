from typing import Dict, Tuple, List
import pandas as pd
import numpy as np

from surmount.base_class import Strategy, TargetAllocation
from surmount.technical_indicators import SMA, EMA
from surmount.logging import log

class TradingStrategy(Strategy):
    def __init__(self):
        # Count is used as a "cool-down" period after triggering risk-off behavior.
        self.count = 0
    
    @property
    def assets(self) -> List[str]:
        """Assets to be traded by this strategy."""
        return ["BTC-USD"]

    @property
    def interval(self) -> str:
        """Data interval used by the strategy."""
        return "1hour"

    def volatility_check(
        self,
        market: str,
        data: Dict,
        INTERVAL_WINDOW: int = 60,
        n_future: int = 20,
        volaT_percentile: float = 55.0,
        volaH_percentile: float = 80.0
    ) -> Tuple[Dict[str, float], int]:
        """
        Perform a volatility check and determine if the strategy should go risk-off.

        Parameters
        ----------
        market : str
            Market symbol (e.g., "BTC-USD").
        data : dict
            Data dictionary with OHLCV values.
        INTERVAL_WINDOW : int
            Rolling window size for volatility calculation.
        n_future : int
            Number of future periods used for forward-looking volatility.
        volaT_percentile : float
            Percentile for the lower volatility threshold.
        volaH_percentile : float
            Percentile for the higher volatility threshold.

        Returns
        -------
        allocation_dict : Dict[str, float]
            A dictionary of allocations by ticker.
        count : int
            Updated count for future risk-off periods.
        """
        # Extract close prices for the given market
        closes = [entry[market]['close'] for entry in data['ohlcv'] if market in entry]
        mrkt_df = pd.DataFrame(closes, columns=['close'])
        
        # Compute log returns and fill any initial NaNs with 0
        mrkt_df['log_returns'] = np.log(mrkt_df['close'] / mrkt_df['close'].shift(1))
        mrkt_df['log_returns'].fillna(0, inplace=True)

        allocation_dict = {market: 0.0}

        if len(mrkt_df) <= n_future:
            # Not enough data to perform forward-looking volatility checks
            return allocation_dict, self.count

        # Compute current volatility (backward-looking)
        mrkt_df['vol_current'] = (
            mrkt_df['log_returns']
            .rolling(window=INTERVAL_WINDOW)
            .apply(lambda x: np.sqrt(np.sum(x**2) / (len(x) - 1)), raw=True)
        )
        # Backfill the initial window to avoid NaNs
        mrkt_df['vol_current'].bfill(inplace=True)

        # Compute future volatility (forward-looking)
        future_shifted = mrkt_df['log_returns'].shift(n_future).fillna(0)
        mrkt_df['vol_future'] = (
            future_shifted
            .rolling(window=INTERVAL_WINDOW)
            .apply(lambda x: np.sqrt(np.sum(x**2) / (len(x) - 1)), raw=True)
        )
        mrkt_df['vol_future'].bfill(inplace=True)

        # Determine volatility thresholds
        volaT = np.percentile(mrkt_df['vol_current'], volaT_percentile)
        volaH = np.percentile(mrkt_df['vol_current'], volaH_percentile)

        # Extract the most recent close and EMA
        mrkt_close = mrkt_df['close'].iloc[-1]
        mrkt_ema = EMA(market, data["ohlcv"], length=30)

        # Volatility-based risk-off logic
        current_vol = mrkt_df['vol_current'].iloc[-1]
        future_vol = mrkt_df['vol_future'].iloc[-1]

        if current_vol > future_vol and current_vol > volaT:
            # Market is volatile, move to risk-off mode
            if current_vol > volaH:
                self.count = 10  # More volatile, longer wait
            else:
                self.count = 5   # Less volatile, shorter wait
            allocation_dict = {market: 0.0}
        elif self.count < 1 and mrkt_close > mrkt_ema[-1]:
            # Conditions allow re-entry into the market
            allocation_dict = {market: 1.0}

        return allocation_dict, self.count

    def run(self, data: Dict) -> TargetAllocation:
        """
        Main logic to run each interval. Adjusts allocation based on volatility and SMAs.

        Parameters
        ----------
        data : dict
            Market OHLCV data.

        Returns
        -------
        TargetAllocation
            The desired allocation for each asset at this interval.
        """
        # Decrement the risk-off count if active
        self.count = max(0, self.count - 1)

        # Check volatility conditions and possibly update count
        allocation_dict, self.count = self.volatility_check("BTC-USD", data)

        # If not in a risk-off period (count == 0), apply SMA trend logic
        if self.count == 0:
            short_sma = SMA("BTC-USD", data["ohlcv"], length=3)
            mid_sma = SMA("BTC-USD", data["ohlcv"], length=5)

            # If short-term SMA is rising and above the mid-term SMA, go long
            if short_sma[-1] > short_sma[-2] and short_sma[-1] > mid_sma[-1]:
                allocation_dict = {"BTC-USD": 1.0}
            else:
                allocation_dict = {"BTC-USD": 0.0}

        return TargetAllocation(allocation_dict)
