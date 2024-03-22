from surmount.base_class import Strategy, TargetAllocation
from surmount.technical_indicators import SMA, MACD, RSI  # We'll use the Simple Moving Average (SMA)
from surmount.logging import log
from surmount.data import Asset

class TradingStrategy(Strategy):
    @property
    def assets(self):
        return ["SPXL", "SPXS", "SPY"]

    @property
    def interval(self):
        return "1day"

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

        spy_recents = sma_SPY[-3:]
        spy_differences = [spy_recents[i+1] - spy_recents[i] for i in range(len(spy_recents)-1)]

        
        upward_trend = sum(d > 0 for d in spy_differences)
        downward_trend = sum(d < 0 for d in spy_differences)

        macdh_SPY = macd_SPY['MACDh_5_10_9']

        if macdh_SPY[-1] < -1.68:
            allocation_dict = {"SPXS": 100, "SPXL": 0}
        else:
            if rsi_SPY[-1] < 62: 
                allocation_dict = {"SPXS": 0, "SPXL": 100}
            else:
                allocation_dict = {"SPXL": 0, "SPXS": 0}


        return TargetAllocation(allocation_dict)



