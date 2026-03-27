import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
import plotly.express as px
import json

st.set_page_config(page_title="AI Trading Terminal", layout="wide")

st.title("🤖 AI Trading Terminal")

# ======================
# TOP SUMMARY (FINBOOM STYLE)
# ======================
col1, col2, col3 = st.columns(3)

col1.metric("💰 Net Worth", "₹2.5L", "+5%")
col2.metric("📊 Assets", "₹3.0L")
col3.metric("💳 Liabilities", "₹50K")

# ======================
# ASSET ALLOCATION
# ======================
st.subheader("📊 Asset Allocation")

alloc = pd.DataFrame({
    "Category": ["Equity", "MF", "Gold"],
    "Value": [50000, 30000, 20000]
})

fig_alloc = px.pie(alloc, names='Category', values='Value')
st.plotly_chart(fig_alloc, use_container_width=True)

# ======================
# GOALS
# ======================
st.subheader("🎯 Goals")

st.progress(0.7, text="Emergency Fund 70%")
st.progress(0.4, text="Retirement 40%")

# ======================
# STOCK LIST
# ======================
stocks = ["RELIANCE.NS", "TCS.NS", "INFY.NS"]

# ======================
# MARKET TREND
# ======================
nifty = yf.download("NIFTY50.NS", period="5d", progress=False)

if not nifty.empty and 'Close' in nifty.columns:
    trend = nifty['Close'].pct_change().dropna()

    if not trend.empty:
        if trend.iloc[-1] > 0:
            st.success("📈 Market Positive")
        else:
            st.error("📉 Market Weak")
else:
    st.warning("Unable to fetch market trend")

# ======================
# LIVE MARKET
# ======================
st.subheader("📊 Live Market")

data = []

for s in stocks:
    try:
        df = yf.download(s, period="1d", interval="1m", progress=False)

        if df.empty or 'Close' not in df.columns:
            continue

        close = pd.to_numeric(df['Close'], errors='coerce').dropna()

        if close.empty:
            continue

        price = float(close.iloc[-1])
        change = float(close.pct_change().iloc[-1] * 100)

        signal = "BUY" if change > 0 else "SELL"

        data.append([s.replace(".NS",""), round(price,2), round(change,2), signal])

    except:
        continue

df_live = pd.DataFrame(data, columns=["Stock","Price","Change %","Signal"])

if not df_live.empty:
    st.dataframe(df_live, use_container_width=True)
else:
    st.warning("No live data available")

# ======================
# SMART CHART (FIXED)
# ======================
st.subheader("📈 Smart Chart")

stock = st.selectbox("Select Stock", stocks)

chart = yf.download(stock, period="5d", interval="15m", progress=False)

if isinstance(chart, pd.DataFrame) and not chart.empty and 'Close' in chart.columns:

    chart = chart.copy()

    chart['Close'] = chart['Close'].astype(float)

    if len(chart) > 20:

        chart['MA20'] = chart['Close'].rolling(20).mean()

        fig = go.Figure()

        fig.add_trace(go.Candlestick(
            x=chart.index,
            open=chart['Open'],
            high=chart['High'],
            low=chart['Low'],
            close=chart['Close']
        ))

        fig.add_trace(go.Scatter(
            x=chart.index,
            y=chart['MA20'],
            line=dict(color='yellow'),
            name="MA20"
        ))

        fig.update_layout(template="plotly_dark")

        st.plotly_chart(fig, use_container_width=True)

    else:
        st.warning("Not enough data")

else:
    st.warning("Chart data unavailable")

# ======================
# FOOTER
# ======================
st.caption("🚀 AI Trading + Wealth Dashboard")
