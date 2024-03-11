from surmount.base_class import Strategy, TargetAllocation
from surmount.technical_indicators import SMA
from surmount.logging import log

class TradingStrategy(Strategy):
    @property
    def assets(self):
        # Define the assets to be used in the strategy
        return ["SPXL", "SPY"]

    @property
    def interval(self):
        # The data interval desired for the strategy. Daily in this case.
        return "1day"

    def run(self, data):
        # This is the principal method where the strategy logic is defined.
        
        # Calculate the 5-day Simple Moving Average (SMA) for SPXL and SPY
        sma_SPXL = SMA("SPXL", data["ohlcv"], length=5)
        sma_SPY = SMA("SPY", data["ohlcv"], length=5)
        
        # Ensure that we have enough data points to proceed
        if not sma_SPXL or not sma_SPY or len(sma_SPXL) < 5 or len(sma_SPY) < 5:
            #log("Insufficient data for SMA calculation.")
            # Returning a neutral or "do-nothing" allocation if insufficient data
            return TargetAllocation({})
        
        # Check the recent performance difference between SPXL and SPY
        # If SPXL has been underperforming SPY, allocate toward SPXL
        log("sma_SPXL on this datapoint:")
        log(str(sma_SPXL.len()))
        if sma_SPXL[-1] < sma_SPY[-1]:
            #log("SPXL underperforming SPY, buying SPXL.")
            allocation_dict = {"SPXL": 1.0} # Put 100% in SPXL
        else:
            #log("SPXL not underperforming or outperforming SPY, liquidating SPXL.")
            allocation_dict = {"SPXL": 0.0} # Liquidate all SPXL
        
        # Return the target allocation based on our logic
        return TargetAllocation(allocation_dict)