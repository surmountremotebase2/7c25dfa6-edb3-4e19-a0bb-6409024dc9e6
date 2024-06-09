from surmount.base_class import Strategy, TargetAllocation, backtest
from surmount.logging import log
from datetime import datetime

class TradingStrategy(Strategy):

   def __init__(self):
      self.tickers = ["AMGN", "GILD", "VRTX", "REGN", "ILMN", "MRNA", "BNTX", "CRSP", "EDIT", "NTLA", "ALNY", "SRPT", "CPRX", "NVAX", "BNGO", "GMAB", "SGEN", "BMRN", "INCY", "ARKG", "BNGE", "NBIX", "EXEL", "FATE", "IOVA", "SGMO", "HZNP", "QURE", "VCEL"]
      self.weights = [0.08, 0.065, 0.065, 0.055, 0.065, 0.055, 0.045, 0.055, 0.045, 0.045, 0.035, 0.035, 0.035, 0.035, 0.025, 0.025, 0.025, 0.025, 0.025, 0.025, 0.015, 0.015, 0.015, 0.015, 0.015, 0.015, 0.015, 0.015, 0.010]
      self.equal_weighting = False

   @property
   def interval(self):
      return "1day"

   @property
   def assets(self):
      return self.tickers

   def run(self, data):
      # Check if there are at least two data points in 'ohlcv'
      if len(data['ohlcv']) < 2:
         return None

      today = datetime.strptime(str(next(iter(data['ohlcv'][-1].values()))['date']), '%Y-%m-%d %H:%M:%S')
      yesterday = datetime.strptime(str(next(iter(data['ohlcv'][-2].values()))['date']), '%Y-%m-%d %H:%M:%S')
      
      if today.day == 10 or (today.day > 10 and yesterday.day < 10):
         if self.equal_weighting: 
            allocation_dict = {i: 1/len(self.tickers) for i in self.tickers}
         else:
            allocation_dict = {self.tickers[i]: self.weights[i] for i in range(len(self.tickers))} 
         return TargetAllocation(allocation_dict)
      return None