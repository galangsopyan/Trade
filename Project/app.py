import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sqlite3

# ==================================================
# CONFIG
# ==================================================

st.set_page_config(
    page_title="Personal Trading Dashboard",
    page_icon="📈",
    layout="wide"
)

# ==================================================
# DATABASE
# ==================================================

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

# ==================================================
# INDICATORS
# ==================================================

def calculate_rsi(close, period=14):

    delta = close.diff()

    gain = delta.clip(lower=0)

    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(period).mean()

    avg_loss = loss.rolling(period).mean()

    rs = avg_gain / avg_loss

    return 100 - (100 / (1 + rs))

# ==================================================
# DATA
# ==================================================

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

        df["EMA20"] = df["Close"].ewm(
            span=20,
            adjust=False
        ).mean()

        df["EMA200"] = df["Close"].ewm(
            span=200,
            adjust=False
        ).mean()

        df["RSI"] = calculate_rsi(
            df["Close"]
        )

        return df

    except:
        return None

# ==================================================
# SIGNAL
# ==================================================

def get_signal(df):

    rsi = df["RSI"].iloc[-1]

    ema20 = df["EMA20"].iloc[-1]

    ema200 = df["EMA200"].iloc[-1]

    if rsi < 30 and ema20 > ema200:
        return "BUY"

    elif rsi > 70 and ema20 < ema200:
        return "SELL"

    else:
        return "HOLD"

# ==================================================
# SIDEBAR
# ==================================================

st.sidebar.title("Navigation")

menu = st.sidebar.radio(
    "Module",
    [
        "Main Dashboard",
        "Multi Stock Screener",
        "Strategy Backtester",
        "Risk Management & Journal"
    ]
)

# ==================================================
# MAIN DASHBOARD
# ==================================================

if menu == "Main Dashboard":

    st.title("📈 Market Dashboard")

    col1, col2 = st.columns([3,1])

    with col1:
        ticker = st.text_input(
            "Ticker",
            "AAPL"
        )

    with col2:
        timeframe = st.selectbox(
            "Period",
            ["1mo","3mo","6mo","1y","2y","5y"]
        )

    df = load_stock_data(
        ticker,
        timeframe
    )

    if df is None:
        st.error("Ticker not found")
        st.stop()

    current = float(df["Close"].iloc[-1])

    prev = float(df["Close"].iloc[-2])

    change = (
        (current-prev)
        / prev
    ) * 100

    rsi = float(df["RSI"].iloc[-1])

    trend = (
        "Bullish"
        if df["EMA20"].iloc[-1]
        > df["EMA200"].iloc[-1]
        else "Bearish"
    )

    c1,c2,c3,c4 = st.columns(4)

    c1.metric(
        "Price",
        f"{current:.2f}"
    )

    c2.metric(
        "Change %",
        f"{change:.2f}%"
    )

    c3.metric(
        "RSI",
        f"{rsi:.2f}"
    )

    c4.metric(
        "Trend",
        trend
    )

    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        row_heights=[0.75,0.25]
    )

    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df["Open"],
            high=df["High"],
            low=df["Low"],
            close=df["Close"]
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
            y=df["EMA200"],
            name="EMA200"
        ),
        row=1,
        col=1
    )

    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df["RSI"],
            name="RSI"
        ),
        row=2,
        col=1
    )

    fig.add_hline(
        y=70,
        row=2,
        col=1,
        line_dash="dash"
    )

    fig.add_hline(
        y=30,
        row=2,
        col=1,
        line_dash="dash"
    )

    fig.update_layout(
        template="plotly_dark",
        height=800,
        xaxis_rangeslider_visible=False
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    signal = get_signal(df)

    if signal == "BUY":
        st.success("BUY SIGNAL")

    elif signal == "SELL":
        st.error("SELL SIGNAL")

    else:
        st.warning("HOLD")

# ==================================================
# SCREENER
# ==================================================

elif menu == "Multi Stock Screener":

    st.title("🔍 Multi Stock Screener")

    text = st.text_area(
        "Ticker List",
        "AAPL,NVDA,MSFT,BBCA.JK,TLKM.JK"
    )

    tickers = [
        x.strip()
        for x in text.split(",")
    ]

    rows = []

    for t in tickers:

        df = load_stock_data(
            t,
            "6mo"
        )

        if df is None:
            continue

        rows.append({
            "Ticker": t,
            "Price": round(
                float(df["Close"].iloc[-1]),2
            ),
            "RSI": round(
                float(df["RSI"].iloc[-1]),2
            ),
            "Volume": int(
                df["Volume"].iloc[-1]
            ),
            "Signal": get_signal(df)
        })

    st.dataframe(
        pd.DataFrame(rows),
        use_container_width=True
    )

# ==================================================
# BACKTESTER
# ==================================================

elif menu == "Strategy Backtester":

    st.title("⚡ RSI Backtester")

    ticker = st.text_input(
        "Ticker",
        "AAPL"
    )

    df = load_stock_data(
        ticker,
        "5y"
    )

    if df is not None:

        capital = 10000

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

        final_value = cash

        total_return = (
            (final_value-capital)
            / capital
        ) * 100

        st.metric(
            "Total Return %",
            f"{total_return:.2f}%"
        )

        with st.expander("Trade Log"):

            st.dataframe(
                pd.DataFrame(
                    trades,
                    columns=[
                        "Date",
                        "Action",
                        "Price"
                    ]
                )
            )

# ==================================================
# RISK MANAGEMENT
# ==================================================

elif menu == "Risk Management & Journal":

    st.title("🛡 Risk Management")

    capital = st.number_input(
        "Capital",
        value=10000.0
    )

    risk_pct = st.number_input(
        "Risk %",
        value=1.0
    )

    entry = st.number_input(
        "Entry Price",
        value=100.0
    )

    stop = st.number_input(
        "Stop Loss",
        value=95.0
    )

    risk_amount = (
        capital * risk_pct / 100
    )

    risk_share = abs(
        entry - stop
    )

    shares = (
        risk_amount / risk_share
        if risk_share > 0
        else 0
    )

    st.success(
        f"Position Size : {shares:.0f} Shares"
    )

    st.info(
        f"Maximum Risk : ${risk_amount:.2f}"
    )

    st.divider()

    st.subheader("Trading Journal")

    with st.form("journal"):

        date = st.date_input("Date")

        ticker = st.text_input("Ticker")

        action = st.selectbox(
            "Action",
            ["BUY","SELL"]
        )

        price = st.number_input(
            "Price"
        )

        notes = st.text_area(
            "Notes"
        )

        submit = st.form_submit_button(
            "Save"
        )

        if submit:

            cursor.execute(
                """
                INSERT INTO journal
                (
                date,
                ticker,
                action,
                price,
                notes
                )
                VALUES (?,?,?,?,?)
                """,
                (
                    str(date),
                    ticker,
                    action,
                    price,
                    notes
                )
            )

            conn.commit()

            st.success("Saved")

    journal = pd.read_sql(
        "SELECT * FROM journal ORDER BY id DESC",
        conn
    )

    st.dataframe(
        journal,
        use_container_width=True
                )

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
