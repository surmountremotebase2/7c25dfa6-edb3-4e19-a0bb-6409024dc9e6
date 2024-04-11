from surmount.base_class import Strategy, TargetAllocation
from surmount.technical_indicators import SMA, MACD, RSI, EMA  # We'll use the Simple Moving Average (SMA)
from surmount.logging import log
from surmount.data import Asset
import json

class TradingStrategy(Strategy):
    @property
    def assets(self):
        return ["SPXL", "SPXS", "SPY"]

    @property
    def interval(self):
        return "1hour"

    def run(self, data):
        macd_SPY = MACD("SPY", data["ohlcv"], 5, 10)

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

        '''if upward_trend > downward_trend: # Go in on long
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
            return TargetAllocation({})'''

        short_sma_SPY = SMA("SPY", data['ohlcv'], length=5)
        short_ema_SPY = EMA("SPY", data['ohlcv'], length=5)

        if not short_ema_SPY or short_ema_SPY > short_sma_SPY:
            # Bull Market
            allocation_dict = {"SPXL": 100, "SPXS": 0}
        else:
            # Bear Market
            allocation_dict = {"SPXL": 0, "SPXS": 100}

        '''if data['ohlcv'][-1]['SPY']['close'] > (short_ema_SPY[-1] * 1.02):
            # Above our short SMA with buffer - upward trajectory
            logging_value = "Upward Potential on: " + data['ohlcv'][-1]['SPY']['date']
            log(logging_value)
            if rsi_SPY[-1] < 62:
                allocation_dict = {"SPXS": 10, "SPXL": 90}
            else:
                allocation_dict = {"SPXL": 0, "SPXS": 0}
        elif data['ohlcv'][-1]['SPY']['close'] < (short_sma_SPY[-1] * 1.02):
            # Below our short SMA with buffer - downward trajectory
            if macdh_SPY[-1] < -1.68:
                allocation_dict = {"SPXS": 100, "SPXL": 0}
            else:
                allocation_dict = {"SPXL": 0, "SPXS": 0}
        else:
            # About even - we don't really care.
            return TargetAllocation({}) '''

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