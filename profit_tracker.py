import psycopg2
import pandas as pd
import yfinance as yf
import os
from datetime import timedelta

# ===== DB =====
DB_URL = os.getenv("DB_URL")
if not DB_URL:
    raise Exception("DB_URL not set")

conn = psycopg2.connect(DB_URL)

# ===== LOAD SIGNALS (only unevaluated) =====
df = pd.read_sql("""
SELECT id, timestamp, option_type
FROM signals
WHERE result IS NULL
""", conn)

if df.empty:
    print("No new signals to evaluate")
    conn.close()
    exit()

# ===== FETCH MARKET DATA (NIFTY proxy) =====
data = yf.download("^NSEI", period="5d", interval="5m")
data.reset_index(inplace=True)

# Normalize column name
if "Datetime" not in data.columns:
    if "Date" in data.columns:
        data.rename(columns={"Date": "Datetime"}, inplace=True)

data["Datetime"] = pd.to_datetime(data["Datetime"])

# ===== EVALUATION FUNCTION =====
def evaluate(row):
    t = pd.to_datetime(row["timestamp"])
    future_t = t + timedelta(minutes=30)

    try:
        entry_row = data[data["Datetime"] >= t].iloc[0]
        exit_row = data[data["Datetime"] >= future_t].iloc[0]
    except Exception:
        return "UNKNOWN", 0.0

    entry = entry_row["Close"]
    exit_price = exit_row["Close"]

    change = (exit_price - entry) / entry

    # If PE, inverse logic
    if row["option_type"] == "PE":
        change = -change

    # Thresholds
    if change > 0.005:
        return "WIN", float(change)
    elif change < -0.005:
        return "LOSS", float(change)
    else:
        return "NEUTRAL", float(change)

# ===== APPLY =====
results = df.apply(evaluate, axis=1)
df["result"] = results.apply(lambda x: x[0])
df["pnl"] = results.apply(lambda x: x[1])

# ===== UPDATE DB =====
cursor = conn.cursor()

for _, row in df.iterrows():
    cursor.execute("""
        UPDATE signals
        SET result = %s, pnl = %s
        WHERE id = %s
    """, (row["result"], row["pnl"], int(row["id"])))

conn.commit()
cursor.close()
conn.close()

print("PTS updated")