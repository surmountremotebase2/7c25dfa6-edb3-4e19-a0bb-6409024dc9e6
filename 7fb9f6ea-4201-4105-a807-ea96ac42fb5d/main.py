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
      today_data, yesterday_data = None, None
      for ticker_data in data['ohlcv']:
         if ticker_data['ticker'] in self.tickers and len(ticker_data['data']) >= 2:
            today_data = ticker_data['data'][-1]
            yesterday_data = ticker_data['data'][-2]
            break

      # If no data found for any tickers, return None
      if not today_data or not yesterday_data:
         log.error("No valid data points found for any tickers.")
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