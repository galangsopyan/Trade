import streamlit as st

from utils.database import (
    init_db,
    add_journal,
    get_journal
)


def show_journal():

    init_db()

    st.title("📒 Trading Journal")

    with st.form("journal"):

        date = st.date_input(
            "Date"
        )

        ticker = st.text_input(
            "Ticker"
        )

        action = st.selectbox(
            "Action",
            ["BUY", "SELL"]
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

            add_journal(
                str(date),
                ticker,
                action,
                price,
                notes
            )

            st.success(
                "Journal Saved"
            )

    st.subheader("History")

    st.dataframe(
        get_journal(),
        use_container_width=True
    )
