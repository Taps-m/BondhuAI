import streamlit as st


SUPPORTED_LANGUAGES = {
    "বাংলা": "bn",
    "English": "en",
}


def select_language():
    """Open in Bengali and keep a language switch available on every render."""
    if st.session_state.get("language") not in SUPPORTED_LANGUAGES.values():
        st.session_state.language = "bn"

    language_names = list(SUPPORTED_LANGUAGES)
    selected_language = st.selectbox(
        "ভাষা / Language",
        language_names,
        index=list(SUPPORTED_LANGUAGES.values()).index(st.session_state.language),
        key="bondhu_language",
    )
    st.session_state.language = SUPPORTED_LANGUAGES[selected_language]
    return st.session_state.language
