from surmount.base_class import Strategy, TargetAllocation
from surmount.technical_indicators import SMA
from surmount.logging import log
import pandas as pd 
import numpy as np 

class TradingStrategy(Strategy):
    in_trade = 0
    resistance_found = 0

    
    @property
    def assets(self):
        # Define the assets to be used in the strategy
        return ["SPXL", "SPY", "SPXS"]

    @property
    def interval(self):
        # The data interval desired for the strategy. Daily in this case.
        #return "5min"
        return "1min"

    def run(self, data):
        # This is the principal method where the strategy logic is defined.

        # Check if we're looking at market open candle


        # Check the opening candle high/low - wait for a rise above, or fall below. 
        log(str(data['ohlcv'][-1]))
        
        
        #allocation_dict = TargetAllocation({})
        return TargetAllocation({})

        # Return the target allocation based on our logic
        #return TargetAllocation(allocation_dict)