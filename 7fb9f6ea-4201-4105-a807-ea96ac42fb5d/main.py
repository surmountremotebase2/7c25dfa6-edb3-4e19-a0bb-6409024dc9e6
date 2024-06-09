from surmount.base_class import Strategy, TargetAllocation, backtest
from surmount.logging import log
from datetime import datetime

class TradingStrategy(Strategy):

   def __init__(self):
      self.tickers = [
          "AMZN", "MSFT", "GOOGL", "IBM", "ORCL", "CSCO", "NVDA", "CRM", "EQIX", "DLR",
          "NET", "FSLY", "PSTG", "NTAP", "AKAM", "HPE", "ANET", "JNPR", "FTNT", "FFIV"
      ]
      self.weights = [
          0.10, 0.10, 0.10, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05,
          0.03, 0.03, 0.03, 0.03, 0.03, 0.03, 0.03, 0.03, 0.03, 0.03
      ]
      self.equal_weighting = False
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
              if self.equal_weighting:
                 allocation_dict = {i: 1 / len(self.tickers) for i in self.tickers}
              else:
                 allocation_dict = {self.tickers[i]: self.weights[i] for i in range(len(self.tickers))}
              return TargetAllocation(allocation_dict)
          else:
              return None

      today = datetime.strptime(str(next(iter(data['ohlcv'][-1].values()))['date']), '%Y-%m-%d %H:%M:%S')
      yesterday = datetime.strptime(str(next(iter(data['ohlcv'][-2].values()))['date']), '%Y-%m-%d %H:%M:%S')
      
      if today.day == 13 or (today.day > 13 and yesterday.day < 13):
         if self.equal_weighting:
            allocation_dict = {i: 1 / len(self.tickers) for i in self.tickers}
         else:
            allocation_dict = {self.tickers[i]: self.weights[i] for i in range(len(self.tickers))}
         return TargetAllocation(allocation_dict)
      return None
