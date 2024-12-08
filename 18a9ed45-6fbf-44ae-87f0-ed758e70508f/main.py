from surmount.base_class import Strategy, TargetAllocation
from surmount.technical_indicators import SMA, MACD, RSI
from surmount.logging import log
import pandas as pd
import numpy as np

class TradingStrategy(Strategy):
    @property
    def assets(self):
        return ["SPXL", "SPXS", "SPY"]

    @property
    def interval(self):
        return "1day"

    def run(self, data):
        # Extract OHLCV data for SPY
        spy_data = data["ohlcv"]["SPY"]
        
        # Compute returns and rolling volatility (14-day std of returns)
        returns = spy_data["close"].pct_change()
        vol_window = 14
        vol = returns.rolling(vol_window).std().dropna()
        current_vol = vol.iloc[-1] if len(vol) > 0 else 0.0

        # Volatility threshold (tweak this as needed)
        # For example, a threshold of 2% daily std: 
        vol_threshold = 0.02

        # Compute MACD and RSI for SPY as signals
        macd_SPY = MACD("SPY", data["ohlcv"], fast=12, slow=26, signal=9)  # standard MACD parameters
        rsi_SPY = RSI("SPY", data["ohlcv"], length=14)

        # We will determine market regime based on MACD histogram and RSI
        macdh_SPY = macd_SPY['MACDh_12_26_9']
        latest_macdh = macdh_SPY[-1] if len(macdh_SPY) > 0 else 0
        latest_rsi_spy = rsi_SPY[-1] if len(rsi_SPY) > 0 else 50

        # Simple regime logic:
        # Bullish if MACD histogram > 0 and RSI < 70
        # Bearish if MACD histogram < 0 and RSI > 30
        # Neutral otherwise
        bullish = (latest_macdh > 0) and (latest_rsi_spy < 70)
        bearish = (latest_macdh < 0) and (latest_rsi_spy > 30)

        # Set baseline allocations
        # Adjust allocation depending on volatility and signals
        # If volatility is high, reduce leveraged exposure.
        # If bullish and low vol: more SPXL, some SPY
        # If bullish and high vol: less SPXL, more SPY
        # If bearish and low vol: more SPXS, some SPY
        # If bearish and high vol: less SPXS, more SPY
        # If neutral: mostly SPY

        if bullish:
            if current_vol < vol_threshold:
                # Low vol & bullish
                allocation_dict = {
                    "SPXL": 0.8,
                    "SPY": 0.2,
                    "SPXS": 0.0
                }
            else:
                # High vol & bullish
                allocation_dict = {
                    "SPXL": 0.4,
                    "SPY": 0.6,
                    "SPXS": 0.0
                }

        elif bearish:
            if current_vol < vol_threshold:
                # Low vol & bearish
                allocation_dict = {
                    "SPXL": 0.0,
                    "SPY": 0.2,
                    "SPXS": 0.8
                }
            else:
                # High vol & bearish
                allocation_dict = {
                    "SPXL": 0.0,
                    "SPY": 0.6,
                    "SPXS": 0.4
                }
        else:
            # Neutral scenario
            # Mostly SPY to hedge, minimal leveraged exposure
            allocation_dict = {
                "SPXL": 0.0,
                "SPY": 1.0,
                "SPXS": 0.0
            }

        return TargetAllocation(allocation_dict)
