from surmount.base_class import Strategy, TargetAllocation
from surmount.technical_indicators import SMA
from surmount.logging import log
import pandas as pd
import numpy as np

class TradingStrategy(Strategy):

    def __init__(self):
        self.counter = 0

    @property
    def assets(self):
        # Define the assets to be used in the strategy
        return ["TQQQ", "TNA", "UPRO", "SPXL", "QLD", "SSO", "UDOW"]

    @property
    def interval(self):
        # The data interval desired for the strategy. Daily in this case.
        return "1day"

    def run(self, data):
        # This is the principal method where the strategy logic is defined.
        if self.counter % 7 != 0:
            return TargetAllocation({})

        # Correct the typos in the SMA calls
        sma_TQQQ = SMA("TQQQ", data["ohlcv"], length=5)
        sma_TNA = SMA("TNA", data["ohlcv"], length=5)
        sma_UPRO = SMA("UPRO", data["ohlcv"], length=5)  # Corrected "lenth=5" -> "length=5"
        sma_SPXL = SMA("SPXL", data["ohlcv"], length=5)
        sma_QLD = SMA("QLD", data["ohlcv"], length=5)
        sma_SSO = SMA("SSO", data["ohlcv"], length=5)
        sma_UDOW = SMA("UDOW", data["ohlcv"], length=5)  # Corrected "SSO" -> "UDOW"

        # Create a dictionary of asset -> SMA values for convenience
        sma_dict = {
            "TQQQ": sma_TQQQ,
            "TNA": sma_TNA,
            "UPRO": sma_UPRO,
            "SPXL": sma_SPXL,
            "QLD": sma_QLD,
            "SSO": sma_SSO,
            "UDOW": sma_UDOW
        }

        # 1) Calculate 5-day SMA percent change for each asset over the last 5 trading days
        #    (close[-1] - close[-5]) / close[-5] on the 5-day SMA values.
        performance = {}
        for asset, sma_series in sma_dict.items():
            # Ensure we have at least 5 points in the SMA
            if len(sma_series) < 5:
                # If insufficient data, treat performance as None or a very large negative value
                performance[asset] = float('-inf')
            else:
                last_val = sma_series[-1]
                five_days_ago_val = sma_series[-5]
                
                # Prevent division by zero
                if five_days_ago_val == 0:
                    performance[asset] = float('-inf')
                else:
                    performance[asset] = (last_val - five_days_ago_val) / five_days_ago_val

        # 2) Sort assets by performance (descending) and take the top 3
        top_3_assets = sorted(performance, key=performance.get, reverse=True)[:3]

        # 3) Assign an equal distribution among the top 3
        allocation_dict = {asset: 1.0 / 3.0 for asset in top_3_assets}

        # Return the TargetAllocation of the allocation_dict
        return TargetAllocation(allocation_dict)
