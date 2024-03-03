from surmount.base_class import Strategy, TargetAllocation
from surmount.data import PE, Asset
import pandas as pd

class TradingStrategy(Strategy):
    def __init__(self):
        self.tickers = ["F", "AAPL", "TSLA", "GOOG"]
        # PE data for 365 days needs to be collected for each ticker.
        self.data_list = [PE(i, period="365d") for i in self.tickers]

    @property
    def interval(self):
        # This strategy runs on a daily interval.
        return "1day"
    
    @property
    def assets(self):
        return self.tickers

    @property
    def data(self):
        return self.data_list
    
    def run(self, data, state):
        allocation_dict = {}
        for ticker in self.tickers:
            historical_pe = data[PE(ticker, period="365d")]
            mean_historical_pe = pd.Series(historical_pe).mean()

            current_pe = data[PE(ticker)]
            
            # Buy conditions
            if (current_pe < 0.95 * mean_historical_pe) and (ticker not in state["holdings"]):
                allocation_dict[ticker] = 1 / len(self.tickers)  # Equal allocation among all tickers
            
            # Sell conditions
            elif ticker in state["holdings"]:
                position = state["holdings"][ticker]
                current_price = state["prices"][ticker]["close"]
                purchase_price = position["average_price"]

                price_change = (current_price - purchase_price) / purchase_price
                # Sell if position has lost 10%, gained 30%, or PE ratio has rebounded within 2% of the historical average.
                if price_change <= -0.10 or price_change >= 0.30 or (0.98 * mean_historical_pe <= current_pe <= 1.02 * mean_historical_pe):
                    allocation_dict[ticker] = 0  # Sell position
                    
        return TargetAllocation(allocation_dict)