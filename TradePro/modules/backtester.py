import streamlit as st
import pandas as pd

from utils.data_loader import load_stock_data


def show_backtester():

    st.title("⚡ RSI Strategy Backtester")

    ticker = st.text_input(
        "Ticker",
        "AAPL"
    )

    capital = st.number_input(
        "Initial Capital",
        value=10000
    )

    df = load_stock_data(
        ticker,
        "5y"
    )

    if df is None:
        return

    cash = capital
    shares = 0

    trades = []

    for i in range(1, len(df)):

        rsi = df["RSI"].iloc[i]
        price = df["Close"].iloc[i]

        if shares == 0 and rsi < 30:

            shares = cash / price
            cash = 0

            trades.append([
                df.index[i],
                "BUY",
                price
            ])

        elif shares > 0 and rsi > 70:

            cash = shares * price
            shares = 0

            trades.append([
                df.index[i],
                "SELL",
                price
            ])

    final_capital = cash

    total_return = (
        (final_capital - capital)
        / capital
    ) * 100

    st.metric(
        "Total Return",
        f"{total_return:.2f}%"
    )

    trade_df = pd.DataFrame(
        trades,
        columns=[
            "Date",
            "Action",
            "Price"
        ]
    )

    with st.expander("Trade Log"):
        st.dataframe(
            trade_df,
            use_container_width=True
        )
