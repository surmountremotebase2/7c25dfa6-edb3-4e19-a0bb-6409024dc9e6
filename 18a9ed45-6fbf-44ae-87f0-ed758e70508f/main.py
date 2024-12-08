from surmount.base_class import Strategy, TargetAllocation
from surmount.technical_indicators import SMA, MACD, RSI, ATR, STDEV
from surmount.logging import log
import pandas as pd
import numpy as np

class TradingStrategy(Strategy):
    
    print_flag = 1
    
    @property
    def assets(self):
        return ["SPXL", "SPXS", "SPY"]

    @property
    def interval(self):
        return "1day"

    def run(self, data):
        # Compute ATR for SPY (using a 14-day window as an example)
        atr_values = ATR("SPY", data["ohlcv"], length=14)
        current_vol = atr_values[-1] if len(atr_values) > 0 else 0.0

        # Example threshold for "high" volatility (this is arbitrary and should be tuned)
        vol_threshold = 5.0  # Adjust this based on typical ATR values for SPY

        # Compute MACD and RSI for SPY
        macd_SPY = MACD("SPY", data["ohlcv"], 12, 26)
        rsi_SPY = RSI("SPY", data["ohlcv"], 14)

        macdh_SPY = macd_SPY['MACDh_12_26_9']
        latest_macdh = macdh_SPY[-1] if len(macdh_SPY) > 0 else 0
        latest_rsi_spy = rsi_SPY[-1] if len(rsi_SPY) > 0 else 50

        # Determine market regime
        bullish = (latest_macdh > 0) and (latest_rsi_spy < 70)
        bearish = (latest_macdh < 0) and (latest_rsi_spy > 30)

        # Adjust allocations based on ATR-based volatility
        if bullish:
            if current_vol < vol_threshold:
                allocation_dict = {"SPXL": 0.8, "SPY": 0.2, "SPXS": 0.0}
            else:
                allocation_dict = {"SPXL": 0.4, "SPY": 0.6, "SPXS": 0.0}
        elif bearish:
            if current_vol < vol_threshold:
                allocation_dict = {"SPXL": 0.0, "SPY": 0.2, "SPXS": 0.8}
            else:
                allocation_dict = {"SPXL": 0.0, "SPY": 0.6, "SPXS": 0.4}
        else:
            allocation_dict = {"SPXL": 0.0, "SPY": 1.0, "SPXS": 0.0}

        return TargetAllocation(allocation_dict)