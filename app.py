import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import pandas_ta as ta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sqlite3
from datetime import datetime

# =====================================================
# CONFIG
# =====================================================

st.set_page_config(
    page_title="Personal Trading Dashboard",
    page_icon="📈",
    layout="wide"
)

st.title("📈 Personal Stock Trading Dashboard")
st.markdown("---")

# =====================================================
# DATABASE
# =====================================================

conn = sqlite3.connect("trading_journal.db", check_same_thread=False)
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

# =====================================================
# CACHE DATA
# =====================================================

@st.cache_data(ttl=300)
def load_stock_data(ticker, period):
    try:
        df = yf.download(
            ticker,
            period=period,
            auto_adjust=True,
            progress=False
        )

        if df.empty:
            return None

        df["EMA20"] = ta.ema(df["Close"], length=20)
        df["EMA200"] = ta.ema(df["Close"], length=200)
        df["RSI"] = ta.rsi(df["Close"], length=14)

        return df

    except Exception:
        return None


# =====================================================
# SIGNAL GENERATOR
# =====================================================

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


# =====================================================
# SIDEBAR
# =====================================================

menu = st.sidebar.radio(
    "Navigation",
    [
        "Main Dashboard",
        "Multi-Stock Screener",
        "Strategy Backtester",
        "Risk Management & Journal"
    ]
)

# =====================================================
# MAIN DASHBOARD
# =====================================================

