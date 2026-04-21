import streamlit as st
import pandas as pd

# ===== PAGE CONFIG =====
st.set_page_config(
    page_title="Telegram Signal Dashboard",
    layout="wide"
)

st.title("📊 Telegram Signal Quality Dashboard")

# ===== CORE INSIGHT =====
st.markdown("""
### 📌 Core Finding

Most Telegram trading groups generate **high-frequency but low-quality signals**,  
making them unreliable for systematic trading.

This dashboard quantifies that gap using structured scoring.
""")

# ===== TIME FILTER (UI ONLY FOR NOW) =====
days = st.selectbox("📅 Select Time Window (UI Placeholder)", [7, 14, 30])

# ===== LOAD DATA =====
rankings = pd.read_csv("outputs/rankings.csv", index_col=0)
details = pd.read_csv("outputs/detailed_rankings.csv", index_col=0)

# ===== METRICS =====
col1, col2, col3, col4 = st.columns(4)

col1.metric("🏆 Top Group", rankings.index[0])
col2.metric("⭐ Best Score", round(rankings.iloc[0], 3))
col3.metric("📊 Total Groups", len(rankings))
col4.metric("⚠️ Lowest Quality Group", rankings.index[-1])

st.markdown("---")

# ===== INSIGHT BANNER =====
st.warning(
    "⚠️ High-frequency Telegram trading groups often produce lower-quality signals, "
    "indicating noise rather than structured, risk-managed trades."
)

# ===== MODEL EXPLANATION =====
st.info("""
🧠 Scoring Model:
- Direction (CE/PE): +2  
- Strike clarity: +2  
- Target: +2  
- Stop-loss: +3 (highest weight)  
- Buy/Sell clarity: +1  

Final score combines:
• Signal quality  
• Consistency  
• Frequency  
""")

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
