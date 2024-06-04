from surmount.base_class import Strategy, TargetAllocation
from surmount.technical_indicators import SMA
from surmount.logging import log
import pandas as pd 
import numpy as np 
from surmount.data import SentateTrades

class TradingStrategy(Strategy):
    @property
    def assets(self):
        # Define the assets to be used in the strategy
        self.data_list = [SentateTrades("AAPL")]
        return ["AAPL"]

    @property
    def interval(self):
        # The data interval desired for the strategy. Daily in this case.
        return "4hour"

    def run(self, data):
        insider_trading_dict = data[("insider_trading", "AAPL")]
        print(insider_trading)