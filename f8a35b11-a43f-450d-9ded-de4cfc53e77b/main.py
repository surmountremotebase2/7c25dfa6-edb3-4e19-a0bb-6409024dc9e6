from surmount.base_class import Strategy, TargetAllocation
from surmount.technical_indicators import RSI
from surmount.data import InsiderTrading
from surmount.logging import log

class TradingStrategy(Strategy):
    def __init__(self):
        self.ticker = "AAPL"
        self.insider_activity = InsiderTrading(self.ticker)

    @property
    def assets(self):
        return [self.ticker]

    @property
    def interval(self):
        return "1day"

    @property
    def data(self):
        return [self.insider_activity]

    def rsi_sentiment(self, data):
        """Using RSI as a proxy for market sentiment.
        High RSI (above 60) indicates strong sentiment.
        Low RSI (below 40) indicates weak sentiment."""
        rsi_values = RSI(self.ticker, data["ohlcv"], length=14)
        if not rsi_values:  # Checking if RSI values are not empty
            return None
        latest_rsi = rsi_values[-1]
        if latest_rsi > 60:
            return "high"
        elif latest_rsi < 40:
            return "low"
        else:
            return "neutral"

    def insider_activity_analysis(self, data):
        """Analyzes the latest insider trading activity."""
        activities = data[(self.insider_activity, self.ticker)]
        if not activities:
            return None
        latest_activity = activities[-1]
        if latest_activity['transactionType'].lower() == "buy":
            return "buying"
        elif latest_activity['transactionType'].lower() == "sell":
            return "selling"
        else:
            return None

    def run(self, data):
        sentiment = self.rsi_sentiment(data)
        insider_action = self.insider_activity_analysis(data)

        allocation = 0
        if sentiment == "high" and insider_action == "buying":
            allocation = 1  # Full investment
        elif sentiment == "high" and insider_action == "selling":
            allocation = 0.5  # Reduce investment due to insider selling
        elif sentiment == "low":
            allocation = 0  # Exit investment due to low sentiment
        else:
            allocation = 0.25  # Maintain a conservative position
        
        log(f"Sentiment: {sentiment}, Insider Action: {insider_action}, Allocation: {allocation}")
        return TargetAllocation({self.ticker: allocation})