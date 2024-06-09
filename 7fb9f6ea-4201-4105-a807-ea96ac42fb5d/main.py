from surmount.base_class import Strategy, TargetAllocation, backtest
from surmount.logging import log
from datetime import datetime

class TradingStrategy(Strategy):

    def __init__(self):
        self.tickers = [
            "CMI", "ETN", "HON", "LMT", "NOC", "RMD", "UNP", "WM", "NEE",
            "AWK", "ECL", "XYL", "ITRI", "PH", "GIS", "WTRG", "VST", "EXC",
            "NEP", "ENPH", "RUN", "ORA", "FSLR", "SEDG", "BE", "AY", "HASI",
            "REG", "CLX", "VZ", "T", "TMUS"
        ]
        self.weights = [
            0.08, 0.08, 0.08, 0.07, 0.07, 0.07, 0.07, 0.06, 0.06,
            0.05, 0.05, 0.05, 0.04, 0.04, 0.03, 0.03, 0.03, 0.02,
            0.02, 0.02, 0.02, 0.02, 0.02, 0.02, 0.02, 0.01, 0.01,
            0.01, 0.01, 0.01, 0.01
        ]
        self.counter = 0

    @property
    def interval(self):
        return "1day"

    @property
    def assets(self):
        return self.tickers

    def run(self, data):
        if len(data['ohlcv']) < 2:
            self.counter += 1
            if self.counter >= 30:
                self.counter = 0
                total_weight = sum(self.weights)
                allocation_dict = {self.tickers[i]: self.weights[i] / total_weight for i in range(min(len(self.tickers), len(self.weights)))}
                return TargetAllocation(allocation_dict)
            else:
                return None

        today = datetime.strptime(str(next(iter(data['ohlcv'][-1].values()))['date']), '%Y-%m-%d %H:%M:%S')
        yesterday = datetime.strptime(str(next(iter(data['ohlcv'][-2].values()))['date']), '%Y-%m-%d %H:%M:%S')
        
        if today.day == 15 or (today.day > 15 and yesterday.day < 15):
            total_weight = sum(self.weights)
            allocation_dict = {self.tickers[i]: self.weights[i] / total_weight for i in range(min(len(self.tickers), len(self.weights)))}
            return TargetAllocation(allocation_dict)
        return None
