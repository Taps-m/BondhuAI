import streamlit as st


def handle_api_error(error):
    st.error(f"Bondhu API Error: {type(error).__name__}")
    st.code(str(error))