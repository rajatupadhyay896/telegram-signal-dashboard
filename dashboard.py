import streamlit as st
import pandas as pd
import psycopg2
import os

# ===== CONFIG =====
st.set_page_config(layout="wide")
st.title("📊 Telegram Signal Dashboard")

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

# ===== SIDEBAR FILTERS =====
st.sidebar.header("Filters")

groups = st.sidebar.multiselect(
    "Select Groups",
    options=df["group_name"].unique(),
    default=df["group_name"].unique()
)

days = st.sidebar.slider("Last N Days", 1, 30, 7)

# ===== APPLY FILTERS =====
df["timestamp"] = pd.to_datetime(df["timestamp"])

df = df[
    (df["group_name"].isin(groups)) &
    (df["timestamp"] >= pd.Timestamp.now() - pd.Timedelta(days=days))
]

# ===== METRICS =====
col1, col2, col3 = st.columns(3)

col1.metric("Total Signals", len(df))
col2.metric("Unique Groups", df["group_name"].nunique())
col3.metric("Latest Signal", str(df["timestamp"].max())[:19])

# ===== SIGNAL VOLUME =====
st.subheader("📈 Signal Volume by Group")
st.bar_chart(df["group_name"].value_counts())

# ===== SIGNAL QUALITY SCORE =====
df["score"] = (
    df["option_type"].notna().astype(int) * 2 +
    df["strike"].notna().astype(int) * 2 +
    df["has_target"].fillna(False).astype(int) * 2 +
    df["has_sl"].fillna(False).astype(int) * 2 +
    (df["is_buy"].fillna(False) | df["is_sell"].fillna(False)).astype(int)
)

quality = df.groupby("group_name")["score"].mean().sort_values(ascending=False)

st.subheader("⭐ Signal Quality Score")
st.bar_chart(quality)

# ===== PTS (if exists) =====
if "pnl" in df.columns and "result" in df.columns:

    st.subheader("💰 Profit Tracking System")

    pnl_summary = df.groupby("group_name")["pnl"].mean()
    win_rate = df.groupby("group_name")["result"].apply(
        lambda x: (x == "WIN").mean()
    )

    pts_df = pd.DataFrame({
        "Win Rate": win_rate,
        "Avg PnL": pnl_summary
    }).sort_values("Avg PnL", ascending=False)

    st.dataframe(pts_df)
    st.bar_chart(pts_df["Avg PnL"])

# ===== RECENT SIGNALS =====
st.subheader("📋 Recent Signals")
st.dataframe(
    df.sort_values("timestamp", ascending=False).head(100),
    use_container_width=True
)
