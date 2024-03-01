from surmount.base_class import Strategy, TargetAllocation
from surmount.logging import log
from surmount.data import Asset, InsiderTrading, SocialSentiment

class TradingStrategy(Strategy):
    def __init__(self):
        # Defining the list of tickers to monitor
        self.tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "FB"]
        # Adding insider trading data sources for the tickers
        self.data_list = [InsiderTrading(i) for i in self.tickers]
        # Adding market sentiment analysis data sources for the tickers
        self.data_list += [SocialSentiment(i) for i in self.tickers]

    @property
    def interval(self):
        # Specifies the data interval, which could be adjusted depending on the strategy requirement
        return "1day"

    @property
    def assets(self):
        # Returns the list of tickers that this strategy is interested in
        return self.tickers

    @property
    def data(self):
        # Returns the data sources (insider trading and market sentiment) needed for this strategy
        return self.data_list

    def run(self, data):
        # Initialize an empty allocation dictionary
        allocation_dict = {}
        # Loop through each ticker to check both insider trading activity and market sentiment
        for ticker in self.tickers:
            insider_data_key = ('insider_trading', ticker)
            sentiment_data_key = ('market_sentiment', ticker)
            # Check if there's insider buying and positive sentiment
            if insider_data_key in data and sentiment_data_key in data:
                if data[insider_data_key] and 'Buy' in data[insider_data_key][-1]['transactionType']:
                    if data[sentiment_data_key] and data[sentiment_data_key][-1]['sentiment'] > 0:
                        # If both conditions are true, assign an equal stake in this asset
                        allocation_dict[ticker] = 1/len(self.tickers)

        # If no asset meets the criteria, this keeps the portfolio in cash (not invested)
        if not allocation_dict:
            return TargetAllocation({})
        # Allocate funds to the assets that meet both conditions
        return TargetAllocation(allocation_dict)