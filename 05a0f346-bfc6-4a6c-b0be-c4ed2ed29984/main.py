from surmount.base_class import Strategy, TargetAllocation
from surmount.technical_indicators import SMA, MACD, RSI
from surmount.logging import log
from surmount.data import Asset 
import random 

class TradingStrategy(Strategy):
    @property
    def assets(self):
        return self.randomAssets()

    @property 
    def interval(self):
        return "1day"
    
    def randomAssets(self):
        init_list = ['SPY', 'GME', 'NVDA', 'MSFT', 'F', 'AAPL', 'GOOG', 'FAZ', 'SPXL', 'SPXS']
        return_list = []
        for ticker in init_list:
            if random() < .5:
                return_list.append(ticker)
        return return_list

    def run(self, data):
        log(str(data))

        return None