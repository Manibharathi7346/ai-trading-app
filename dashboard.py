import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go

# ======================
# PAGE CONFIG
# ======================
st.set_page_config(page_title="AI Trading Terminal", layout="wide")

st.title("🤖 AI Trading Terminal")

# ======================
# STOCK LIST
# ======================
stocks = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS"]

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
# LIVE STOCK TABLE
# ======================
st.subheader("📊 Live Market Data")

data = []

for s in stocks:
    df = yf.download(s, period="1d", interval="1m")

    if df is None or df.empty:
        continue

    price = float(df['Close'].iloc[-1])
    change = float(df['Close'].pct_change().iloc[-1] * 100)

    signal = "BUY" if change > 0 else "SELL"

    data.append([s.replace(".NS",""), round(price,2), round(change,2), signal])

df_live = pd.DataFrame(data, columns=["Stock","Price","Change %","Signal"])

st.dataframe(df_live, use_container_width=True)

# ======================
# TOP PICKS
# ======================
st.subheader("🏆 Top Picks Today")

top = df_live.sort_values("Change %", ascending=False).head(2)
st.dataframe(top, use_container_width=True)

# ======================
# ADVANCED CHART
# ======================
st.subheader("📈 Smart Trading Chart")

stock = st.selectbox("Select Stock", stocks)

chart = yf.download(stock, period="5d", interval="15m")

if chart is not None and not chart.empty:

    # Moving Average
    chart['MA20'] = chart['Close'].rolling(20).mean()

    # RSI
    delta = chart['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    chart['RSI'] = 100 - (100 / (1 + rs))

    # AI SIGNAL
    chart['Signal'] = 0

    for i in range(20, len(chart)):
        price = chart['Close'].iloc[i]
        ma = chart['MA20'].iloc[i]
        rsi = chart['RSI'].iloc[i]

        if price > ma and rsi < 35:
            chart.loc[chart.index[i], 'Signal'] = 1

        elif price < ma and rsi > 65:
            chart.loc[chart.index[i], 'Signal'] = -1

    # ======================
    # CANDLE CHART
    # ======================
    fig = go.Figure()

    fig.add_trace(go.Candlestick(
        x=chart.index,
        open=chart['Open'],
        high=chart['High'],
        low=chart['Low'],
        close=chart['Close'],
        name="Candles"
    ))

    # MA Line
    fig.add_trace(go.Scatter(
        x=chart.index,
        y=chart['MA20'],
        line=dict(color='yellow'),
        name="MA20"
    ))

    # BUY SIGNALS
    buy = chart[chart['Signal'] == 1]

    fig.add_trace(go.Scatter(
        x=buy.index,
        y=buy['Close'],
        mode='markers',
        marker=dict(symbol='triangle-up', color='green', size=12),
        name="BUY"
    ))

    # SELL SIGNALS
    sell = chart[chart['Signal'] == -1]

    fig.add_trace(go.Scatter(
        x=sell.index,
        y=sell['Close'],
        mode='markers',
        marker=dict(symbol='triangle-down', color='red', size=12),
        name="SELL"
    ))

    fig.update_layout(
        template="plotly_dark",
        title=f"{stock} Trading Chart",
        xaxis_title="Time",
        yaxis_title="Price"
    )

    st.plotly_chart(fig, use_container_width=True)

    # ======================
    # RSI CHART
    # ======================
    st.subheader("📉 RSI Indicator")

    fig2 = go.Figure()

    fig2.add_trace(go.Scatter(
        x=chart.index,
        y=chart['RSI'],
        line=dict(color='cyan'),
        name="RSI"
    ))

    fig2.add_hline(y=70, line_dash="dash", line_color="red")
    fig2.add_hline(y=30, line_dash="dash", line_color="green")

    fig2.update_layout(
        template="plotly_dark"
    )

    st.plotly_chart(fig2, use_container_width=True)

    # ======================
    # AI SIGNAL TABLE
    # ======================
    st.subheader("🤖 AI Signals Data")

    st.dataframe(chart[['Close','MA20','RSI','Signal']].tail(10),
                 use_container_width=True)

else:
    st.warning("No data available")

# ======================
# PORTFOLIO (STATIC FOR NOW)
# ======================
st.subheader("💰 Portfolio")

col1, col2, col3 = st.columns(3)

col1.metric("Capital", "₹50,000")
col2.metric("Value", "₹52,300")
col3.metric("P&L", "+₹2,300")

# ======================
# ANALYTICS
# ======================
st.subheader("📊 Analytics")

col1, col2, col3 = st.columns(3)

col1.metric("Trades", "12")
col2.metric("Win Rate", "66%")
col3.metric("Profit", "₹3,200")

# ======================
# FOOTER
# ======================
st.caption("🚀 AI Trading System • Live Dashboard")
