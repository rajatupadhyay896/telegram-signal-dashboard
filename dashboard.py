import streamlit as st
import pandas as pd

# ===== PAGE CONFIG =====
st.set_page_config(
    page_title="Telegram Signal Dashboard",
    layout="wide"
)

st.title("📊 Telegram Signal Quality Dashboard")

# ===== LOAD DATA =====
rankings = pd.read_csv("outputs/rankings.csv", index_col=0)
details = pd.read_csv("outputs/detailed_rankings.csv", index_col=0)

# ===== TOP METRICS =====
col1, col2, col3 = st.columns(3)

col1.metric("🏆 Top Group", rankings.index[0])
col2.metric("⭐ Best Score", round(rankings.iloc[0], 3))
col3.metric("📊 Total Groups", len(rankings))

st.markdown("---")

# ===== 🔥 KEY INSIGHT =====
st.warning(
    "⚠️ Insight: High-frequency Telegram trading groups often produce lower-quality signals, "
    "indicating noise rather than structured, risk-managed trades."
)

# ===== CHART =====
st.subheader("📈 Signal Performance Comparison")
st.bar_chart(rankings)

# ===== TABLE =====
st.subheader("📋 Detailed Breakdown")
st.dataframe(details)

# ===== GROUP ANALYSIS =====
st.subheader("🔍 Group Deep Dive")

group = st.selectbox("Select Group", details.index)

if group:
    data = details.loc[group]

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Avg Score", round(data["avg_score"], 2))
    c2.metric("Quality Ratio", round(data["quality_ratio"], 2))
    c3.metric("Signals/Day", round(data["frequency_per_day"], 2))
    c4.metric("Final Score", round(data["final_score"], 3))

st.markdown("---")
st.caption("Built with Python, PostgreSQL, Pandas, and Streamlit")