if menu == "Main Dashboard":

    st.header("📊 Market Analysis Dashboard")

    col1, col2 = st.columns([3,1])

    with col1:
        ticker = st.text_input(
            "Ticker",
            value="AAPL"
        )

    with col2:
        timeframe = st.selectbox(
            "Timeframe",
            ["1d","5d","1mo","3mo","6mo","1y","2y","5y","max"],
            index=6
        )

    df = load_stock_data(ticker, timeframe)

    if df is None:
        st.error("Invalid ticker or no data found.")
        st.stop()

    current_price = float(df["Close"].iloc[-1])

    prev_price = float(df["Close"].iloc[-2])

    pct_change = ((current_price-prev_price)/prev_price)*100

    rsi = float(df["RSI"].iloc[-1])

    trend = (
        "Bullish"
        if df["EMA20"].iloc[-1] > df["EMA200"].iloc[-1]
        else "Bearish"
    )

    c1,c2,c3,c4 = st.columns(4)

    c1.metric(
        "Current Price",
        f"{current_price:.2f}"
    )

    c2.metric(
        "Price Change %",
        f"{pct_change:.2f}%"
    )

    c3.metric(
        "RSI (14)",
        f"{rsi:.2f}"
    )

    c4.metric(
        "Trend",
        trend
    )

    # ==========================================
    # PLOTLY CHART
    # ==========================================

    fig = make_subplots(
        rows=3,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=[0.6,0.2,0.2]
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
        xaxis_rangeslider_visible=False,
        template="plotly_dark"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    signal = generate_signal(df)

    st.markdown("### Trading Signal")

    if signal == "BUY SIGNAL":
        st.success(signal)

    elif signal == "SELL SIGNAL":
        st.error(signal)

    else:
        st.warning(signal)

# =====================================================
# MULTI STOCK SCREENER
# =====================================================

elif menu == "Multi-Stock Screener":

    st.header("🔍 Multi Stock Screener")

    default_list = "AAPL,MSFT,GOOGL,TSLA,BBCA.JK"

    ticker_text = st.text_area(
        "Ticker List",
        default_list
    )

    tickers = [
        x.strip()
        for x in ticker_text.split(",")
    ]

    filter_option = st.selectbox(
        "Filter",
        [
            "All",
            "Oversold",
            "Overbought"
        ]
    )

    results = []

    for ticker in tickers:

        df = load_stock_data(
            ticker,
            "3mo"
        )

        if df is None:
            continue

        rsi = float(df["RSI"].iloc[-1])

        if rsi < 30:
            status = "Oversold"

        elif rsi > 70:
            status = "Overbought"

        else:
            status = "Neutral"

        results.append({
            "Ticker": ticker,
            "Last Price": round(
                float(df["Close"].iloc[-1]),2
            ),
            "RSI": round(rsi,2),
            "Volume": int(df["Volume"].iloc[-1]),
            "Signal": status
        })

    screener_df = pd.DataFrame(results)

    if filter_option != "All":
        screener_df = screener_df[
            screener_df["Signal"] == filter_option
        ]

    st.dataframe(
        screener_df,
        use_container_width=True
    )

# =====================================================
# BACKTESTER
# =====================================================

elif menu == "Strategy Backtester":

    st.header("⚡ RSI Strategy Backtester")

    ticker = st.text_input(
        "Ticker",
        "AAPL",
        key="backtest"
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

        wins = 0
        losses = 0

        portfolio_values = []

        position = False
        buy_price = 0

        for i in range(1,len(df)):

            rsi_prev = df["RSI"].iloc[i-1]
            rsi_now = df["RSI"].iloc[i]

            price = df["Close"].iloc[i]

            if not position:

                if rsi_prev > 30 and rsi_now < 30:

                    shares = cash / price

                    buy_price = price

                    cash = 0

                    position = True

                    trades.append(
                        [
                            df.index[i],
                            "BUY",
                            price
                        ]
                    )

            else:

                if rsi_prev < 70 and rsi_now > 70:

                    cash = shares * price

                    pnl = price - buy_price

                    if pnl > 0:
                        wins += 1
                    else:
                        losses += 1

                    shares = 0
                    position = False

                    trades.append(
                        [
                            df.index[i],
                            "SELL",
                            price
                        ]
                    )

            current_value = (
                cash if shares == 0
                else shares * price
            )

            portfolio_values.append(current_value)

        final_capital = portfolio_values[-1]

        total_return = (
            (final_capital-capital)
            / capital
        ) * 100

        equity = pd.Series(
            portfolio_values
        )

        rolling_max = equity.cummax()

        drawdown = (
            (equity-rolling_max)
            / rolling_max
        )

        max_drawdown = drawdown.min()*100

        total_trades = wins + losses

        win_rate = (
            wins/total_trades*100
            if total_trades > 0
            else 0
        )

        metrics = pd.DataFrame({
            "Metric":[
                "Initial Capital",
                "Final Capital",
                "Total Return %",
                "Win Rate %",
                "Executed Trades",
                "Max Drawdown %"
            ],
            "Value":[
                round(capital,2),
                round(final_capital,2),
                round(total_return,2),
                round(win_rate,2),
                total_trades,
                round(max_drawdown,2)
            ]
        })

        st.dataframe(
            metrics,
            use_container_width=True
        )

        trade_df = pd.DataFrame(
            trades,
            columns=[
                "Date",
                "Action",
                "Price"
            ]
        )

        with st.expander(
            "Trade Log"
        ):
            st.dataframe(
                trade_df,
                use_container_width=True
            )

# =====================================================
# RISK MANAGEMENT
# =====================================================

elif menu == "Risk Management & Journal":

    st.header("🛡 Risk Management")

    col1,col2 = st.columns(2)

    with col1:

        capital = st.number_input(
            "Total Capital",
            value=10000.0
        )

        risk_pct = st.number_input(
            "Risk %",
            value=1.0
        )

    with col2:

        entry = st.number_input(
            "Entry Price",
            value=100.0
        )

        stop = st.number_input(
            "Stop Loss",
            value=95.0
        )

    risk_amount = (
        capital*risk_pct/100
    )

    risk_per_share = abs(
        entry-stop
    )

    shares = (
        risk_amount/risk_per_share
        if risk_per_share > 0
        else 0
    )

    st.success(
        f"Position Size: {shares:.0f} shares"
    )

    st.info(
        f"Maximum Risk: ${risk_amount:.2f}"
    )

    st.markdown("---")

    st.header("📒 Trading Journal")

    with st.form("journal_form"):

        date = st.date_input(
            "Date"
        )

        ticker = st.text_input(
            "Ticker"
        )

        action = st.selectbox(
            "Action",
            ["BUY","SELL"]
        )

        price = st.number_input(
            "Price",
            value=0.0
        )

        notes = st.text_area(
            "Notes / Psychology"
        )

        submit = st.form_submit_button(
            "Save Journal"
        )

        if submit:

            cursor.execute("""
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
            ))

            conn.commit()

            st.success(
                "Journal saved."
            )

    journal_df = pd.read_sql(
        "SELECT * FROM journal ORDER BY id DESC",
        conn
    )

    st.dataframe(
        journal_df,
        use_container_width=True
    )
