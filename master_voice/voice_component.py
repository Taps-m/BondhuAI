import os
import base64

import streamlit as st

import streamlit.components.v1 as components


# --------------------------------------------------
# COMPONENT PATH
# --------------------------------------------------

_COMPONENT_PATH = os.path.join(
    os.path.dirname(__file__),
    "voice_component"
)


# --------------------------------------------------
# DECLARE STREAMLIT COMPONENT
# --------------------------------------------------

bondhu_voice = components.declare_component(
    "bondhu_voice",
    path=_COMPONENT_PATH
)


# --------------------------------------------------
# RECORD VOICE
# --------------------------------------------------

def record_voice(answer_ready=None, language="en", session_id=0):
    """
    Run the Bondhu browser voice component.

    Browser handles:
        - microphone access
        - recording
        - speech detection
        - silence detection
        - 10-second next-question timeout

    Python handles:
        - receiving Base64 audio
        - converting Base64 to bytes
        - informing browser when Bondhu's answer
          is ready for display, using a recording ID
        - acknowledging display and ignoring retained audio
    """

    audio_base64 = bondhu_voice(
        answer_ready=answer_ready,
        language=language,
        key=f"bondhu_voice_recorder_{session_id}"
    )


    if not isinstance(audio_base64, dict):
        return None

    event = audio_base64
    recording_id = event.get("id")
    if event.get("type") == "answer_displayed":
        if recording_id == answer_ready:
            st.session_state.voice_answer_ready = None
        return None
    if event.get("type") != "audio" or not recording_id:
        return None
    if st.session_state.get("voice_recording_id") == recording_id:
        return None
    try:
        audio_bytes = base64.b64decode(event["audio"], validate=True)
    except (KeyError, ValueError, TypeError, base64.binascii.Error):
        return None
    st.session_state.voice_recording_id = recording_id
    return audio_bytes
