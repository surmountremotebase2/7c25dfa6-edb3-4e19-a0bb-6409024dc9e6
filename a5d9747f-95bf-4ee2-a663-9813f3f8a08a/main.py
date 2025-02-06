from surmount.base_class import Strategy, TargetAllocation
from surmount.technical_indicators import SMA
from surmount.logging import log
import pandas as pd
import numpy as np

class TradingStrategy(Strategy):

    def __init__(self):
        self.counter = 0

    @property
    def assets(self):
        """
        A broader set of 3x leveraged ETFs covering various market segments:
          - S&P 500 (SPXL)
          - NASDAQ (TQQQ)
          - Dow (UDOW)
          - Small Caps (TNA)
          - Financials (FAS)
          - Technology (TECL)
          - Semiconductors (SOXL)
        """
        return ["SPXL", "TQQQ", "UDOW", "TNA", "FAS", "TECL", "SOXL"]

    @property
    def interval(self):
        # The data interval desired for the strategy. Daily in this case.
        return "1day"

    def run(self, data):
        """
        1. Calculate 5-day SMA for each asset.
        2. Determine the percent change of that 5-day SMA from 5 days ago to today.
        3. Pick the top 3 performers based on this metric.
        4. Allocate equally among them.
        """

        # Weekly rebalance
        if self.counter % 7 != 0:
            return TargetAllocation({})
        
        # Calculate 5-day SMA for each asset
        sma_dict = {}
        for asset in self.assets:
            sma_series = SMA(asset, data["ohlcv"], length=5)
            sma_dict[asset] = sma_series

        # Calculate performance over the last 5 trading days
        # (SMA[-1] - SMA[-5]) / SMA[-5]
        performance = {}
        for asset, sma_series in sma_dict.items():
            if len(sma_series) < 5:
                # Not enough data => rank very low
                performance[asset] = float("-inf")
            else:
                last_val = sma_series[-1]
                five_days_ago_val = sma_series[-5]
                if five_days_ago_val == 0:
                    performance[asset] = float("-inf")
                else:
                    performance[asset] = (last_val - five_days_ago_val) / five_days_ago_val

        # Sort by performance (descending), and pick top 3
        top_3_assets = sorted(performance, key=performance.get, reverse=True)[:3]

        # Create allocation dict with equal weights among the top 3
        allocation_dict = {asset: 1.0 / 3.0 for asset in top_3_assets}

        return TargetAllocation(allocation_dict)
