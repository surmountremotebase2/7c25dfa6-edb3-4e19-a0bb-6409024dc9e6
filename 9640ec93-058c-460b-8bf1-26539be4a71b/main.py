from surmount.base_class import Strategy, TargetAllocation
from surmount.technical_indicators import RSI, MACD
from surmount.logging import log

class TradingStrategy(Strategy):
    
    def __init__(self):
        self.ticker = "SPY"
        
    @property
    def assets(self):
        return [self.ticker]

    @property
    def interval(self):
        # Choosing '1day' interval for daily RSI and MACD calculation
        return "1day"

    def run(self, data):
        # Initialize SPY stake to 0
        spy_stake = 0
        
        # Retrieve SPY RSI and MACD
        spy_rsi = RSI(self.ticker, data["ohlcv"], length=14) # RSI calculated over 14 days
        spy_macd = MACD(self.ticker, data["ohlcv"], fast=12, slow=26) # MACD with standard settings
        
        if spy_rsi and spy_macd: # Ensure we have data to work with
            # Check for the last RSI and MACD signal
            last_rsi = spy_rsi[-1]
            macd_line = spy_macd["MACD"][-1]
            signal_line = spy_macd["signal"][-1]
            
            # Buying condition: RSI below 30 (oversold) and MACD crosses above signal
            if last_rsi < 30 and macd_line > signal_line:
                spy_stake = 1  # Full allocation to SPY

            # Selling condition: RSI above 70 (overbought)
            elif last_rsi > 70:
                spy_stake = 0  # No allocation to SPY

        # Log the decision
        log(f"SPY allocation: {spy_stake}")
        
        return TargetAllocation({self.ticker: spy_stake})