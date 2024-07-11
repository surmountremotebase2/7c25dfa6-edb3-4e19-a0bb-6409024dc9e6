from surmount.base_class import Strategy, TargetAllocation
from surmount.data import InsiderTrading, InstitutionalOwnership

class TradingStrategy(Strategy):
    def __init__(self):
        # Define the ticker symbols for the oil and green energy companies.
        self.oil_companies = ["XOM", "CVX"]  # Example oil companies: Exxon Mobil, Chevron
        self.green_energy_companies = ["TSLA", "NIO"]  # Example green energy companies: Tesla, NIO
        
        # Combine all tickers for data processing
        self.tickers = self.oil_companies + self.green_energy_companies
        
        # Load institutional ownership data as an example of additional data utilization
        self.data_list = [InstitutionalOwnership(ticker) for ticker in self.tickers]
        
    @property
    def interval(self):
        # Choose an appropriate data interval for the strategy
        return "1day"

    @property
    def assets(self):
        # Return the list of assets to be used in this strategy
        return self.tickers

    @property
    def data(self):
        # Return the data needed for trading decisions
        return self.data_list

    def run(self, data):
        # Implement the trading logic
        # Here, we'll allocate our investments equally among all companies
        
        num_assets = len(self.tickers)
        allocation_value = 1 / num_assets
        allocation_dict = {ticker: allocation_value for ticker in self.tickers}
        
        # Example to modify allocation based on custom logic
        # Check institutional ownership as an example, modifying allocation if needed
        # This is a place where any form of analysis can be introduced
        for i in self.data_list:
            dataset_key = ("institutional_ownership", i.symbol)
            if dataset_key in data and data[dataset_key]:
                latest_ownership = data[dataset_key][-1] # Get the most recent data point available
                # Example condition to adjust allocation based on some criteria, it's simplified
                if latest_ownership['ownershipPercent'] < 50: 
                    allocation_dict[i.symbol] *= 0.9  # Reduce allocation if ownership is low
        
        return TargetAllocation(allocation_dict)