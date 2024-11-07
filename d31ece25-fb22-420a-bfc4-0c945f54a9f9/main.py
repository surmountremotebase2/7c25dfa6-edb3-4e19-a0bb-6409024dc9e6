from surmount.base_class import Strategy, TargetAllocation, backtest
from surmount.logging import log

class TradingStrategy(Strategy):
    def __init__(self):
        self.tickers = ["NVDA"]
        self.weights = [100]

    @property
    def interval(self):
        return "1hour"

    @property
    def assets(self):
        return self.tickers

    def run(self, data):
        allocation_dict = {self.tickers[i]: self.weights[i]/sum(self.weights) for i in range(len(self.tickers))}
        return TargetAllocation(allocation_dict)
