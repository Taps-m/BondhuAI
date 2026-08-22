import os
import streamlit as st
from google import genai
from dotenv import load_dotenv

from bondhu_orchestrator import answer_question

load_dotenv()


# --------------------------------------------------
# GEMINI CLIENT
# --------------------------------------------------

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
        """
        <p style="
            text-align: center;
            font-size: 20px;
            color: #5f6368;
        ">
            Hi! I'm Bondhu AI 👋<br>
            How can I help you today?
        </p>
        """,
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

    # --------------------------------------------------
    # SAVE USER MESSAGE
    # --------------------------------------------------

    st.session_state.messages.append(
        {
            "role": "user",
            "content": user_input
        }
    )


    # --------------------------------------------------
    # CONVERT CONVERSATION HISTORY
    # --------------------------------------------------

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
- Answer only what the user asked.
- For document-based questions, do not list every category,
  exception, or related detail unless it is necessary to answer
  the question.
- Prefer 2–5 short sentences or bullet points.
- Avoid unnecessary technical language.
- Explain difficult terms in simple Bengali when appropriate.
- If reliable information cannot be found, say so rather than guessing.

IMPORTANT:

- Never mention internal routing.
- Never write "ROUTE:" in the answer.
- Never mention RAG, WEB or GENERAL to the user.
"""
        )


    # --------------------------------------------------
    # GET RESPONSE OBJECT
    # --------------------------------------------------

    response = result.get("response")

    if response is None:

        st.error(
            "Sorry, Bondhu could not generate a response."
        )

        st.stop()


    # --------------------------------------------------
    # GET FINAL ANSWER
    # --------------------------------------------------

    final_answer = result.get(
        "answer",
        ""
    )

    if not final_answer:

        final_answer = response.text


    # --------------------------------------------------
    # DISPLAY ASSISTANT RESPONSE
    # --------------------------------------------------

    with st.chat_message("assistant"):

        st.write(final_answer)


        # --------------------------------------------------
        # DISPLAY WEB SOURCES
        # --------------------------------------------------

        if (
            response.candidates
            and response.candidates[0].grounding_metadata
        ):

            grounding_metadata = (
                response
                .candidates[0]
                .grounding_metadata
            )

            web_chunks = []

            if grounding_metadata.grounding_chunks:

                for chunk in grounding_metadata.grounding_chunks:

                    if chunk.web:

                        web_chunks.append(
                            chunk.web
                        )


            if web_chunks:

                st.markdown("### 🔎 Sources")

                for web in web_chunks:

                    st.markdown(
                        f"- [{web.title}]({web.uri})"
                    )


    # --------------------------------------------------
    # SAVE FINAL ANSWER
    # --------------------------------------------------

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": final_answer
        }
    )