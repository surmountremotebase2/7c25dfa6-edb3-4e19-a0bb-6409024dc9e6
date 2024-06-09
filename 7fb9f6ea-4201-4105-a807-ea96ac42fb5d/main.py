from surmount.base_class import Strategy, TargetAllocation, backtest
from surmount.logging import log
from datetime import datetime

class TradingStrategy(Strategy):

    def __init__(self):
        self.tickers = [
            "ILMN", "REGN", "VRTX", "GILD", "AMGN", "BIIB", "TMO", "A", "DHR",
            "BIO", "QGEN", "WAT", "PACB", "PKI", "CRSP", "EDIT", "NTLA", "TWST",
            "TXG", "NVTA", "GH", "ADPT", "PSNL", "MYGN", "BNGO", "VCYT", "IDNA",
            "NSTG", "ARKG"
        ]
        self.weights = [
            0.065, 0.065, 0.065, 0.055, 0.055, 0.055, 0.045, 0.045, 0.045,
            0.045, 0.035, 0.035, 0.035, 0.035, 0.025, 0.025, 0.025, 0.025,
            0.025, 0.025, 0.015, 0.015, 0.015, 0.015, 0.015, 0.015, 0.015,
            0.015, 0.015
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
            if counter >= 30:
                allocation_dict = {self.tickers[i]: self.weights[i] for i in range(len(self.tickers))}
                self.counter = 0
                return TargetAllocation(allocation_dict)
            else:
                return None

        today = datetime.strptime(str(next(iter(data['ohlcv'][-1].values()))['date']), '%Y-%m-%d %H:%M:%S')
        yesterday = datetime.strptime(str(next(iter(data['ohlcv'][-2].values()))['date']), '%Y-%m-%d %H:%M:%S')
        
        if today.day == 12 or (today.day > 12 and yesterday.day < 12):
            allocation_dict = {self.tickers[i]: self.weights[i] for i in range(len(self.tickers))}
            return TargetAllocation(allocation_dict)
        return None
