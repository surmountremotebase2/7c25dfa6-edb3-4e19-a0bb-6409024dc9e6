from surmount.base_class import Strategy, TargetAllocation
from surmount.technical_indicators import SMA
from surmount.logging import log

from datetime import datetime, time

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
        return "1hour"

    def isThursdayMorning(self, date_string):
        date_format = "%Y-%m-%d %H:%M:%S"
        native_datetime = datetime.strptime(date_string, date_format)

        is_thursday = native_datetime.weekday() == 3

        start_time = time(2, 30)
        end_time = time(3, 30)
        is_time = start_time <= native_datetime.time() <= end_time

        return is_thursday and is_time

    def run(self, data):
        # This is the principal method where the strategy logic is defined.
        log(str(data["ohlcv"][-1]["SPY"]['date']))
        if self.isThursdayMorning(data["ohlcv"][-1]["SPY"]['date']):
            log(str(data["ohlcv"][-1]))
            allocation_dict = {"SPXS": 1.0, "SPXL": 0}
        else:
            allocation_dict = {"SPY": 0}

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
        
        if not allocation_dict:
            allocation_dict = TargetAllocation({})

        # Return the target allocation based on our logic
        return TargetAllocation(allocation_dict)
