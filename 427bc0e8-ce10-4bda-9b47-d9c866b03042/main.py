from surmount.base_class import Strategy, TargetAllocation
from surmount.technical_indicators import SMA  # We'll use the Simple Moving Average (SMA)
from surmount.logging import log
from surmount.data import Asset

class TradingStrategy(Strategy):
    @property
    def assets(self):
        return ["VIX", "SPXL", "SPXS"]

    @property
    def interval(self):
        return "1day"

    def run(self, data):
        # Calculating the 5-day SMA for VIX
        sma_VIX = SMA("VIX", data["ohlcv"], length=5)

        if not sma_VIX or len(sma_VIX) < 5:
            return TargetAllocation({})
        
        if sma_VIX[-1] < 25:
            allocation_dict = {"SPXS": 0}
        else:
            allocation_dict = {"SPXS": 100}

        return TargetAllocation(allocation_dict)