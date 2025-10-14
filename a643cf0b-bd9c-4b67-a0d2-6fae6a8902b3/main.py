from surmount.base_class import Strategy, TargetAllocation
from surmount.technical_indicators import SMA
from surmount.logging import log
import pandas as pd
import numpy as np
from datetime import datetime

class TradingStrategy(Strategy):
    ASSET = "ETH-USD"  # switched from BTC-USD to ETH-USD

    @property
    def assets(self):
        # Define the assets to be used in the strategy
        return [self.ASSET]

    @property
    def interval(self):
        # The data interval desired for the strategy. Hourly bars.
        return "1hour"
    
    def __init__(self):
        self.count = 0
        self.buy_price = 0.0
        self.watermark = 0.0

    def run(self, data):
        # Warm-up one bar with flat allocation
        if self.count < 1:
            self.count += 1
            return TargetAllocation({self.ASSET: 0.0})

        self.count += 1

        # Calculate historical SMAs for ETH-USD
        three_sma = SMA(self.ASSET, data["ohlcv"], length=3)
        five_sma  = SMA(self.ASSET, data["ohlcv"], length=5)
        seven_sma = SMA(self.ASSET, data["ohlcv"], length=7)
        ten_sma   = SMA(self.ASSET, data["ohlcv"], length=10)

        # Current close
        last_close = float(data["ohlcv"][-1][self.ASSET]["close"])

        # If in-position, manage stops / trailing
        if self.buy_price > 0:
            # Update trailing watermark
            if self.watermark < last_close:
                self.watermark = last_close

            # Hard stop: down >2% from entry OR >1% below watermark (trailing stop)
            if ((self.buy_price - last_close) / self.buy_price) > 0.02 or \
               ((self.watermark - last_close) / self.watermark) > 0.01:
                log("Trailing or full exit hit")
                self.watermark = 0.0
                self.buy_price = 0.0
                self.count = -10  # cooldown
                return TargetAllocation({self.ASSET: 0.0})

            # Take profit: +50% from entry
            if ((last_close - self.buy_price) / self.buy_price) > 0.5:
                log("Take profit hit")
                self.watermark = 0.0
                self.buy_price = 0.0
                self.count = -5  # shorter cooldown
                return TargetAllocation({self.ASSET: 0.0})

        # Entry logic: 3-SMA rising for 3 bars and above 5-SMA
        if three_sma[-1] > three_sma[-2] and three_sma[-2] > three_sma[-3]:
            if three_sma[-1] > five_sma[-1]:
                # Go long ETH-USD
                self.buy_price = last_close
                self.watermark = last_close
                allocation_dict = {self.ASSET: 1.0}
            else:
                self.buy_price = 0.0
                allocation_dict = {self.ASSET: 0.0}
        else:
            self.buy_price = 0.0
            allocation_dict = {self.ASSET: 0.0}

        # Return the target allocation based on our logic
        return TargetAllocation(allocation_dict)