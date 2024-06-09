from surmount.base_class import Strategy, TargetAllocation, backtest
from surmount.logging import log
from datetime import datetime

class TradingStrategy(Strategy):

    def __init__(self):
        self.tickers = [
            "DKNG", "WYNN", "LVS", "CZR", "MLCO", "MGM", "PENN", "IGT", "LNW", "GDEN",
            "BYD"
        ]
        self.weights = [
            0.04, 0.08, 0.04, 0.1, 0.05, 0.08, 0.125, 0.125, 0.1, 0.13, 0.13
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
        
        if today.day == 11 or (today.day > 11 and yesterday.day < 11):
            # Normalize the weights to add up to 1
            total_weight = sum(self.weights)
            allocation_dict = {self.tickers[i]: self.weights[i] / total_weight for i in range(len(self.tickers))}
            return TargetAllocation(allocation_dict)
        return None
