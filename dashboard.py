import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
from sklearn.linear_model import LinearRegression

st.set_page_config(page_title="AI Trading Terminal", layout="wide")

# ======================
# PREMIUM STYLE
# ======================
st.markdown("""
<style>
.block-container { padding-top: 2rem; }
[data-testid="stMetric"] {
    background-color: #111827;
    padding: 15px;
    border-radius: 12px;
}
</style>
""", unsafe_allow_html=True)

st.title("🤖 AI Trading + Wealth Dashboard")

# ======================
# STOCK LIST
# ======================
stocks = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS"]

stock = st.selectbox("📌 Select Stock", stocks)

# ======================
# LOAD DATA (STABLE FIX)
# ======================
df = yf.download(stock, period="1mo", interval="5m", progress=False, threads=False)

if df is None or df.empty:
    st.error("❌ Data not available")
    st.stop()

# FIX MULTI INDEX
if isinstance(df.columns, pd.MultiIndex):
    df.columns = df.columns.get_level_values(0)

if 'Close' not in df.columns:
    st.error("❌ Close column missing")
    st.stop()

# FIX CLOSE COLUMN
close = df['Close']
if isinstance(close, pd.DataFrame):
    close = close.iloc[:, 0]

df['Close'] = pd.to_numeric(close, errors='coerce')
df.dropna(inplace=True)

# ======================
# SIMPLE PORTFOLIO (REAL VALUES)
# ======================
quantity = st.number_input("Enter Quantity", value=10)

current_price = df['Close'].iloc[-1]
portfolio_value = current_price * quantity

col1, col2, col3 = st.columns(3)
col1.metric("💰 Portfolio Value", f"₹{round(portfolio_value,2)}")
col2.metric("📊 Current Price", f"₹{round(current_price,2)}")
col3.metric("📦 Quantity", quantity)

# ======================
# INDICATORS
# ======================
df['MA20'] = df['Close'].rolling(20).mean()

delta = df['Close'].diff()
gain = delta.clip(lower=0).rolling(14).mean()
loss = (-delta.clip(upper=0)).rolling(14).mean()
rs = gain / loss
df['RSI'] = 100 - (100 / (1 + rs))

df.dropna(inplace=True)

# ======================
# TRADE SIGNAL
# ======================
st.subheader("🎯 Trade Decision")

latest_price = df['Close'].iloc[-1]
latest_ma = df['MA20'].iloc[-1]
latest_rsi = df['RSI'].iloc[-1]

col1, col2, col3 = st.columns(3)
col1.metric("Price", round(latest_price, 2))
col2.metric("MA20", round(latest_ma, 2))
col3.metric("RSI", round(latest_rsi, 2))

signal = "HOLD"

if latest_price > latest_ma and latest_rsi < 40:
    signal = "BUY"
    st.success("🟢 STRONG BUY")
elif latest_price < latest_ma and latest_rsi > 60:
    signal = "SELL"
    st.error("🔴 STRONG SELL")
else:
    st.warning("🟡 HOLD")

# ======================
# BACKTESTING
# ======================
st.subheader("📊 Backtesting")

position = 0
entry_price = 0
profits = []
wins = 0
trades = 0

for i in range(20, len(df)):
    price = df['Close'].iloc[i]
    ma = df['MA20'].iloc[i]
    rsi = df['RSI'].iloc[i]

    if position == 0 and price > ma and rsi < 40:
        position = 1
        entry_price = price

    elif position == 1 and price < ma and rsi > 60:
        profit = price - entry_price
        profits.append(profit)

        trades += 1
        if profit > 0:
            wins += 1

        position = 0

if position == 1:
    profit = df['Close'].iloc[-1] - entry_price
    profits.append(profit)
    trades += 1
    if profit > 0:
        wins += 1

total_profit = sum(profits)
win_rate = (wins / trades * 100) if trades > 0 else 0

col1, col2, col3 = st.columns(3)
col1.metric("Profit", f"₹{round(total_profit,2)}")
col2.metric("Trades", trades)
col3.metric("Win Rate", f"{round(win_rate,2)}%")

# ======================
# AI PREDICTION (NO ERROR VERSION)
# ======================
st.subheader("🤖 AI Prediction")

df_ai = df.copy()
df_ai['Target'] = df_ai['Close'].shift(-1)
df_ai.dropna(inplace=True)

X = df_ai[['Close', 'MA20', 'RSI']]
y = df_ai['Target']

model = LinearRegression()
model.fit(X, y)

last_row = df_ai.iloc[-1]
predicted_price = model.predict([[last_row['Close'], last_row['MA20'], last_row['RSI']]])[0]

confidence = abs(predicted_price - last_row['Close']) / last_row['Close'] * 100

col1, col2, col3 = st.columns(3)
col1.metric("Current", round(last_row['Close'],2))
col2.metric("Predicted", round(predicted_price,2))
col3.metric("Confidence", f"{round(confidence,2)}%")

if predicted_price > last_row['Close']:
    st.success("🟢 AI: UP")
else:
    st.error("🔴 AI: DOWN")

# ======================
# CHART
# ======================
st.subheader("📈 Chart")

fig = go.Figure()

fig.add_trace(go.Candlestick(
    x=df.index,
    open=df['Open'],
    high=df['High'],
    low=df['Low'],
    close=df['Close']
))

fig.add_trace(go.Scatter(
    x=df.index,
    y=df['MA20'],
    name="MA20"
))

fig.update_layout(template="plotly_dark")

st.plotly_chart(fig, use_container_width=True)

st.caption("🚀 AI Trading Dashboard • Stable Version")
