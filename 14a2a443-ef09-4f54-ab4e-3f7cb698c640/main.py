from surmount.base_class import Strategy, TargetAllocation, backtest
from surmount.logging import log
from datetime import datetime

class TradingStrategy(Strategy):

    def __init__(self):
        self.tickers = ["XOM", "CVX", "SLB", "ECL", "APD", "LIN", "OXY", "PSX", "VLO", "PXD", "EOG", "FANG", "CQP", "MPLX", "SRE", "LNG", "WMB", "KMI", "ET"]
        self.weights = [0.1, 0.1, 0.08, 0.08, 0.08, 0.08, 0.08, 0.07, 0.05, 0.04, 0.04, 0.03, 0.03, 0.02, 0.02, 0.01, 0.01, 0.01, 0.01]
        self.equal_weighting = False

    @property
    def interval(self):
        return "1day"

    @property
    def assets(self):
        return self.tickers

    def run(self, data):
        if data['ohlcv']:
            today = datetime.strptime(str(next(iter(data['ohlcv'][-1].values()))['date']), '%Y-%m-%d %H:%M:%S')
            yesterday = datetime.strptime(str(next(iter(data['ohlcv'][-2].values()))['date']), '%Y-%m-%d %H:%M:%S')
            
            if today.day == 14 or (today.day > 14 and yesterday.day < 14):
                if self.equal_weighting:
                    allocation_dict = {i: 1 / len(self.tickers) for i in self.tickers}
                else:
                    allocation_dict = {self.tickers[i]: self.weights[i] for i in range(len(self.tickers))}
                return TargetAllocation(allocation_dict)
        return None