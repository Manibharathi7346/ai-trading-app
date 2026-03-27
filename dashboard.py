import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
from sklearn.linear_model import LinearRegression

# ======================
# PAGE CONFIG
# ======================
st.set_page_config(page_title="AI Trading Terminal", layout="wide")

# ======================
# PREMIUM UI STYLE
# ======================
st.markdown("""
<style>
.block-container {
    padding-top: 2rem;
}
[data-testid="stMetric"] {
    background-color: #111827;
    padding: 15px;
    border-radius: 12px;
}
</style>
""", unsafe_allow_html=True)

st.title("🤖 AI Trading + Wealth Dashboard")

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
# STOCK LIST
# ======================
stocks = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS"]

stock = st.selectbox("📌 Select Stock", stocks)

# ======================
# LOAD DATA (STABLE)
# ======================
df = yf.download(stock, period="1mo", interval="5m", progress=False, threads=False)

if df is None or df.empty or 'Close' not in df.columns:
    st.error("❌ Unable to fetch data")
    st.stop()

df['Close'] = pd.to_numeric(df['Close'], errors='coerce')
df.dropna(inplace=True)

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
# TRADE DECISION
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
st.subheader("📊 Strategy Backtesting")

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

# close open trade
if position == 1:
    profit = df['Close'].iloc[-1] - entry_price
    profits.append(profit)
    trades += 1
    if profit > 0:
        wins += 1

total_profit = sum(profits)
win_rate = (wins / trades * 100) if trades > 0 else 0

col1, col2, col3 = st.columns(3)
col1.metric("💰 Total Profit", f"₹{round(total_profit,2)}")
col2.metric("📊 Trades", trades)
col3.metric("🎯 Win Rate", f"{round(win_rate,2)}%")

# ======================
# ADVANCED AI PREDICTION
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
input_data = [[last_row['Close'], last_row['MA20'], last_row['RSI']]]

predicted_price = model.predict(input_data)[0]
current_price = last_row['Close']

confidence = abs(predicted_price - current_price) / current_price * 100

col1, col2, col3 = st.columns(3)
col1.metric("Current Price", round(current_price, 2))
col2.metric("Predicted Price", round(predicted_price, 2))
col3.metric("Confidence", f"{round(confidence,2)}%")

if predicted_price > current_price:
    st.success("🟢 AI: Market likely UP")
else:
    st.error("🔴 AI: Market likely DOWN")

# ======================
# AI ACCURACY
# ======================
st.subheader("📊 AI Accuracy")

correct = 0
wrong = 0

for i in range(len(df_ai) - 1):
    row = df_ai.iloc[i]
    next_price = df_ai['Close'].iloc[i+1]

    pred = model.predict([[row['Close'], row['MA20'], row['RSI']]])[0]

    if (pred > row['Close'] and next_price > row['Close']) or \
       (pred < row['Close'] and next_price < row['Close']):
        correct += 1
    else:
        wrong += 1

total = correct + wrong
accuracy = (correct / total * 100) if total > 0 else 0

col1, col2, col3 = st.columns(3)
col1.metric("Accuracy", f"{round(accuracy,2)}%")
col2.metric("Correct", correct)
col3.metric("Wrong", wrong)

# ======================
# CHART
# ======================
st.subheader("📈 Price Chart")

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

# ======================
# FINAL FOOTER
# ======================
st.caption("🚀 AI Trading System • Premium Version")
