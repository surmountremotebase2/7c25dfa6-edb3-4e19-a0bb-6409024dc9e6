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
        return "1hour"

    def run(self, data):
        #allocation_dict = {"BTCUSD": 1.0}

        # Calculate the hitorical SMA's for BTCUSD
        three_sma = SMA("BTCUSD", data["ohlcv"], length=3)
        five_sma = SMA("BTCUSD", data["ohlcv"], length=5)
        seven_sma = SMA("BTCUSD", data["ohlcv"], length=7)
        ten_sma = SMA("BTCUSD", data["ohlcv"], length=10)

        if three_sma > five_sma:
            allocation_dict = {"BTCUSD": 1.0}
        else:
            allocation_dict = {"BTCUSD": 0.0}
        
        if not allocation_dict:
            allocation_dict = TargetAllocation({})

        # Return the target allocation based on our logic
        return TargetAllocation(allocation_dict)