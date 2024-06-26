from surmount.base_class import Strategy, TargetAllocation
from surmount.technical_indicators import SMA, MACD, RSI  # We'll use the Simple Moving Average (SMA)
from surmount.logging import log
from surmount.data import Asset
import json

class TradingStrategy(Strategy):
    @property
    def assets(self):
        return ["SPXL", "SPXS", "SPY", "AAPL"]

    @property
    def interval(self):
        return "1day"

    def run(self, data):
        '''macd_SPY = MACD("SPY", data["ohlcv"], 5, 10)

        sma_SPXL = SMA("SPXL", data["ohlcv"], length=5)
        sma_SPY = SMA("SPY", data["ohlcv"], length=5)
        sma_SPXS = SMA("SPXS", data["ohlcv"], length=5)

        rsi_SPY = RSI("SPY", data["ohlcv"], length=14)
        rsi_SPXL = RSI("SPXL", data["ohlcv"], length=14)

        spxl_delta = (sma_SPXL[-1] - sma_SPXL[-2]) / sma_SPXL[-1]
        spy_delta = (sma_SPY[-1] - sma_SPY[-2]) / sma_SPY[-1]
        spxs_delta = (sma_SPXS[-1] - sma_SPXS[-2]) / sma_SPXS[-1]

        spy_recents = sma_SPY[-15:]
        spy_differences = [spy_recents[i+1] - spy_recents[i] for i in range(len(spy_recents)-1)]

        
        upward_trend = sum(d > 0 for d in spy_differences)
        downward_trend = sum(d < 0 for d in spy_differences)

        macdh_SPY = macd_SPY['MACDh_5_10_9']

        if upward_trend > downward_trend: # Go in on long
            if macdh_SPY[-1] < -1.68:
                allocation_dict = {"SPXS": 70, "SPXL": 30}
            else:
                if rsi_SPY[-1] < 62: 
                    allocation_dict = {"SPXS": 10, "SPXL": 90}
                else:
                    allocation_dict = {"SPXL": 0, "SPXS": 0}
        elif upward_trend < downward_trend:
            if macdh_SPY[-1] < -1.68:
                allocation_dict = {"SPXS": 100, "SPXL": 0}
            else:
                if rsi_SPY[-1] < 62: 
                    allocation_dict = {"SPXS": 0, "SPXL": 100}
                else:
                    allocation_dict = {"SPXL": 0, "SPXS": 0}
        else:
            return TargetAllocation({})
            '''

        macd_test = 

        for ticker in self.assets:
            # Idnetify if we're in an upward trend for the Moving Average Breakout 
            # We're going to use a 10-day lookback on our SMA. 
            if data['ohlcv'][-1][ticker] > SMA(ticker, data['ohlcv'], length=10):
                moving_breakout_flag = 1
            else:
                moving_breakout_flag = 0
            
            # Identify if we're at a MACD Breakout point. We're going to use a 8, 17 day MACD. 
            

        allocation_dict = {}

        return TargetAllocation(allocation_dict)



        '''elif upward_trend < downward_trend:
            # Go in on short
            if macdh_SPY[-1] < -1.68:
                allocation_dict = {"SPXS": 90, "SPXL": 10}
            else:
                if rsi_SPY[-1] < 62: 
                    allocation_dict = {"SPXS": 30, "SPXL": 70}
                else:
                    allocation_dict = {"SPXL": 0, "SPXS": 0}'''