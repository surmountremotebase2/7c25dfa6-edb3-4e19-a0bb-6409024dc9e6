from surmount.base_class import Strategy, TargetAllocation
from surmount.technical_indicators import SMA, MACD  # We'll use the Simple Moving Average (SMA)
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
        macd_SPY = MACD("SPY", data["ohlcv"], 15, 30) # we want to use the MACDh_12_26_9

        if not sma_VIX or len(sma_VIX) < 5:
            return TargetAllocation({})

        macdh_SPY = macd_SPY['MACDh_15_30_9']

        # Figure out the general trend of SPY
        if macdh_SPY[-1] > -0.15:
            if sma_VIX[-1] > 20:
                allocation_dict = {"SPXL": 100, "SPXS": 0}
            else:
                allocation_dict = {"SPXL": 0, "SPXS": 0}
        else:
            if sma_VIX[-1] > 25:
                allocation_dict = {"SPXS": 100, "SPXL": 0}
            else: 
                allocation_dict = {"SPXS": 0, "SPXL": 0}

        return TargetAllocation(allocation_dict)