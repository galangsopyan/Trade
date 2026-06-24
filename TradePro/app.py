import streamlit as st

from modules.dashboard import show_dashboard
from modules.screener import show_screener
from modules.backtester import show_backtester
from modules.risk import show_risk_management
from modules.journal import show_journal

st.set_page_config(
    page_title="TradePro",
    page_icon="📈",
    layout="wide"
)

st.sidebar.title("📈 TradePro")

menu = st.sidebar.radio(
    "Navigation",
    [
        "Dashboard",
        "Screener",
        "Backtester",
        "Risk Management",
        "Trading Journal"
    ]
)

if menu == "Dashboard":
    show_dashboard()

elif menu == "Screener":
    show_screener()

elif menu == "Backtester":
    show_backtester()

elif menu == "Risk Management":
    show_risk_management()

elif menu == "Trading Journal":
    show_journal()
