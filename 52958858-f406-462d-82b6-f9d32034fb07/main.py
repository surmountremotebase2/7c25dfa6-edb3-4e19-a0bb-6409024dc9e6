from surmount.base_class import Strategy, TargetAllocation
from surmount.data import Asset
from sklearn.linear_model import LinearRegression
import numpy as np

class TradingStrategy(Strategy):
    def __init__(self):
        # Define the tickers we are interested in
        self.tickers = ["SPY", "SPXL"]
        
        # Initialize a linear regression model for our AI component
        # This is a simple placeholder for more complex AI analyses
        self.model = LinearRegression()
        
        # Store a history of price ratios to train our model
        self.price_ratios = []
        
        # Define a window for our moving average, which will help us determine divergence
        self.window = 5

    @property
    def interval(self):
        # We are looking at daily data to analyze the relationship
        return "1day"

    @property
    def assets(self):
        # We only trade in SPXL based on our analysis
        return ["SPXL"]

    @property
    def data(self):
        # We are only interested in receiving price data for SPY and SPXL
        return [Asset(i) for i in self.tickers]

    def run(self, data):
        # Fetch close prices for SPY and SPXL
        spy_close = [i["SPY"]["close"] for i in data["ohlcv"]]
        spxl_close = [i["SPXL"]["close"] for i in data["ohlcv"]]
        
        # Ensure we have enough data to proceed
        if len(spy_close) < self.window + 1:  
            return TargetAllocation({})
        
        # Calculate the ratio of SPXL to SPY prices
        current_ratio = spxl_close[-1] / spy_close[-1]
        self.price_ratios.append(current_ratio)
        
        # If we don't have enough ratios to form our moving average, do not trade
        if len(self.price_ratios) < self.window + 1:
            return TargetAllocation({})
        
        # Calculate the moving average of the price ratio
        moving_avg = np.mean(self.price_ratios[-self.window:])
        
        # Train our AI model to predict the next ratio
        X = np.arange(len(self.price_ratios)).reshape(-1, 1)
        y = np.array(self.price_ratios)
        self.model.fit(X, y)
        
        # Predict the next ratio
        predicted_ratio = self.model.predict([[len(self.price_ratios)]])[0]
        
        # Determining allocation based on the predicted divergence
        # If the predicted ratio significantly deviates from the moving average, we see this as a divergence
        if predicted_ratio > moving_avg * 1.01:
            # If the predicted ratio is higher, we expect SPXL to outperform SPY, and thus we buy SPXL
            allocation_dict = {"SPXL": 1.0}
        elif predicted_ratio < moving_avg * 0.99:
            # If the predicted ratio is lower, we expect SPXL to underperform SPY, and we sell SPXL to avoid losses
            allocation_dict = {"SPXL": 0.0}
        else:
            # No significant divergence, maintain current holdings
            allocation_dict = {}
        
        return TargetAllocation(allocation_dict)