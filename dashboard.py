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
# HELPER FUNCTION
# ======================
def get_safe_last(series):
    try:
        series = pd.to_numeric(series, errors='coerce').dropna()
        if series.empty:
            return None
        return float(series.iloc[-1])
    except:
        return None

# ======================
# STOCK LIST
# ======================
stocks = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS"]

# ======================
# MARKET TREND (FIXED)
# ======================
nifty = yf.download("NIFTY50.NS", period="5d", progress=False)

if nifty is not None and not nifty.empty and 'Close' in nifty.columns:
    trend_series = nifty['Close'].pct_change().dropna()

    if not trend_series.empty:
        trend = trend_series.iloc[-1]   # ✅ FIX

        if trend > 0:
            st.success("📈 Market Positive")
        else:
            st.error("📉 Market Weak")
    else:
        st.warning("No trend data available")
else:
    st.warning("⚠️ Unable to fetch market trend")

# ======================
# LIVE MARKET DATA
# ======================
st.subheader("📊 Live Market")

data = []

for s in stocks:
    try:
        df = yf.download(s, period="1d", interval="1m", progress=False)

        if df is None or df.empty or 'Close' not in df.columns:
            continue

        price = get_safe_last(df['Close'])
        change = get_safe_last(df['Close'].pct_change() * 100)

        if price is None or change is None:
            continue

        signal = "BUY" if change > 0 else "SELL"

        data.append([
            s.replace(".NS", ""),
            round(price, 2),
            round(change, 2),
            signal
        ])

    except:
        continue

df_live = pd.DataFrame(data, columns=["Stock", "Price", "Change %", "Signal"])

def highlight_signal(val):
    if val == "BUY":
        return "color: green; font-weight: bold"
    elif val == "SELL":
        return "color: red; font-weight: bold"
    return ""

if not df_live.empty:
    st.dataframe(df_live.style.applymap(highlight_signal, subset=["Signal"]), use_container_width=True)
else:
    st.warning("No live data available")

# ======================
# AI STOCK RANKING
# ======================
st.subheader("🏆 AI Top Picks")

ranked_data = []

for s in stocks:
    try:
        df = yf.download(s, period="5d", interval="15m", progress=False)

        if df is None or df.empty or 'Close' not in df.columns:
            continue

        df['Close'] = pd.to_numeric(df['Close'], errors='coerce')
        df.dropna(inplace=True)

        if len(df) < 20:
            continue

        df['MA20'] = df['Close'].rolling(20).mean()

        delta = df['Close'].diff()
        gain = delta.clip(lower=0).rolling(14).mean()
        loss = (-delta.clip(upper=0)).rolling(14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))

        price = get_safe_last(df['Close'])
        ma = get_safe_last(df['MA20'])
        rsi = get_safe_last(df['RSI'])

        if None in (price, ma, rsi):
            continue

        score = 0

        if price > ma:
            score += 40
        if rsi < 40:
            score += 30
        if rsi < 30:
            score += 30

        signal = 1 if score >= 60 else -1 if score <= 30 else 0

        ranked_data.append({
            "Stock": s.replace(".NS", ""),
            "Price": round(price, 2),
            "RSI": round(rsi, 2),
            "Score": score,
            "Signal": signal
        })

    except:
        continue

df_ranked = pd.DataFrame(ranked_data)

if not df_ranked.empty:
    df_ranked = df_ranked.sort_values("Score", ascending=False)
    top_stocks = df_ranked.head(2)
    st.dataframe(top_stocks, use_container_width=True)
else:
    top_stocks = pd.DataFrame()
    st.warning("No ranking data available")

# ======================
# SMART CHART
# ======================
st.subheader("📈 Smart Chart")

stock = st.selectbox("Select Stock", stocks)

chart = yf.download(stock, period="5d", interval="15m", progress=False)

if chart is not None and not chart.empty and 'Close' in chart.columns:

    chart['Close'] = pd.to_numeric(chart['Close'], errors='coerce')
    chart.dropna(inplace=True)

    if len(chart) > 20:

        chart['MA20'] = chart['Close'].rolling(20).mean()

        delta = chart['Close'].diff()
        gain = delta.clip(lower=0).rolling(14).mean()
        loss = (-delta.clip(upper=0)).rolling(14).mean()
        rs = gain / loss
        chart['RSI'] = 100 - (100 / (1 + rs))

        chart['Signal'] = 0

        for i in range(20, len(chart)):
            price = chart['Close'].iloc[i]
            ma = chart['MA20'].iloc[i]
            rsi = chart['RSI'].iloc[i]

            if pd.notna(ma) and pd.notna(rsi):
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

    else:
        st.warning("Not enough data for chart")
else:
    st.warning("Chart data unavailable")

# ======================
# PORTFOLIO
# ======================
st.subheader("💰 Portfolio")

if not top_stocks.empty:
    portfolio = top_stocks.copy()
    portfolio["Profit"] = portfolio["Price"].diff().fillna(0)

    st.metric("Trades", len(portfolio))
    st.metric("Total Profit", f"₹{round(portfolio['Profit'].sum(), 2)}")

    st.dataframe(portfolio, use_container_width=True)
else:
    st.warning("No portfolio data")

# ======================
# EXPORT SIGNAL
# ======================
try:
    export_data = top_stocks.to_dict(orient="records")
    with open("signal.json", "w") as f:
        json.dump(export_data, f)
    st.success("✅ Signals exported for trading bot")
except:
    st.warning("⚠️ Export failed")

# ======================
# FOOTER
# ======================
st.caption("🚀 AI Trading System • Stable Version")
