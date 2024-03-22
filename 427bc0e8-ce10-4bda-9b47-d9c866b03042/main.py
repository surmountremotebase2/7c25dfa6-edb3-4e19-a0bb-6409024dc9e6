from surmount.base_class import Strategy, TargetAllocation
from surmount.technical_indicators import SMA, MACD, RSI  # We'll use the Simple Moving Average (SMA)
from surmount.logging import log
from surmount.data import Asset

class TradingStrategy(Strategy):
    @property
    def assets(self):
        return ["VIX", "SPXL", "SPXS", "SPY"]

    @property
    def interval(self):
        return "1day"

    def run(self, data):
        # Calculating the 5-day SMA for VIX
        sma_VIX = SMA("VIX", data["ohlcv"], length=5)
        macd_SPY = MACD("SPY", data["ohlcv"], 5, 10) # we want to use the MACDh_12_26_9

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

        if not sma_VIX or len(sma_VIX) < 5:
            return TargetAllocation({})

        macdh_SPY = macd_SPY['MACDh_5_10_9']

        # Figure out the general trend of SPY
        '''if macdh_SPY[-1] > -0.15:
            if sma_VIX[-1] > 27:
                allocation_dict = {"SPXL": 100, "SPXS": 0}
            else:
                allocation_dict = {"SPXL": 0, "SPXS": 0}
        else:
            if sma_VIX[-1] > 27:
                allocation_dict = {"SPXS": 100, "SPXL": 0}
            else: 
                allocation_dict = {"SPXS": 0, "SPXL": 0}'''
        
        '''if macdh_SPY[-1] > 2:
            allocation_dict = {"SPXS": 100, "SPXL": 0}
        elif macdh_SPY[-1] < -0.1:
            allocation_dict = {"SPXL": 100, "SPXS": 0}
        else:
            allocation_dict = {}'''

        if macdh_SPY[-1] < -1.75:
            allocation_dict = {"SPXS": 100, "SPXL": 0}
        else:
            if rsi_SPY[-1] > 60: 
                allocation_dict = {"SPXS": 0, "SPXL": 100}
            else:
                allocation_dict = {"SPXL": 0, "SPXS": 0}


        return TargetAllocation(allocation_dict)



