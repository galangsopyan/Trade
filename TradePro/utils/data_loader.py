import streamlit as st
import pandas as pd
import yfinance as yf

from utils.indicators import add_indicators

@st.cache_data(ttl=300)
def load_stock_data(ticker, period):

    try:

        df = yf.download(
            ticker,
            period=period,
            auto_adjust=True,
            progress=False,
            group_by="column"
        )

        if df is None or df.empty:
            return None

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        df = add_indicators(df)

        return df

    except:
        return None
