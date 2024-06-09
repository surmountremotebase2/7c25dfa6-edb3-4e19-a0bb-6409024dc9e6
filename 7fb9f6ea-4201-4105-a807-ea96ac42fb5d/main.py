from surmount.base_class import Strategy, TargetAllocation, backtest
from surmount.logging import log
from datetime import datetime

class TradingStrategy(Strategy):

   def __init__(self):
      self.tickers = ["IBM", "GOOGL", "MSFT", "INTC", "HON", "NVDA", "RGTI", "BABA", "DELL", "ANET", "SMCI", "WDC"]
      self.weights = [0.1, 0.10, 0.10, 0.05, 0.05, 0.10, .05, .10, .10, .05, .10, .05]
      self.equal_weighting = False
      self.counter = 0

   @property
   def interval(self):
      return "1day"

   @property
   def assets(self):
      return self.tickers

   def run(self, data):
      # Ensure there is at least one data point
      if len(data['ohlcv']) < 1:
         self.counter += 1
         if self.counter >= 30:
            self.counter = 0
            if self.equal_weighting: 
               allocation_dict = {I: 1/len(self.tickers) for I in self.tickers}
            else:
               allocation_dict = {self.tickers[I]: self.weights[I] for I in range(len(self.tickers))} 
            return TargetAllocation(allocation_dict)
         else:
             return None

      # Iterate over tickers to find one with data
      print(str(data['ohlcv'][-1]))
      today_data, yesterday_data = None, None
      for ticker_data in data['ohlcv'][-2]:
         if data['ohlcv'][-2][ticker_data]['date']:
            today_data = data['ohlcv'][-1][ticker_data]['date']
            yesterday_data = data['ohlcv'][-2][ticker_data]['date']
            break

      # If no data found for any tickers, return None
      if not today_data or not yesterday_data:
         return None

      # Parse dates
      today = datetime.strptime(today_data['date'], '%Y-%m-%d %H:%M:%S')
      yesterday = datetime.strptime(yesterday_data['date'], '%Y-%m-%d %H:%M:%S')
      
      if today.day == 17 or (today.day > 17 and yesterday.day < 17):
         if self.equal_weighting: 
            allocation_dict = {I: 1/len(self.tickers) for I in self.tickers}
         else:
            allocation_dict = {self.tickers[I]: self.weights[I] for I in range(len(self.tickers))}
         return TargetAllocation(allocation_dict)
      
      return None