from surmount.base_class import Strategy, TargetAllocation, backtest
from surmount.logging import log
from datetime import datetime

class TradingStrategy(Strategy):

    def __init__(self):
        self.tickers = [
            "GM", "BBY", "ADP", "BBWI", "WBA", "HSY", "VTR", "ORCL", "LNC", "TPR",
            "FIS", "C", "NDAQ", "DUK", "PGR", "AWK", "OXY", "BEN", "LUMN", "VRTX",
            "CDW", "CNC", "CVS", "OTIS", "GD", "REG", "PH", "ZTS", "PCG", "CLX",
            "ROST", "CMI", "CE", "AEP", "AMD", "ACN", "UPS", "CDAY", "ANET", "NOC"
        ]
        self.weights = [
            0.04, 0.02, 0.03, 0.02, 0.03, 0.03, 0.02, 0.04, 0.02, 0.02,
            0.03, 0.03, 0.02, 0.03, 0.03, 0.02, 0.02, 0.02, 0.01, 0.02,
            0.02, 0.02, 0.03, 0.02, 0.03, 0.01, 0.02, 0.03, 0.01, 0.03,
            0.02, 0.02, 0.02, 0.03, 0.03, 0.03, 0.03, 0.02, 0.01, 0.03,
            0.01, 0.03
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
              # Normalize the weights to add up to 1
              total_weight = sum(self.weights)
              allocation_dict = {self.tickers[i]: self.weights[i]/total_weight for i in range(len(self.tickers))}
              return TargetAllocation(allocation_dict)
           else:
              return None


        today = datetime.strptime(str(next(iter(data['ohlcv'][-1].values()))['date']), '%Y-%m-%d %H:%M:%S')
        yesterday = datetime.strptime(str(next(iter(data['ohlcv'][-2].values()))['date']), '%Y-%m-%d %H:%M:%S')
        
        if today.day == 17 or (today.day > 17 and yesterday.day < 17):
            # Normalize the weights to add up to 1
            total_weight = sum(self.weights)
            allocation_dict = {self.tickers[i]: self.weights[i]/total_weight for i in range(len(self.tickers))}
            return TargetAllocation(allocation_dict)
        return None
