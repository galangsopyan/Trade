import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sqlite3

# ==========================================
# PAGE CONFIG
# ==========================================

st.set_page_config(
    page_title="Personal Trading Dashboard",
    page_icon="📈",
    layout="wide"
)

# ==========================================
# DATABASE
# ==========================================

conn = sqlite3.connect(
    "trading_journal.db",
    check_same_thread=False
)

cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS journal(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT,
    ticker TEXT,
    action TEXT,
    price REAL,
    notes TEXT
)
""")

conn.commit()

# ==========================================
# INDICATOR FUNCTIONS
# ==========================================

def calculate_rsi(data, period=14):

    delta = data.diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()

    rs = avg_gain / avg_loss

    rsi = 100 - (100 / (1 + rs))

    return rsi


@st.cache_data(ttl=300)
def load_stock_data(ticker, period):

    try:

        df = yf.download(
            ticker,
            period=period,
            progress=False,
            auto_adjust=True
        )

        if df.empty:
            return None

        df["EMA20"] = (
            df["Close"]
            .ewm(span=20, adjust=False)
            .mean()
        )

        df["EMA200"] = (
            df["Close"]
            .ewm(span=200, adjust=False)
            .mean()
        )

        df["RSI"] = calculate_rsi(
            df["Close"]
        )

        return df

    except Exception as e:
        st.error(f"Error: {e}")
        return None


def generate_signal(df):

    rsi = df["RSI"].iloc[-1]

    ema20 = df["EMA20"].iloc[-1]

    ema200 = df["EMA200"].iloc[-1]

    if rsi < 30 and ema20 > ema200:
        return "BUY SIGNAL"

    elif rsi > 70 and ema20 < ema200:
        return "SELL SIGNAL"

    else:
        return "HOLD / NEUTRAL"


# ==========================================
# SIDEBAR
# ==========================================

st.sidebar.title("Navigation")

menu = st.sidebar.radio(
    "Select Module",
    [
        "Main Dashboard",
        "Multi Stock Screener",
        "Strategy Backtester",
        "Risk Management & Journal"
    ]
)

st.title("📈 Personal Trading Dashboard")
st.markdown("---")
