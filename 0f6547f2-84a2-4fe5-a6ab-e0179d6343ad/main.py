from surmount.base_class import Strategy, TargetAllocation
from surmount.data import OHLCV
from surmount.logging import log
import pandas as pd

class TradingStrategy(Strategy):
    def __init__(self):
        # Define the tickers involved in the strategy
        self.tickers = ["SPY", "SPXL"]

    @property
    def assets(self):
        # The assets that this strategy will trade
        return self.tickers

    @property
    def interval(self):
        # Use hourly data for the analysis
        return "1hour"

    def run(self, data):
        """
        SPY SPXL Arb logic:
        - Buy $SPXL when it underperforms $SPY based on hourly closing prices.
        """
        # Check if we have enough data points (at least 2 hours of data)
        if len(data["ohlcv"]) < 2:
            return TargetAllocation({})
        
        # Gather the closing prices for SPY and SPXL
        spy_close_prices = [d["SPY"]["close"] for d in data["ohlcv"]]
        spxl_close_prices = [d["SPXL"]["close"] for d in data["ohlcv"]]
        
        # Convert lists to pandas Series for easier manipulation
        spy_series = pd.Series(spy_close_prices)
        spxl_series = pd.Series(spxl_close_prices)
        
        # Calculate the percentage change of the closing prices for both SPY and SPXL
        spy_pct_change = spy_series.pct_change().iloc[-1] # Percent change for the last available data
        spxl_pct_change = spxl_series.pct_change().iloc[-1] # Percent change for the last available data
        
        # Initialize the stake for SPXL as 0 (assume no position)
        spxl_stake = 0
        
        # Trading logic:
        # If $SPXL underperforms $SPY (in terms of percentage change), we consider buying $SPXL
        # This example assumes a simple logic of setting the allocation to 1 (100% of the portfolio)
        # in case the condition is met. Adjust the strategy, risk management, and allocation
        # parameters as needed for actual trading.
        if spxl_pct_change < spy_pct_change:
            log("Buying SPXL as it underperformed SPY in the last hour.")
            spxl_stake = 1  # This means we allocate all in on SPXL under the strategy's logic

        # Return the target allocation with the calculated stake for SPXL
        return TargetAllocation({"SPXL": spxl_stake})