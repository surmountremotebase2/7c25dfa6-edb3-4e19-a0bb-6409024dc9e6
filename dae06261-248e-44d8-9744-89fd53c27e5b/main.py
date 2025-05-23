from surmount.base_class import Strategy, TargetAllocation
from surmount.technical_indicators import SMA
from surmount.logging import log
import pandas as pd 
import numpy as np 

from surmount.logging import log
from datetime import datetime

class TradingStrategy(Strategy):
    @property
    def assets(self):
        # Define the assets to be used in the strategy
        return ["BTC-USD"]

    @property
    def interval(self):
        # The data interval desired for the strategy. Daily in this case.
        return "1hour"
    
    def __init__(self):
      self.count = 0
      self.buy_price = 0
      self.watermark = 0
    
    '''def run(self, data):
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

        return TargetAllocation(allocation_dict)'''
    
    '''def run(self, data):
        #allocation_dict = {"BTCUSD": 1.0}
        #return TargetAllocation(allocation_dict)
        # Calculate SMAs
        three_sma = SMA("BTCUSD", data["ohlcv"], length=5)
        five_sma = SMA("BTCUSD", data["ohlcv"], length=10)

        # Set the number of periods to confirm the upward trend
        N = 2  # Reduced from 3 to 2

        # Check if the 3-period SMA has been increasing for the last N periods
        upward_trend = all([three_sma[-i] > three_sma[-i-1] for i in range(1, N+1)])

        # Relaxed moving average alignment
        ma_alignment = three_sma[-1] > five_sma[-1]

        # Include RSI for momentum confirmation
        from surmount.technical_indicators import RSI
        rsi = RSI("BTCUSD", data["ohlcv"], length=14)
        momentum = rsi[-1] > 50

        # Position sizing based on confidence levels
        if upward_trend and ma_alignment and momentum:
            allocation_dict = {"BTCUSD": 1.0}
        elif upward_trend and ma_alignment:
            allocation_dict = {"BTCUSD": 0.5}
        else:
            allocation_dict = {"BTCUSD": 0.0}

        # Exit strategy with confirmation
        exit_signal = (three_sma[-1] < five_sma[-1]) and (rsi[-1] < 50)
        if exit_signal:
            allocation_dict = {"BTCUSD": 0.0}

        return TargetAllocation(allocation_dict)'''

    def run(self, data):
        #allocation_dict = {"BTCUSD": 1.0}

        if self.count < 1:
            self.count += 1
            allocation_dict = {"BTC-USD": 0.0}
            return TargetAllocation(allocation_dict)

        self.count += 1

        # Calculate the hitorical SMA's for BTCUSD
        three_sma = SMA("BTC-USD", data["ohlcv"], length=3)
        five_sma = SMA("BTC-USD", data["ohlcv"], length=5)
        seven_sma = SMA("BTC-USD", data["ohlcv"], length=7)
        ten_sma = SMA("BTC-USD", data["ohlcv"], length=10)
        
        if self.buy_price > 0:
            if self.watermark < data["ohlcv"][-1]["BTC-USD"]["close"]:
                self.watermark = data["ohlcv"][-1]["BTC-USD"]["close"]
                
            if ((self.buy_price - data["ohlcv"][-1]["BTC-USD"]["close"]) / self.buy_price) > .02 or ((self.watermark - data["ohlcv"][-1]["BTC-USD"]["close"]) / self.watermark) > 0.01:
                log("Trailing or full exit hit")
                self.watermark = 0
                self.buy_price = 0
                allocation_dict = {"BTC-USD": 0.0}
                self.count = -10
                return TargetAllocation(allocation_dict)
            
            if ((data["ohlcv"][-1]["BTC-USD"]["close"] - self.buy_price) / self.buy_price) > .5:
                log("Take profit hit")
                self.watermark = 0
                self.buy_price = 0
                allocation_dict = {"BTC-USD": 0.0}
                self.count = -5
                return TargetAllocation(allocation_dict)

        if three_sma[-1] > three_sma[-2] and three_sma[-2] > three_sma[-3]:
            if three_sma[-1] > five_sma[-1]:
                allocation_dict = {"BTC-USD": 1.0}
                #log(str(data["ohlcv"][-1]["BTC-USD"]["close"]))
                self.buy_price = float(data["ohlcv"][-1]["BTC-USD"]["close"])
                self.watermark = float(data["ohlcv"][-1]["BTC-USD"]["close"])
            else:
                self.buy_price = 0
                allocation_dict = {"BTC-USD": 0.0}
        else:
            self.buy_price = 0
            allocation_dict = {"BTC-USD": 0.0}
        
        if not allocation_dict:
            allocation_dict = TargetAllocation({})

        # Return the target allocation based on our logic
        return TargetAllocation(allocation_dict)