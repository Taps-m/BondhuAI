import os

from google import genai
from google.genai import types
from dotenv import load_dotenv


# --------------------------------------------------
# ENVIRONMENT
# --------------------------------------------------

load_dotenv()


# --------------------------------------------------
# GEMINI CLIENT
# --------------------------------------------------

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise RuntimeError(
        "GEMINI_API_KEY is not configured."
    )


client = genai.Client(
    api_key=api_key
)


# --------------------------------------------------
# SUPPORTED LANGUAGES
# --------------------------------------------------

LANGUAGE_NAMES = {
    "bn": "Bengali",
    "en": "English",
}


# --------------------------------------------------
# TRANSCRIBE AUDIO
# --------------------------------------------------

def transcribe_audio(audio_bytes, language):
    """
    Convert recorded browser audio into text.

    Browser recording:
        WebM / Opus

    Input:
        audio_bytes -> bytes

    Output:
        Transcribed text -> str
    """

    if not audio_bytes:
        return ""


    # --------------------------------------------------
    # LANGUAGE
    # --------------------------------------------------

    language_name = LANGUAGE_NAMES.get(
        language,
        "Bengali"
    )


    # --------------------------------------------------
    # TRANSCRIPTION PROMPT
    # --------------------------------------------------

    prompt = f"""
You are a speech-to-text transcription engine.

Transcribe the attached audio recording.

Expected spoken language:
{language_name}

IMPORTANT RULES:

1. Return ONLY the words spoken in the recording.
2. Do NOT answer the user's question.
3. Do NOT explain anything.
4. Do NOT summarize.
5. Do NOT add greetings.
6. Do NOT add labels such as "Transcription:".
7. If the user speaks Bengali, write the result in Bengali script.
8. If the user speaks English, write the result in English.
9. Preserve the meaning and wording as closely as possible.
10. If there is no understandable speech, return an empty response.
"""


    # --------------------------------------------------
    # SEND AUDIO TO GEMINI
    # --------------------------------------------------

    response = client.models.generate_content(

        model="gemini-3.5-flash",

        contents=[
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(
                        text=prompt
                    ),
                    types.Part.from_bytes(
                        data=audio_bytes,
                        mime_type="audio/webm"
                    ),
                ],
            )
        ],
    )


    # --------------------------------------------------
    # EXTRACT TEXT
    # --------------------------------------------------

    if response is None:
        raise RuntimeError(
            "Gemini returned no response."
        )


    text = response.text


    if text is None:
        return ""


    return text.strip()