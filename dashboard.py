import streamlit as st
import pandas as pd
import psycopg2
import os

# ===== PAGE CONFIG =====
st.set_page_config(page_title="Telegram Signal Dashboard", layout="wide")

st.title("📊 Telegram Signal Quality Dashboard")

# ===== CORE INSIGHT =====
st.markdown("""
### 📌 Core Finding

Most Telegram trading groups generate **high-frequency but low-quality signals**,  
making them unreliable for systematic trading.

This dashboard evaluates signals using live database data.
""")

# ===== TIME FILTER =====
days = st.selectbox("📅 Select Time Window", [7, 14, 30])

# ===== DB CONNECTION =====
@st.cache_resource
def get_connection():
    db_url = os.getenv("DB_URL")
    if not db_url:
        st.error("Database URL not set")
        st.stop()
    return psycopg2.connect(db_url)

conn = get_connection()

# ===== LOAD DATA FROM DB =====
@st.cache_data(ttl=300)
def load_data(days):
    query = f"""
        SELECT *
        FROM signals
        WHERE timestamp >= NOW() - INTERVAL '{days} days'
    """
    return pd.read_sql(query, conn)

df = load_data(days)

# ===== CHECK =====
if df.empty:
    st.warning("No data found in selected time window")
    st.stop()

# ===== SCORING FUNCTION =====
def score_signal(row):
    score = 0

    if row["option_type"] in ["CE", "PE"]:
        score += 2

    if pd.notna(row["strike"]):
        score += 2

    if row.get("has_target"):
        score += 2

    if row.get("has_sl"):
        score += 3

    if row.get("is_buy") or row.get("is_sell"):
        score += 1

    return score

# APPLY SCORING
df["score"] = df.apply(score_signal, axis=1)
df["is_good"] = df["score"] >= 7

# ===== GROUP METRICS =====
avg_score = df.groupby("group_name")["score"].mean()
quality_ratio = df.groupby("group_name")["is_good"].mean()
frequency = df.groupby("group_name").size() / days

# NORMALIZE
normalized_score = avg_score / 10
frequency_norm = frequency / frequency.max()

# FINAL SCORE
final_score = (
    (0.6 * quality_ratio) +
    (0.3 * normalized_score) +
    (0.1 * frequency_norm)
).sort_values(ascending=False)

# SUMMARY TABLE
summary = pd.DataFrame({
    "avg_score": avg_score,
    "quality_ratio": quality_ratio,
    "frequency_per_day": frequency,
    "final_score": final_score
}).sort_values("final_score", ascending=False)

# ===== METRICS =====
col1, col2, col3, col4 = st.columns(4)

col1.metric("🏆 Top Group", final_score.index[0])
col2.metric("⭐ Best Score", round(final_score.iloc[0], 3))
col3.metric("📊 Total Groups", len(final_score))
col4.metric("⚠️ Lowest Quality Group", final_score.index[-1])

st.markdown("---")

# ===== INSIGHT =====
st.warning(
    "⚠️ High-frequency groups often produce lower-quality signals, "
    "indicating noise rather than structured trading setups."
)

# ===== MODEL =====
st.info("""
🧠 Scoring Model:
- Direction: +2  
- Strike: +2  
- Target: +2  
- Stop-loss: +3  
- Buy/Sell: +1  

Final score = quality + consistency + frequency
""")

# ===== CHART =====
st.subheader("📈 Signal Performance Comparison")
st.bar_chart(final_score)

# ===== TABLE =====
st.subheader("📋 Detailed Breakdown")
st.dataframe(summary)

# ===== GROUP DEEP DIVE =====
st.subheader("🔍 Group Deep Dive")

group = st.selectbox("Select Group", summary.index)

if group:
    data = summary.loc[group]

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Avg Score", round(data["avg_score"], 2))
    c2.metric("Quality Ratio", round(data["quality_ratio"], 2))
    c3.metric("Signals/Day", round(data["frequency_per_day"], 2))
    c4.metric("Final Score", round(data["final_score"], 3))

st.markdown("---")
st.caption("Live DB | Python | PostgreSQL | Streamlit")
