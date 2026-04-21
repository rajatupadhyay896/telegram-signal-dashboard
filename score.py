import pandas as pd
import psycopg2
import os

# ===== CONNECT TO DB =====
conn = psycopg2.connect(
    dbname="telegram_trading",
    user="user",
    password="",
    host="localhost",
    port="5432"
)

# ===== LOAD DATA =====
query = "SELECT * FROM signals;"
df = pd.read_sql(query, conn)

# ===== CLEAN TIME =====
df["timestamp"] = pd.to_datetime(df["timestamp"])
df = df[df["timestamp"] > pd.Timestamp.now() - pd.Timedelta(days=7)]

# ===== SCORING FUNCTION (STRUCTURED, NO REGEX) =====
def score_signal(row):
    score = 0

    # Direction (CE/PE)
    if row["option_type"] in ["CE", "PE"]:
        score += 2

    # Strike
    if pd.notna(row["strike"]):
        score += 2

    # Target
    if row.get("has_target"):
        score += 2

    # Stop-loss (MOST IMPORTANT)
    if row.get("has_sl"):
        score += 3

    # Buy/Sell clarity
    if row.get("is_buy") or row.get("is_sell"):
        score += 1

    return score

# APPLY SCORE
df["score"] = df.apply(score_signal, axis=1)

# ===== QUALITY METRIC =====
df["is_good"] = df["score"] >= 7

avg_score = df.groupby("group_name")["score"].mean()
quality_ratio = df.groupby("group_name")["is_good"].mean()

# ===== FREQUENCY (signals/day) =====
frequency = df.groupby("group_name").size()
frequency = frequency / 7

# normalize
normalized_score = avg_score / 10
frequency_norm = frequency / frequency.max()

# ===== FINAL SCORE =====
final_score = (
    (0.6 * quality_ratio) +
    (0.3 * normalized_score) +
    (0.1 * frequency_norm)
)

final_score = final_score.sort_values(ascending=False)

# ===== SAVE OUTPUT =====
os.makedirs("outputs", exist_ok=True)

final_score.to_csv("outputs/rankings.csv")

summary = pd.DataFrame({
    "avg_score": avg_score,
    "quality_ratio": quality_ratio,
    "frequency_per_day": frequency,
    "final_score": final_score
})

summary = summary.sort_values("final_score", ascending=False)
summary.to_csv("outputs/detailed_rankings.csv")

# ===== PRINT =====
print("\n===== FINAL RANKING =====\n")
print(final_score)

print("\n===== DETAILED BREAKDOWN =====\n")
print(summary)
