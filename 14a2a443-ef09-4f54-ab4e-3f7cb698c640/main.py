from surmount.base_class import Strategy, TargetAllocation, backtest
from surmount.logging import log
from datetime import datetime

class TradingStrategy(Strategy):

    def __init__(self):
        self.tickers = [
            "AMZN", "AAPL", "META", "GOOGL", "MSFT", "NVDA", "PYPL", "SHOP",
            "SQ", "TSLA", "TTD", "ADBE", "ATVI", "NFLX", "TWLO", "ZM", "ROKU",
            "PTON", "SNAP", "SE", "SPOT", "PINS", "UBER", "LYFT", "DOCU", "ETSY",
            "ZG", "W", "CHWY", "CRWD"
        ]
        self.weights = [
            0.045, 0.045, 0.045, 0.045, 0.045, 0.035, 0.035, 0.035,
            0.035, 0.035, 0.03, 0.03, 0.03, 0.03, 0.025, 0.025, 0.025,
            0.025, 0.025, 0.02, 0.02, 0.02, 0.02, 0.02, 0.015, 0.015,
            0.015, 0.015, 0.015, 0.015
        ]
        self.count = 0

    @property
    def interval(self):
        return "1day"

    @property
    def assets(self):
        return self.tickers

    def run(self, data):
        
        if count % 7 == 0:
            allocation_dict = {self.tickers[i]: self.weights[i] for i in range(len(self.tickers))}
            return TargetAllocation(allocation_dict)
        return None