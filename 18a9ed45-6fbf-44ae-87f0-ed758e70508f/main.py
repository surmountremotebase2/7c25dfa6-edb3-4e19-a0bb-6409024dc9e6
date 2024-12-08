from surmount.base_class import Strategy, TargetAllocation
from surmount.technical_indicators import SMA, MACD, RSI  # We'll use the Simple Moving Average (SMA)
from surmount.logging import log
from surmount.data import Asset

class TradingStrategy(Strategy):
    @property
    def assets(self):
        return ["SPXL", "SPXS", "SPY", "SH"]

    @property
    def interval(self):
        return "1day"

    def run(self, data):
        macd_SPY = MACD("SPY", data["ohlcv"], 5, 10)
        sma_SPXL = SMA("SPXL", data["ohlcv"], length=5)
        sma_SPY = SMA("SPY", data["ohlcv"], length=5)
        sma_SPXS = SMA("SPXS", data["ohlcv"], length=5)
        
        # Add longer-term SMA for trend confirmation
        sma_SPY_long = SMA("SPY", data["ohlcv"], length=20)
        
        rsi_SPY = RSI("SPY", data["ohlcv"], length=14)
        rsi_SPXL = RSI("SPXL", data["ohlcv"], length=14)

        # Calculate trends
        spy_recents = sma_SPY[-3:]
        spy_differences = [spy_recents[i+1] - spy_recents[i] for i in range(len(spy_recents)-1)]
        upward_trend = sum(d > 0 for d in spy_differences)
        downward_trend = sum(d < 0 for d in spy_differences)

        macdh_SPY = macd_SPY['MACDh_5_10_9']
        
        # Position sizing based on trend strength and RSI
        position_size = 1.0
        if 30 <= rsi_SPY[-1] <= 70:  # Reduce position in moderate RSI
            position_size = 0.75
        if 20 <= rsi_SPY[-1] <= 80:  # Further reduce in extreme RSI
            position_size = 0.5

        # Stop loss conditions
        if sma_SPY[-1] < sma_SPY_long[-1] * 0.95:  # 5% below long-term SMA
            allocation_dict = {"SPXL": 0, "SPXS": 0}
            return TargetAllocation(allocation_dict)

        # Modified entry conditions with trend confirmation
        if macdh_SPY[-1] < -1.68 and downward_trend >= 1:
            allocation_dict = {"SPXS": position_size, "SPXL": 0}
        else:
            if rsi_SPY[-1] < 62 and upward_trend >= 1:
                allocation_dict = {"SPXS": 0, "SPXL": position_size}
            else:
                allocation_dict = {"SPXL": 0, "SPXS": 0}

        return TargetAllocation(allocation_dict)