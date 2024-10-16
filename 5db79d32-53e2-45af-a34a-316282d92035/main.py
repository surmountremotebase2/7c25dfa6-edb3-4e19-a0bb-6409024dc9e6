from surmount.base_class import Strategy, TargetAllocation
from surmount.technical_indicators import SMA, EMA
from surmount.logging import log
import pandas as pd
import numpy as np

class TradingStrategy(Strategy):
    def __init__(self):
        self.count = 0  # Initialize the count for the risk-off holding period
    
    @property
    def assets(self):
        # Define the assets to be used in the strategy
        return ["BTC-USD"]

    @property
    def interval(self):
        # The data interval desired for the strategy. Daily in this case.
        return "1hour"

    def volatility_check(self, mrkt, data, INTERVAL_WINDOW=60, n_future=20, volaT_percentile=55, volaH_percentile=80):
        """
        Perform a volatility check for market conditions and return an updated allocation based on risk-off behavior.
        
        Parameters:
            - mrkt: Market symbol (e.g., "BTC-USD")
            - data: Data dictionary with OHLCV values
            - INTERVAL_WINDOW: Rolling window size for volatility calculation
            - n_future: Number of future periods for forward-looking volatility
            - volaT_percentile: Percentile for lower volatility threshold
            - volaH_percentile: Percentile for higher volatility threshold

        Returns:
            - allocation_dict: Dictionary of ticker allocations based on volatility conditions
            - count: Updated count for future decisions
        """
        mrktData = [entry[mrkt]['close'] for entry in data['ohlcv'] if mrkt in entry]
        mrktData = pd.DataFrame(mrktData, columns=['close'])
        mrktData['log_returns'] = np.log(mrktData.close / mrktData.close.shift(1))
        mrktData = mrktData.fillna(0)

        allocation_dict = {"BTC-USD": 0.0}

        if len(mrktData) > n_future:
            # Get backward-looking realized volatility
            mrktData['vol_current'] = mrktData['log_returns'].rolling(window=INTERVAL_WINDOW).apply(
                lambda x: np.sqrt(np.sum(x**2) / (len(x) - 1)))
            mrktData['vol_current'] = mrktData['vol_current'].bfill()

            # Get forward-looking realized volatility
            mrktData['vol_future'] = mrktData['log_returns'].shift(n_future).fillna(0).rolling(window=INTERVAL_WINDOW).apply(
                lambda x: np.sqrt(np.sum(x**2) / (len(x) - 1)))
            mrktData['vol_future'] = mrktData['vol_future'].bfill()

            # Calculate volatility thresholds
            volaT = np.percentile(mrktData['vol_current'], volaT_percentile)
            volaH = np.percentile(mrktData['vol_current'], volaH_percentile)
            mrktClose = mrktData['close'].iloc[-1]
            mrktEMA = EMA(mrkt, data["ohlcv"], length=30)

            # Volatility check and risk-off allocation logic
            if mrktData['vol_current'].iloc[-1] > mrktData['vol_future'].iloc[-1] and mrktData['vol_current'].iloc[-1] > volaT:
                if mrktData['vol_current'].iloc[-1] > volaH:
                    self.count = 10  # Risk-off for 10 intervals
                else:
                    self.count = 5   # Risk-off for 5 intervals
                allocation_dict = {"BTC-USD": 0.0}  # Risk-off, allocate nothing
            elif self.count < 1 and mrktClose > mrktEMA[-1]:
                allocation_dict = {"BTC-USD": 1.0}  # Re-enter positions

        return allocation_dict, self.count

    def run(self, data):
        # Decrement the count for the risk-off holding period if it's active
        self.count = max(0, self.count - 1)

        # Run the volatility check
        allocation_dict, self.count = self.volatility_check("BTC-USD", data)

        # If volatility check allows, proceed with the SMA logic
        if self.count == 0:
            # Calculate the historical SMAs for BTCUSD
            three_sma = SMA("BTC-USD", data["ohlcv"], length=3)
            five_sma = SMA("BTC-USD", data["ohlcv"], length=5)

            # Check SMA alignment for trend confirmation
            if three_sma[-1] > three_sma[-2] and three_sma[-1] > five_sma[-1]:
                allocation_dict = {"BTC-USD": 1.0}
            else:
                allocation_dict = {"BTC-USD": 0.0}
        
        # Return the target allocation based on our logic
        return TargetAllocation(allocation_dict)
