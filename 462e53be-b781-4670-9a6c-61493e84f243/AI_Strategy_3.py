from surmount.base_class import Strategy, TargetAllocation
from surmount.data import OHLCV
from surmount.logging import log

class TradingStrategy(Strategy):
    def __init__(self):
        # Define the tickers you want to monitor
        self.tickers = ["MPW", "F", "AAPL"]
        # Data needed: OHLCV for calculating daily percentage change
        self.data_list = [OHLCV(ticker) for ticker in self.tickers]

    @property
    def interval(self):
        # Daily data is sufficient for this strategy
        return "1day"

    @property
    def assets(self):
        # Return the list of tickers the strategy monitors
        return self.tickers

    @property
    def data(self):
        # Return the list of data sources (OHLCV) required for the strategy
        return self.data_list

    def run(self, data):
        # Initialize allocation dictionary, default to 0 (no position)
        allocation_dict = {ticker: 0 for ticker in self.tickers}
        
        # Check for each stock if it falls by at least 1.5% in a single day
        for ticker in self.tickers:
            ohlcv_data = data[OHLCV(ticker)]
            
            # Ensure there are at least two days of data to compare
            if len(ohlcv_data) >= 2:
                # Calculate the percentage change from the previous close to today's close
                percentage_change = ((ohlcv_data[-1]["close"] - ohlcv_data[-2]["close"]) / ohlcv_data[-2]["close"]) * 100
                
                # If the stock fell by at least 1.5%, set to buy 10 call options
                if percentage_change <= -1.5:
                    # Here 10 call options is abstracted; in an actual trading system, 
                    # this would involve specifying option contracts to buy
                    allocation_dict[ticker] = 10
                    log(f"Buying 10 call options for {ticker} due to a {percentage_change}% drop.")
        
        return TargetAllocation(allocation_dict)