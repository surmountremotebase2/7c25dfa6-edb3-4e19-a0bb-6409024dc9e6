from surmount.base_class import Strategy, TargetAllocation
from surmount.technical_indicators import SMA
from surmount.logging import log
import pandas as pd 
import numpy as np 

class TradingStrategy(Strategy):
    @property
    def assets(self):
        # Define the assets to be used in the strategy
        return ["SPXL", "SPY", "SPXS"]

    @property
    def interval(self):
        # The data interval desired for the strategy. Daily in this case.
        return "1day"

    def run(self, data):
        # This is the principal method where the strategy logic is defined.
        
        # Calculate the 5-day Simple Moving Average (SMA) for SPXL and SPY
        sma_SPXL = SMA("SPXL", data["ohlcv"], length=5)
        sma_SPY = SMA("SPY", data["ohlcv"], length=5)
        sma_SPXS = SMA("SPXS", data["ohlcv"], length=5)
        
        # Ensure that we have enough data points to proceed
        if not sma_SPXL or not sma_SPY or not sma_SPXS or len(sma_SPXL) < 5 or len(sma_SPY) < 5 or len(sma_SPXS) < 5:
            #log("Insufficient data for SMA calculation.")
            # Returning a neutral or "do-nothing" allocation if insufficient data
            return TargetAllocation({})
        
        # Check the recent performance difference between SPXL and SPY
        # If SPXL has been underperforming SPY, allocate toward SPXL

        spxl_delta = (sma_SPXL[-1] - sma_SPXL[-2]) / sma_SPXL[-1]
        spy_delta = (sma_SPY[-1] - sma_SPY[-2]) / sma_SPY[-1]
        spxs_delta = (sma_SPXS[-1] - sma_SPXS[-2]) / sma_SPXS[-1]

        spy_recents = sma_SPY[-5:]
        spy_differences = [last_values[i+1] - last_values[i] for i in range(len(last_values)-1)]

        # Determine overall trend based on the last 5 days
        upward_trend = sum(d > 0 for d in differences)
        downward_trend = sum(d < 0 for d in differences)

        #log("Checking trends")
        if upward_trend > downward_trend:
            allocation_dict = {"SPXS": 0.0}
            #log("Upward trend")
            if spxl_delta < spy_delta:
                allocation_dict = {"SPXL": 1.0}
            else:
                allocation_dict = {"SPXL": 0.0}
        elif upward_trend < downward_trend:
            #log("downward trend")
            allocation_dict = {"SPXL": 0.0}
            if spxs_delta < abs(spy_delta):
                allocation_dict = {"SPXS": 1.0}
            else:
                allocation_dict = {"SPXS": 0.0}
        else:
            log("In the last else")

        '''if sma_SPXL[-1] < sma_SPY[-1]:
            #log("SPXL underperforming SPY, buying SPXL.")
            allocation_dict = {"SPXL": 1.0} # Put 100% in SPXL
        else:
            #log("SPXL not underperforming or outperforming SPY, liquidating SPXL.")
            allocation_dict = {"SPXL": 0.0} # Liquidate all SPXL

        if spxl_delta < spy_delta:
            #log("SPXL Underperforming spy, buying SPXL.")
            allocation_dict = {"SPXL": 0.00}
        else:
            #log("SPXL caught up - liquidating SPXL.")
            allocation_dict = {"SPXL": 0.0}
        '''
            
        # Return the target allocation based on our logic
        return TargetAllocation(allocation_dict)