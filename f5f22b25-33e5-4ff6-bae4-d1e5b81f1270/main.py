from surmount.base_class import Strategy, TargetAllocation
from surmount.technical_indicators import SMA
from surmount.logging import log
import pandas as pd 
import numpy as np 

class TradingStrategy(Strategy):
    @property
    def assets(self):
        # Define the assets to be used in the strategy
        return ["SPDN", "SPY", "SH"]

    @property
    def interval(self):
        # The data interval desired for the strategy. Daily in this case.
        return "4hour"

    def run(self, data):
        # This is the principal method where the strategy logic is defined.
        
        # Calculate the 5-day Simple Moving Average (SMA) for spdn and SPY
        sma_spdn = SMA("SPDN", data["ohlcv"], length=5)
        sma_SPY = SMA("SPY", data["ohlcv"], length=5)
        sma_sh = SMA("SH", data["ohlcv"], length=5)
        
        # Ensure that we have enough data points to proceed
        if not sma_spdn or not sma_SPY or not sma_sh or len(sma_spdn) < 5 or len(sma_SPY) < 5 or len(sma_sh) < 5:
            #log("Insufficient data for SMA calculation.")
            # Returning a neutral or "do-nothing" allocation if insufficient data
            return TargetAllocation({})
        
        # Check the recent performance difference between spdn and SPY
        # If spdn has been underperforming SPY, allocate toward spdn

        spdn_delta = (sma_spdn[-1] - sma_spdn[-2]) / sma_spdn[-1]
        spy_delta = (sma_SPY[-1] - sma_SPY[-2]) / sma_SPY[-1]
        sh_delta = (sma_sh[-1] - sma_sh[-2]) / sma_sh[-1]

        spy_recents = sma_SPY[-15:]
        spy_differences = [spy_recents[i+1] - spy_recents[i] for i in range(len(spy_recents)-1)]

        # Determine overall trend based on the last 5 days
        upward_trend = sum(d > 0 for d in spy_differences)
        downward_trend = sum(d < 0 for d in spy_differences)

        #log("Checking trends")
        if upward_trend < downward_trend:
            allocation_dict = {"SH": 0.0}
            #log("Upward trend")
            if spdn_delta < spy_delta * 1.15:
                allocation_dict = {"SPDN": 0.0}
            else:
                allocation_dict = {"SPDN": 1.0}
        elif upward_trend > downward_trend:
            #log("downward trend")
            allocation_dict = {"SPDN": 0.0}
            if sh_delta < abs(spy_delta * 1.15):
                allocation_dict = {"SH": 0.0}
            else:
                allocation_dict = {"SH": 1.0}
        else:
            #log("In the else")
            return TargetAllocation({})
        
        if not allocation_dict:
            allocation_dict = TargetAllocation({})

        # Return the target allocation based on our logic
        return TargetAllocation(allocation_dict)