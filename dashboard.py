import psycopg2
import pandas as pd
import os
from datetime import timedelta

DB_URL = os.getenv("DB_URL")

conn = psycopg2.connect(DB_URL)

# ===== LOAD SIGNALS =====
df = pd.read_sql("""
SELECT id, timestamp, option_type
FROM signals
WHERE result IS NULL
""", conn)

if df.empty:
    print("No new signals")
    exit()

# ===== GET PRICE DATA =====
data = yf.download("^NSEI", period="5d", interval="5m")
data.reset_index(inplace=True)

# normalize datetime
if "Datetime" not in data.columns:
    data.rename(columns={"Date": "Datetime"}, inplace=True)

data["Datetime"] = pd.to_datetime(data["Datetime"])

# 🔥 FIX: remove timezone for comparison
data["Datetime"] = data["Datetime"].dt.tz_localize(None)

# ===== FUNCTION =====
def evaluate(row):
    try:
        signal_time = pd.to_datetime(row["timestamp"])

        signal_date = signal_time.date()

        entry_candidates = data[data["Datetime"].dt.date >= signal_date]

        if entry_candidates.empty:
            return "UNKNOWN", 0

        entry_row = entry_candidates.iloc[0]

        exit_candidates = data[data["Datetime"].dt.date > entry_row["Datetime"].date()]

        if exit_candidates.empty:
            return "UNKNOWN", 0

        exit_row = exit_candidates.iloc[0]

        entry = entry_row["Close"]
        exit_price = exit_row["Close"]

        change = float((exit_price - entry) / entry)

        if row["option_type"] == "PE":
            change = -change

        if change > 0.003:
            return "WIN", change
        elif change < -0.003:
            return "LOSS", change
        else:
            return "NEUTRAL", change

    except Exception:
        return "UNKNOWN", 0

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
    """, (row["result"], row["pnl"], row["id"]))

conn.commit()
cursor.close()
conn.close()

print("PTS updated (fixed)")
