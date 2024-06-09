from surmount.base_class import Strategy, TargetAllocation, backtest
from surmount.logging import log
from datetime import datetime

class TradingStrategy(Strategy):

    def __init__(self):
        self.tickers = [
            "NEE", "TSLA", "ENPH", "BEP", "FSLR", "ORA", "TPIC", "RUN", "SEDG", "AWK",
            "WM", "ECL", "XYL", "ITRI", "BLDP", "CLH", "CVA", "BE", "FCEL", "PLUG",
            "AEIS", "DAR", "WTRG", "AMRC", "REGI", "HASI", "PEGX", "AY", "CWEN", "GPRE"
        ]
        self.weights = [
            0.067, 0.067, 0.033, 0.033, 0.033, 0.033, 0.033, 0.033, 0.033, 0.033,
            0.033, 0.033, 0.033, 0.033, 0.033, 0.033, 0.033, 0.033, 0.033, 0.033,
            0.033, 0.033, 0.033, 0.033, 0.033, 0.033, 0.033, 0.033, 0.033, 0.033
        ]

    @property
    def interval(self):
        return "1day"

    @property
    def assets(self):
        return self.tickers

    def run(self, data):

        if len(data['ohlcv']) < 2:
            log(str(data))
            return None


        today = datetime.strptime(str(next(iter(data['ohlcv'][-1].values()))['date']), '%Y-%m-%d %H:%M:%S')
        yesterday = datetime.strptime(str(next(iter(data['ohlcv'][-2].values()))['date']), '%Y-%m-%d %H:%M:%S')
        
        if today.day == 15 or (today.day > 15 and yesterday.day < 15):
            # Normalize the weights to add up to 1
            total_weight = sum(self.weights)
            allocation_dict = {self.tickers[i]: self.weights[i] / total_weight for i in range(len(self.tickers))}
            return TargetAllocation(allocation_dict)
        return None
