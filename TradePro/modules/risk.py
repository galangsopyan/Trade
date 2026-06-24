import streamlit as st


def show_risk_management():

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

    risk_per_share = abs(
        entry - stop
    )

    shares = (
        risk_amount / risk_per_share
        if risk_per_share > 0
        else 0
    )

    st.success(
        f"Position Size : {shares:.0f} Shares"
    )

    st.info(
        f"Maximum Risk : ${risk_amount:.2f}"
    )
