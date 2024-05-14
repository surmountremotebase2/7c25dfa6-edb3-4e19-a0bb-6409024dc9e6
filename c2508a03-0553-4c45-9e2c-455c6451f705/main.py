from surmount.base_class import Strategy, TargetAllocation
from surmount.technical_indicators import SMA
from surmount.logging import log

class TradingStrategy(Strategy):

   @property
   def assets(self):
      return ["SPY", "QQQ"]

   @property
   def interval(self):
      return "1day"

   def run(self, data):
      holdings = data["holdings"]
      data = data["ohlcv"]
      spy_stake = 0
      qqq_stake = 0

      spy_ma = SMA("SPY", data, 5)
      qqq_ma = SMA("QQQ", data, 5)

      #log(str(data[0]))
      

      if len(data)<5:
         return TargetAllocation({})
    
      if not bool(holdings):
          return TargetAllocation({}) 

      current_price_spy = data[-1]["SPY"]['close']
      current_price_qqq = data[-1]["QQQ"]['close']

      if current_price_spy < spy_ma[-1]:
         #log("going long spy")
         if holdings["SPY"] >= 0:
            spy_stake = min(1, holdings["SPY"]+0.1)
         else:
            spy_stake = 0.4
      elif current_price_spy > spy_ma[-1]:
         #log("selling spy")
         if holdings["SPY"] > 0:
            spy_stake = 0

      if current_price_qqq < qqq_ma[-1]:
         #log("going long qqq")
         if holdings["QQQ"] >= 0:
            qqq_stake = min(1, holdings["QQQ"]+0.1)
         else:
            qqq_stake = 0.4
      elif current_price_qqq > qqq_ma[-1]:
         #log("selling qqq")
         if holdings["QQQ"] > 0:
            qqq_stake = 0

      return TargetAllocation({"SPY": spy_stake, "QQQ": qqq_stake})