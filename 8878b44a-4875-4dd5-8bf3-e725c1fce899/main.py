from surmount.base_class import Strategy, TargetAllocation
from surmount.technical_indicators import SMA
from surmount.logging import log
import pandas as pd 
import numpy as np 

class TradingStrategy(Strategy):
    @property
    def assets(self):
        # Define the assets to be used in the strategy
        return ["BTCUSD"]

    @property
    def interval(self):
        # The data interval desired for the strategy. Daily in this case.
        return "4hour"

    def run(self, data):
        allocation_dict = {"BTCUSD": 1.0}
        
        if not allocation_dict:
            allocation_dict = TargetAllocation({})

        # Return the target allocation based on our logic
        return TargetAllocation(allocation_dict)