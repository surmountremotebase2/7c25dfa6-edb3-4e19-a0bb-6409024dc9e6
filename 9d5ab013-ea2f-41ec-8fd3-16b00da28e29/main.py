from surmount.base_class import Strategy, TargetAllocation
from surmount.data import Asset, InsiderTrading, Ratios
from surmount.logging import log

class TradingStrategy(Strategy):

    def __init__(self):
        # Get S&P 500 tickers. Replace 'SP500_tickers' with actual list or method to fetch S&P 500 tickers
        self.tickers = ["AAPL", "SPY", "GOOG", "F", "MPW"]  
        self.data_list = [Ratios(i)['priceFairValue'] for i in self.tickers] + [InsiderTrading(i) for i in self.tickers]

    @property
    def interval(self):
        return "1day"

    @property
    def assets(self):
        return self.tickers

    @property
    def data(self):
        return self.data_list

    def run(self, data):
        allocation_dict = {}
        for ticker in self.tickers:
            current_price = data["ohlcv"][-1][ticker]["close"]
            fair_value_data = data[Ratios(ticker)['priceFairValue']]
            insider_trading_data = data[InsiderTrading(ticker)]

            # Check if fair value and insider trading data are available
            if fair_value_data and insider_trading_data:
                price_fair_value = fair_value_data["priceFairValue"]
                insider_buying = any(trade['transactionType'] == 'Buy' for trade in insider_trading_data)

                # If the current price is at least 20% greater than the priceFairValue
                if current_price > price_fair_value * 1.20:
                    # If insider investors are buying, allocate 20% of portfolio, else 10%
                    allocation_percentage = 0.20 if insider_buying else 0.10
                    allocation_dict[ticker] = allocation_percentage
                elif current_price <= price_fair_value * 1.20:
                    # Close the position if the price is within 20% of the fair value
                    allocation_dict[ticker] = 0
            else:
                # Log if there's missing data for fair value or insider trading
                log(f"Missing data for {ticker}")

        # Normalize allocations if necessary, ensuring total allocation doesn't exceed 1
        total_allocation = sum(allocation_dict.values())
        if total_allocation > 1:
            allocation_dict = {k: v / total_capacity for k, v in allocation_dict.items()}

        return TargetAllocation(allocation_dict)