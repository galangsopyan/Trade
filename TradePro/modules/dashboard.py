import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from utils.data_loader import load_stock_data


def get_signal(df):

    rsi = df["RSI"].iloc[-1]
    ema20 = df["EMA20"].iloc[-1]
    ema200 = df["EMA200"].iloc[-1]

    if rsi < 30 and ema20 > ema200:
        return "BUY"

    elif rsi > 70 and ema20 < ema200:
        return "SELL"

    return "HOLD"


def show_dashboard():

    st.title("📈 Trading Dashboard")

    col1, col2 = st.columns([3, 1])

    with col1:
        ticker = st.text_input(
            "Ticker",
            value="AAPL"
        )

    with col2:
        period = st.selectbox(
            "Period",
            ["1mo", "3mo", "6mo", "1y", "2y", "5y"]
        )

    df = load_stock_data(
        ticker,
        period
    )

    if df is None:
        st.error("Ticker tidak ditemukan")
        return

    price = float(df["Close"].iloc[-1])
    prev = float(df["Close"].iloc[-2])

    change = ((price - prev) / prev) * 100

    rsi = float(df["RSI"].iloc[-1])

    trend = (
        "Bullish"
        if df["EMA20"].iloc[-1] >
        df["EMA200"].iloc[-1]
        else "Bearish"
    )

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Price", f"{price:.2f}")
    c2.metric("Change", f"{change:.2f}%")
    c3.metric("RSI", f"{rsi:.2f}")
    c4.metric("Trend", trend)

    fig = make_subplots(
        rows=3,
        cols=1,
        shared_xaxes=True,
        row_heights=[0.6, 0.2, 0.2]
    )

    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df["Open"],
            high=df["High"],
            low=df["Low"],
            close=df["Close"],
            name="Price"
        ),
        row=1,
        col=1
    )

    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df["EMA20"],
            name="EMA20"
        ),
        row=1,
        col=1
    )

    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df["EMA50"],
            name="EMA50"
        ),
        row=1,
        col=1
    )

    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df["EMA200"],
            name="EMA200"
        ),
        row=1,
        col=1
    )

    fig.add_trace(
        go.Bar(
            x=df.index,
            y=df["Volume"],
            name="Volume"
        ),
        row=2,
        col=1
    )

    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df["RSI"],
            name="RSI"
        ),
        row=3,
        col=1
    )

    fig.add_hline(
        y=70,
        row=3,
        col=1,
        line_dash="dash"
    )

    fig.add_hline(
        y=30,
        row=3,
        col=1,
        line_dash="dash"
    )

    fig.update_layout(
        height=900,
        template="plotly_dark",
        xaxis_rangeslider_visible=False
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    signal = get_signal(df)

    if signal == "BUY":
        st.success("🟢 BUY SIGNAL")

    elif signal == "SELL":
        st.error("🔴 SELL SIGNAL")

    else:
        st.warning("🟡 HOLD")
