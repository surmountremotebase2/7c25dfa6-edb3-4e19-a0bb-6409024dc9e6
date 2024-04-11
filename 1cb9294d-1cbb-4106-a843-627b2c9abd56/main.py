from surmount.base_class import Strategy, TargetAllocation
from surmount.technical_indicators import SMA, MACD, RSI, EMA  # We'll use the Simple Moving Average (SMA)
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
        #macd_SPY = MACD("SPY", data["ohlcv"], 5, 10)

        #spy_recents = sma_SPY[-15:]
        #spy_differences = [spy_recents[i+1] - spy_recents[i] for i in range(len(spy_recents)-1)]

        
        #upward_trend = sum(d > 0 for d in spy_differences)
        #downward_trend = sum(d < 0 for d in spy_differences)

        #macdh_SPY = macd_SPY['MACDh_5_10_9']

        short_sma_SPY = SMA("SPY", data['ohlcv'], length=3)
        short_ema_SPY = EMA("SPY", data['ohlcv'], length=3)

        if short_ema_SPY[-1] > (short_sma_SPY[-1] * 1.02):
            # Bull Market
            allocation_dict = {"SPXL": 90, "SPXS": 10}
        elif short_sma_SPY[-1] > (short_ema_SPY[-1] * 1.02):
            # Bear Market
            allocation_dict = {"SPXL": 10, "SPXS": 90}
        else:
            allocation_dict = {}

        return TargetAllocation(allocation_dict)