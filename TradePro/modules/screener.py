import streamlit as st
import pandas as pd

from utils.data_loader import load_stock_data


def signal(df):

    rsi = df["RSI"].iloc[-1]

    if rsi < 30:
        return "Oversold"

    if rsi > 70:
        return "Overbought"

    return "Neutral"


def show_screener():

    st.title("🔍 Stock Screener")

    tickers = st.text_area(
        "Ticker List",
        "AAPL,NVDA,MSFT,GOOGL,BBCA.JK,TLKM.JK,BBRI.JK,BMRI.JK,ASII.JK,ANTM.JK,ADRO.JK,BUMI.JK"
    )

    filter_signal = st.selectbox(
        "Filter",
        [
            "All",
            "Oversold",
            "Overbought"
        ]
    )

    rows = []

    for ticker in tickers.split(","):

        ticker = ticker.strip()

        df = load_stock_data(
            ticker,
            "6mo"
        )

        if df is None:
            continue

        rows.append({
            "Ticker": ticker,
            "Price": round(float(df["Close"].iloc[-1]), 2),
            "RSI": round(float(df["RSI"].iloc[-1]), 2),
            "Volume": int(df["Volume"].iloc[-1]),
            "Signal": signal(df)
        })

    result = pd.DataFrame(rows)

    if filter_signal != "All":
        result = result[
            result["Signal"] == filter_signal
        ]

    st.dataframe(
        result,
        use_container_width=True
    )
