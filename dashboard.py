import streamlit as st
import pandas as pd
import psycopg2
import os

# ===== CONFIG =====
st.set_page_config(layout="wide")
st.title("📊 Telegram Signal Quality Dashboard")

DB_URL = os.getenv("DB_URL")

# ===== LOAD DATA =====
@st.cache_data(ttl=60)
def load_data():
    conn = psycopg2.connect(DB_URL)
    df = pd.read_sql("SELECT * FROM signals", conn)
    conn.close()
    return df

df = load_data()

if df.empty:
    st.warning("No data available")
    st.stop()

# ===== FILTERS =====
st.sidebar.header("Filters")

groups = st.sidebar.multiselect(
    "Select Groups",
    options=df["group_name"].unique(),
    default=df["group_name"].unique()
)

days = st.sidebar.slider("Last N Days", 1, 30, 7)

df["timestamp"] = pd.to_datetime(df["timestamp"])

df = df[
    (df["group_name"].isin(groups)) &
    (df["timestamp"] >= pd.Timestamp.now() - pd.Timedelta(days=days))
]

# ===== SIGNAL SCORE =====
df["score"] = (
    df["option_type"].notna().astype(int) * 2 +
    df["strike"].notna().astype(int) * 2 +
    df["has_target"].fillna(False).astype(int) * 2 +
    df["has_sl"].fillna(False).astype(int) * 2 +
    (df["is_buy"].fillna(False) | df["is_sell"].fillna(False)).astype(int)
)

# ===== GROUP METRICS =====
grouped = df.groupby("group_name")

summary = pd.DataFrame({
    "avg_score": grouped["score"].mean(),
    "total_signals": grouped.size(),
    "signals_per_day": grouped.size() / days,
    "structured_ratio": grouped["score"].apply(lambda x: (x >= 6).mean())
})

# ===== NORMALIZATION =====
summary["freq_norm"] = summary["signals_per_day"] / summary["signals_per_day"].max()
summary["quality_norm"] = summary["avg_score"] / summary["avg_score"].max()

# ===== FINAL SCORE (SMART) =====
summary["final_score"] = (
    summary["quality_norm"] * 0.5 +
    summary["structured_ratio"] * 0.3 +
    summary["freq_norm"] * 0.2
)

summary = summary.sort_values("final_score", ascending=False)

# ===== TOP METRICS =====
col1, col2, col3 = st.columns(3)

top_group = summary.index[0]
best_score = summary["final_score"].iloc[0]

col1.metric("🏆 Top Group", top_group)
col2.metric("⭐ Best Score", round(best_score, 3))
col3.metric("📊 Total Groups", len(summary))

st.markdown("---")

# ===== FINAL RANKING =====
st.subheader("🏆 Final Ranking")
st.dataframe(summary[["final_score"]])

# ===== VISUALIZATION =====
st.subheader("📊 Ranking Visualization")
st.bar_chart(summary["final_score"])

# ===== DETAILED BREAKDOWN =====
st.subheader("📋 Detailed Breakdown")
st.dataframe(summary)

# ===== GROUP DEEP DIVE =====
st.subheader("🔍 Group Deep Dive")

selected_group = st.selectbox(
    "Select Group",
    options=summary.index
)

group_data = summary.loc[selected_group]

col1, col2, col3, col4 = st.columns(4)

col1.metric("Avg Score", round(group_data["avg_score"], 2))
col2.metric("Structured Ratio", round(group_data["structured_ratio"], 2))
col3.metric("Signals/Day", round(group_data["signals_per_day"], 2))
col4.metric("Final Score", round(group_data["final_score"], 3))

# ===== RECENT SIGNALS =====
st.subheader("📋 Recent Signals")
st.dataframe(
    df.sort_values("timestamp", ascending=False).head(100),
    use_container_width=True
)
