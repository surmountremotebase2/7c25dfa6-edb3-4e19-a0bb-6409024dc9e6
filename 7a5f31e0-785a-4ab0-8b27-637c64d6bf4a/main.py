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

    def isThursdayAfternoon(self, date_string):
        date_format = "%Y-%m-%d %H:%M:%S"
        native_datetime = datetime.strptime(date_string, date_format)

        is_thursday = native_datetime.weekday() == 2

        start_time = time(14, 30)
        end_time = time(15, 30)
        is_time = start_time <= native_datetime.time() <= end_time

        #log("Thursday Check: ")
        #log(str(is_thursday))
        #log(str(is_time))

        return is_thursday and is_time
    
    def isFridayAfternoon(self, date_string):
        date_format = "%Y-%m-%d %H:%M:%S"
        native_datetime = datetime.strptime(date_string, date_format)

        is_friday = native_datetime.weekday() == 4

        start_time = time(14, 30)
        end_time = time(15, 30)
        is_time = start_time <= native_datetime.time() <= end_time

        #log("Friday Check: ")
        #log(str(is_friday))
        #log(str(is_time))

        return is_friday and is_time
    
    def isMondayAfternoon(self, date_string):
        date_format = "%Y-%m-%d %H:%M:%S"
        native_datetime = datetime.strptime(date_string, date_format)

        is_monday = native_datetime.weekday() == 0

        start_time = time(14, 30)
        end_time = time(15, 30)
        is_time = start_time <= native_datetime.time() <= end_time

        #log("Monday Check: ")
        #log(str(is_monday))
        #log(str(is_time))
        #log(str(native_datetime))

        return is_monday and is_time

    def run(self, data):
        # This is the principal method where the strategy logic is defined.
        #log(str(data["ohlcv"][-1]["SPY"]['date']))
        '''if self.isThursdayAfternoon(data["ohlcv"][-1]["SPY"]['date']):
            #log(str(data["ohlcv"][-1]))
            #log("Thursday Afternoon - going short")
            allocation_dict = {"SPXS": 0.75, "SPXL": 0.25}
        elif self.isFridayAfternoon(data["ohlcv"][-1]["SPY"]['date']):
            #log("Friday afternoon - going long")
            allocation_dict = {"SPXS": 0.25, "SPXL": 0.75}
        elif self.isMondayAfternoon(data["ohlcv"][-1]["SPY"]['date']):
            #log("Monday Afternoon - exiting")
            allocation_dict = {"SPXS": 0, "SPXL": 0}
        else:
            allocation_dict = {"SPY": 0}'''
        
        if self.isFridayAfternoon(data["ohlcv"][-1]["SPY"]['date']) and data["ohlcv"][-1]["SPY"]["open"] > data["ohlcv"][-1]["SPY"]["close"]:
            allocation_dict = {"SPXL": 1}
        elif self.isMondayAfternoon(data["ohlcv"][-1]["SPY"]['date']):
            allocation_dict = {"SPXL": 0}
        else:
            allocation_dict = {"SPY": 0}

        
        if not allocation_dict:
            allocation_dict = TargetAllocation({})

        # Return the target allocation based on our logic
        return TargetAllocation(allocation_dict)
