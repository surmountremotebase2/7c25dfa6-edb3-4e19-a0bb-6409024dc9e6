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

    @property
    def interval(self):
        return "1day"

    @property
    def assets(self):
        return self.tickers

    def run(self, data):
        today = datetime.strptime(str(next(iter(data['ohlcv'][-1].values()))['date']), '%Y-%m-%d %H:%M:%S')
        yesterday = datetime.strptime(str(next(iter(data['ohlcv'][-2].values()))['date']), '%Y-%m-%d %H:%M:%S')
        
        if today.day == 7 or (today.day > 7 and yesterday.day < 7):
            allocation_dict = {self.tickers[i]: self.weights[i] for i in range(len(self.tickers))}
            return TargetAllocation(allocation_dict)
        return None
