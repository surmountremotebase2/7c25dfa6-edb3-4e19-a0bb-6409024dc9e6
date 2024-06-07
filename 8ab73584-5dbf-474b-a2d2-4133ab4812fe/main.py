from surmount.base_class import Strategy, TargetAllocation, backtest
from surmount.logging import log
from datetime import datetime

class TradingStrategy(Strategy):

   def __init__(self):
      self.tickers = ["NEE", "TSLA", "VWDRY", "ENPH", "DNNGY", "FSLR", "SEDG", "CSIQ", "IBDRY", "XEL", "ECL"]
      self.weights = [0.12, 0.12 , 0.1 , 0.1, 0.1, 0.1, 0.08,0.08, 0.08, 0.06, 0.06]
      self.equal_weighting = False

   @property
   def interval(self):
      return "1day"

   @property
   def assets(self):
      return self.tickers

   def run(self, data):
      today = datetime.now()
      log(str(next(iter(data['ohlcv'][-1].values()))['date']))

      today = datetime.strptime(str(next(iter(data['ohlcv'][-1].values()))['date']), '%Y-%m-%d %H:%M:%S')
      #log(str(data['ohlcv'][-1]))
      if today.day == 7:
         log('Its the 7th, purchasing')
         if self.equal_weighting: 
            allocation_dict = {i: 1/len(self.tickers) for i in self.tickers}
         else:
            allocation_dict = {self.tickers[i]: self.weights[i] for i in range(len(self.tickers))} 
         return TargetAllocation(allocation_dict)
      return None