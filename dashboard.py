import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
import json

# ======================
# PAGE CONFIG
# ======================
st.set_page_config(page_title="AI Trading Terminal", layout="wide")

st.title("🤖 AI Trading Terminal")

# ======================
# STOCK LIST
# ======================
stocks = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS"]

# ======================
# MARKET TREND
# ======================
nifty = yf.download("NIFTY50.NS", period="5d")

if not nifty.empty:
    trend = nifty['Close'].pct_change().iloc[-1]
    if trend > 0:
        st.success("📈 Market Positive")
    else:
        st.error("📉 Market Weak")

# ======================
# LIVE MARKET DATA
# ======================
st.subheader("📊 Live Market")

data = []

for s in stocks:
    df = yf.download(s, period="1d", interval="1m")

    if df is None or df.empty:
        continue

    price = float(df['Close'].values[-1])
    change = float(df['Close'].pct_change().iloc[-1] * 100)

    signal = "BUY" if change > 0 else "SELL"

    data.append([s.replace(".NS",""), round(price,2), round(change,2), signal])

df_live = pd.DataFrame(data, columns=["Stock","Price","Change %","Signal"])

def highlight_signal(val):
    if val == "BUY":
        return "color: green; font-weight: bold"
    elif val == "SELL":
        return "color: red; font-weight: bold"
    return ""

st.dataframe(df_live.style.applymap(highlight_signal, subset=["Signal"]), use_container_width=True)

# ======================
# AI STOCK RANKING
# ======================
st.subheader("🏆 AI Top Picks")

ranked_data = []

for s in stocks:
    df = yf.download(s, period="5d", interval="15m")

    if df is None or df.empty:
        continue

    # Indicators
    df['MA20'] = df['Close'].rolling(20).mean()

    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))

    price = float(df['Close'].iloc[-1])
    ma = float(df['MA20'].iloc[-1])
    rsi = float(df['RSI'].iloc[-1])

    score = 0

    # AI scoring
    if price > ma:
        score += 40
    if rsi < 40:
        score += 30
    if rsi < 30:
        score += 30

    signal = 0
    if score >= 60:
        signal = 1
    elif score <= 30:
        signal = -1

    ranked_data.append({
        "Stock": s.replace(".NS",""),
        "Price": round(price,2),
        "RSI": round(rsi,2),
        "Score": score,
        "Signal": signal
    })

df_ranked = pd.DataFrame(ranked_data).sort_values("Score", ascending=False)

top_stocks = df_ranked.head(2)

st.dataframe(top_stocks, use_container_width=True)

# ======================
# SMART CHART
# ======================
st.subheader("📈 Smart Chart")

stock = st.selectbox("Select Stock", stocks)

chart = yf.download(stock, period="5d", interval="15m")

if chart is not None and not chart.empty:

    chart['MA20'] = chart['Close'].rolling(20).mean()

    delta = chart['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    chart['RSI'] = 100 - (100 / (1 + rs))

    chart['Signal'] = 0

    for i in range(20, len(chart)):
        price = chart['Close'].iloc[i]
        ma = chart['MA20'].iloc[i]
        rsi = chart['RSI'].iloc[i]

        if price > ma and rsi < 35:
            chart.loc[chart.index[i], 'Signal'] = 1
        elif price < ma and rsi > 65:
            chart.loc[chart.index[i], 'Signal'] = -1

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

    buy = chart[chart['Signal'] == 1]
    sell = chart[chart['Signal'] == -1]

    fig.add_trace(go.Scatter(
        x=buy.index,
        y=buy['Close'],
        mode='markers',
        marker=dict(symbol='triangle-up', color='green', size=10),
        name="BUY"
    ))

    fig.add_trace(go.Scatter(
        x=sell.index,
        y=sell['Close'],
        mode='markers',
        marker=dict(symbol='triangle-down', color='red', size=10),
        name="SELL"
    ))

    fig.update_layout(template="plotly_dark")

    st.plotly_chart(fig, use_container_width=True)

# ======================
# PORTFOLIO (BASIC VIEW)
# ======================
st.subheader("💰 Portfolio")

if not top_stocks.empty:
    portfolio = top_stocks.copy()
    portfolio["Profit"] = portfolio["Price"].diff().fillna(0)

    st.metric("Trades", len(portfolio))
    st.metric("Total Profit", f"₹{round(portfolio['Profit'].sum(),2)}")

    st.dataframe(portfolio, use_container_width=True)

# ======================
# EXPORT SIGNAL FOR BOT
# ======================
export_data = top_stocks.to_dict(orient="records")

with open("signal.json", "w") as f:
    json.dump(export_data, f)

st.success("✅ Signals exported for trading bot")

# ======================
# FOOTER
# ======================
st.caption("🚀 AI Trading System • Stable Version")
