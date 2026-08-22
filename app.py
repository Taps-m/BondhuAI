import os
import streamlit as st
from google import genai
from dotenv import load_dotenv
from bondhu_orchestrator import answer_question

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


# --------------------------------------------------
# SESSION MEMORY
# --------------------------------------------------

if "messages" not in st.session_state:
    st.session_state.messages = []


# --------------------------------------------------
# CLEAR CHAT
# --------------------------------------------------

if st.button("🧹 Clear Chat"):
    st.session_state.messages = []
    st.rerun()


# --------------------------------------------------
# WELCOME MESSAGE
# --------------------------------------------------

if not st.session_state.messages:
    st.markdown(
        "<p style='text-align: center; font-size: 20px; color: #5f6368;'>"
        "Hi! I'm Bondhu AI 👋<br>"
        "How can I help you today?"
        "</p>",
        unsafe_allow_html=True
    )


# --------------------------------------------------
# CHAT UI STYLING
# --------------------------------------------------

st.markdown(
    """
    <style>
    [data-testid="stChatInput"] {
        width: 60%;
        left: 20%;
    }

    .stChatMessage {
        max-width: 75%;
        margin-left: auto;
        margin-right: auto;
    }
    </style>
    """,
    unsafe_allow_html=True
)


# --------------------------------------------------
# DISPLAY CHAT HISTORY
# --------------------------------------------------

for message in st.session_state.messages:

    with st.chat_message(message["role"]):
        st.write(message["content"])


# --------------------------------------------------
# USER INPUT
# --------------------------------------------------

user_input = st.chat_input(
    "What would you like to ask BondhuAI?"
)


# --------------------------------------------------
# PROCESS QUESTION
# --------------------------------------------------

if user_input:

    # Save user's message
    st.session_state.messages.append(
        {
            "role": "user",
            "content": user_input
        }
    )


    # Convert conversation history to Gemini format
    gemini_messages = []

    for message in st.session_state.messages:

        gemini_messages.append(
            {
                "role": (
                    "model"
                    if message["role"] == "assistant"
                    else "user"
                ),
                "parts": [
                    {
                        "text": message["content"]
                    }
                ]
            }
        )


    # --------------------------------------------------
    # ASK BONDHU
    # --------------------------------------------------

    with st.spinner("🤝 Bondhu is thinking..."):

        result = answer_question(
            question=user_input,
            conversation_history=gemini_messages[:-1],
            system_instruction="""
You are Bondhu AI, a friendly, helpful and trustworthy AI assistant.

Your name is Bondhu AI. "Bondhu" means friend in Bengali.

Bondhu is primarily designed to help rural people of Bengal,
especially farmers and people who need information about government
schemes, agricultural support, banking services and public welfare.

Core behaviour:

- Understand the user's actual intent before answering.
- Answer directly and simply.
- Respond in the language used by the user.
- Maintain conversation context.
- Do not invent facts, schemes, amounts, eligibility criteria or deadlines.

Answer style:

- Keep answers concise and easy to understand.
- Avoid unnecessary technical language.
- Explain difficult terms in simple Bengali when appropriate.
- If reliable information cannot be found, say so rather than guessing.
"""
        )


    # --------------------------------------------------
    # ROUTE DIAGNOSTIC
    # --------------------------------------------------

    st.write("ROUTE:", result["route"])


    # --------------------------------------------------
    # GET RESPONSE
    # --------------------------------------------------

    response = result["response"]


    if response is None:
        st.stop()


    # --------------------------------------------------
    # DISPLAY ANSWER
    # --------------------------------------------------

    st.write(response.text)


    # --------------------------------------------------
    # DISPLAY WEB SOURCES
    # --------------------------------------------------

    if (
        response.candidates
        and response.candidates[0].grounding_metadata
    ):

        st.markdown("### 🔎 Sources")

        for chunk in (
            response
            .candidates[0]
            .grounding_metadata
            .grounding_chunks
        ):

            if chunk.web:

                st.markdown(
                    f"- [{chunk.web.title}]({chunk.web.uri})"
                )


    # --------------------------------------------------
    # SAVE ASSISTANT RESPONSE
    # --------------------------------------------------

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": response.text
        }
    )