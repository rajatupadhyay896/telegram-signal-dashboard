import yfinance as yf
import pandas as pd

# Fetch NIFTY data
nifty = yf.download("^NSEI", period="1mo", interval="5m")

# Fetch BANKNIFTY data
banknifty = yf.download("^NSEBANK", period="7d", interval="5m")

# Save
nifty.to_csv("nifty_data.csv")
banknifty.to_csv("banknifty_data.csv")

print("Price data downloaded")
