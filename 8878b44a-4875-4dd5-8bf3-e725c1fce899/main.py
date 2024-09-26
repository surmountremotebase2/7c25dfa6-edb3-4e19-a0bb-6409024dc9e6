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
        # Calculate the historical SMAs for BTCUSD
        three_sma = SMA("BTCUSD", data["ohlcv"], length=3)
        five_sma = SMA("BTCUSD", data["ohlcv"], length=5)
        seven_sma = SMA("BTCUSD", data["ohlcv"], length=7)
        ten_sma = SMA("BTCUSD", data["ohlcv"], length=10)
        
        # Set the number of periods to confirm the upward trend
        N = 3  # Number of consecutive increases required
        
        # Check if the 3-period SMA has been increasing for the last N periods
        upward_trend = all([three_sma[-i] > three_sma[-i-1] for i in range(1, N+1)])
        
        # Check if moving averages are aligned (shorter-term SMAs above longer-term SMAs)
        ma_alignment = three_sma[-1] > five_sma[-1] > seven_sma[-1] > ten_sma[-1]
        
        if upward_trend and ma_alignment:
            allocation_dict = {"BTCUSD": 1.0}
        else:
            allocation_dict = {"BTCUSD": 0.0}
        
        if not allocation_dict:
            allocation_dict = TargetAllocation({})

        return TargetAllocation(allocation_dict)