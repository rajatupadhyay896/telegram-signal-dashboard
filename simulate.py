import pandas as pd

signals = pd.read_csv("signals_only.csv")
nifty = pd.read_csv("nifty_data.csv")

# FIX SIGNAL TIME
signals["timestamp"] = pd.to_datetime(signals["timestamp"])

# FORCE NIFTY TIME FIX
nifty = nifty.reset_index()
nifty.rename(columns={nifty.columns[0]: "Datetime"}, inplace=True)
nifty["Datetime"] = pd.to_datetime(nifty["Datetime"])

# 🔥 FORCE SAME TIMEZONE (critical)
signals["timestamp"] = signals["timestamp"].dt.tz_localize(None)
nifty["Datetime"] = nifty["Datetime"].dt.tz_localize(None)

results = []

for _, row in signals.iterrows():
    if pd.isna(row.get("option_type")):
        continue

    signal_time = row["timestamp"]

    # find closest candle
    closest = nifty.iloc[(nifty["Datetime"] - signal_time).abs().argsort()[:1]]

    if closest.empty:
        continue

    idx = closest.index[0]

    if idx + 3 >= len(nifty):
        continue

    entry = nifty.iloc[idx]["Close"]
    future_prices = nifty.iloc[idx+1:idx+4]["Close"]

    max_price = future_prices.max()
    min_price = future_prices.min()

    if row["option_type"] == "CE":
        outcome = "WIN" if max_price > entry else "LOSS"
    elif row["option_type"] == "PE":
        outcome = "WIN" if min_price < entry else "LOSS"
    else:
        continue

    results.append({
        "group": row["group_name"],
        "result": outcome
    })

df = pd.DataFrame(results)

print("\n===== RESULTS =====\n")

if df.empty:
    print("Still no matches — likely data mismatch or no valid signals")
else:
    print(df.groupby("group")["result"].value_counts())
