from surmount.base_class import Strategy, TargetAllocation
from surmount.technical_indicators import SMA  # We'll use the Simple Moving Average (SMA)
from surmount.logging import log
from surmount.data import Asset

class TradingStrategy(Strategy):
    @property
    def assets(self):
        return ["VIX", "SPXL", "SPXY"]

    @property
    def interval(self):
        return "1day"

    @property
    def data(self):
        # Assuming data required is the 5-day SMA for VIX and current prices for SPXL and SPXS
        return [Asset("VIX"), Asset("SPXL"), Asset("SPXS")]

    def run(self, data):
        # Calculating the 5-day SMA for VIX
        vix_sma_5_day = SMA("VIX", data["ohlcv"], 5)
        
        allocation_dict = {"SPXL": 0, "SPXS": 0}  # Initially, no allocation

        if vix_sma_5_day is not None and len(vix_sma_5_day) > 0:
            avg_vix_price = vix_sma_5_day[-1]  # Getting the latest SMA value

            if avg_vix_price < 25:
                log("VIX average is below 25, going bullish with SPXL")
                allocation_dict["SPXL"] = 1.0  # Allocating 100% to SPXL
            elif avg_vix_price > 25:
                log("VIX average is above 25, going bearish with SPXS")
                allocation_dict["SPXS"] = 1.0  # Allocating 100% to SPXS
            else:
                log("VIX average is exactly 25, holding positions")
                # In this case, decide what should be done when VIX is exactly 25. This implementation holds.
        else:
            log("No valid SMA data for VIX; holding positions")

        return TargetAllocation(allocation_dict)