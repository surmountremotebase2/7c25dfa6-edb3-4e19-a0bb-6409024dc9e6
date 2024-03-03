from surmount.base_class import Strategy, TargetAllocation
from surmount.technical_indicators import RSI, MFI
from surmount.logging import log
from surmount.data import OHLCV

class TradingStrategy(Strategy):
    def __init__(self):
        # List of symbols to apply the strategy
        self.tickers = ["TSLA", "MSFT", "GOOG", "F", "MPW"]
        # Data required: OHLCV for RSI and MFI calculation
        self.data_list = [OHLCV(i) for i in self.tickers]

    @property
    def interval(self):
        # Define the interval for the data, daily in this case
        return "1day"

    @property
    def assets(self):
        # Return the list of tickers
        return self.tickers

    @property
    def data(self):
        # Data required for the strategy
        return self.data_list

    def run(self, data):
        # Initialize empty allocation dictionary
        allocation_dict = {}

        for ticker in self.tickers:
            if ticker not in data["ohlcv"]:
                log(f"Data for {ticker} not found.")
                continue

            # Calculate RSI and MFI for the stock
            rsi = RSI(ticker, data["ohlcv"], 14)[-1]  # Assuming 14-day period for RSI
            mfi = MFI(ticker, data["ohlcv"], 14)[-1]  # Assuming 14-day period for MFI

            # Check the conditions for buying or shorting
            if rsi < 30 and mfi < 20:
                allocation_dict[ticker] = 1  # 100% of capital allocated to buy
            elif rsi > 70 and mfi > 80:
                allocation_dict[ticker] = -1  # Short sell (assuming the platform supports it)

            # No explicit sell or cover (short sell buyback) instructions are included here, since
            # those would typically be managed by separate stop-loss/take-profit orders or
            # could be implemented in additional logic within this function based on entry price
            # which would require storing and tracking state (not shown here).

        return TargetAllocation(allocation_dict)