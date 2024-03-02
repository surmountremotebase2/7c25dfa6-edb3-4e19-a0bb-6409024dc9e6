from surmount.base_class import Strategy, TargetAllocation
from surmount.logging import log
import pandas as pd

class TradingStrategy(Strategy):
    def __init__(self):
        # Define the ticker of interest
        self.ticker = "SPY"
        
    @property
    def interval(self):
        # Set the data interval to daily since we are working with daily volume
        return "1day"

    @property
    def assets(self):
        # The asset this strategy is interested in is SPY
        return [self.ticker]

    @property
    def data(self):
        # No additional data sources required beyond the default OHLCV data
        return []

    def run(self, data):
        # Extract volume data for the ticker
        volumes = [i[self.ticker]["volume"] for i in data["ohlcv"]]
        
        # Check if we have enough data to compute an average over the previous 180 days
        if len(volumes) > 180:
            # Calculate the 180-day average volume
            avg_volume_180d = pd.Series(volumes[-181:-1]).mean()  # Exclude the current day
            
            # Determine if the current day's volume exceeds 120% of the 180-day average
            if volumes[-1] > avg_volume_180d * 1.2:
                log(f"Current day's volume for {self.ticker} is above 120% of the 180-day average.")
                # If so, set the allocation for SPY to 1 (100%)
                return TargetAllocation({self.ticker: 1})
                
        # If condition not met or there's insufficient historical data, do not allocate to SPY
        return TargetAllocation({self.ticker: 0})