import streamlit as st


def handle_api_error(error):
    """
    Handle API errors without exposing technical details to users.
    """

    error_message = str(error)

    if "503" in error_message or "UNAVAILABLE" in error_message:
        st.error(
            "🤝 Bondhu is temporarily busy. "
            "Please try again in a moment."
        )

    elif "429" in error_message or "RESOURCE_EXHAUSTED" in error_message:
        st.error(
            "🤝 Bondhu is currently receiving too many requests. "
            "Please try again shortly."
        )

    elif "401" in error_message or "UNAUTHENTICATED" in error_message:
        st.error(
            "🤝 Bondhu could not connect to its AI service. "
            "Please check the API configuration."
        )

    elif "403" in error_message or "PERMISSION_DENIED" in error_message:
        st.error(
            "🤝 Bondhu does not have permission to access "
            "the required AI service."
        )

    elif "ReadTimeout" in error_message or "timed out" in error_message.lower():
        st.error(
            "🤝 Bondhu is taking longer than expected to respond. "
            "Please try again."
        )

    else:
        st.error(
            "🤝 Something went wrong while Bondhu was processing "
            "your question. Please try again."
        )