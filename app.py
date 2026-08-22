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
# PAGE CONFIG
# --------------------------------------------------

st.set_page_config(
    page_title="Bondhu AI",
    page_icon="🤝",
    layout="centered"
)


# --------------------------------------------------
# LOAD EXTERNAL CSS
# --------------------------------------------------

with open("style.css", "r", encoding="utf-8") as f:
    st.markdown(
        f"<style>{f.read()}</style>",
        unsafe_allow_html=True
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
            margin-top: 30px;
        ">
        Hi! I'm Bondhu AI 👋<br>
        How can I help you today?
        </p>
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
    # CONVERT CONVERSATION HISTORY FOR GEMINI
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

CORE BEHAVIOUR:

- Understand the user's actual intent before answering.
- Answer directly and simply.
- Respond in the language used by the user.
- Maintain conversation context.
- Do not invent facts, schemes, amounts, eligibility criteria or deadlines.

ANSWER STYLE:

- Keep answers concise and easy to understand.
- Answer only what the user asked.
- Prefer 2–5 short sentences or bullet points.
- Avoid unnecessary technical language.
- Explain difficult terms in simple Bengali when appropriate.
- If reliable information cannot be found, say so rather than guessing.

GREETING BEHAVIOUR:

If the user simply says:
- Hi
- Hello
- Hey
- Good morning
- Good evening
- Namaste

respond naturally and briefly.

Do not provide information about schemes, farming, banking,
or other topics unless the user asks for them.

Do not repeat the full Bondhu AI introduction every time.

For example:

User: Hi

Bondhu:
Hi! 👋 I'm Bondhu AI.
How can I help you today?

DOCUMENT QUESTIONS:

When answering from Bondhu's knowledge base:

- Use the retrieved documents as the source of truth.
- Answer only the specific question.
- Do not provide unnecessary related information.
- Do not use outside knowledge.

CURRENT INFORMATION:

When current information is required, use web search.

GENERAL QUESTIONS:

For stable general knowledge, answer normally and simply.
"""
        )


    # --------------------------------------------------
    # SAFETY CHECK
    # --------------------------------------------------

    if result is None:

        st.error(
            "Sorry, Bondhu could not generate a response."
        )

        st.stop()


    # --------------------------------------------------
    # GET RESPONSE
    # --------------------------------------------------

    response = result.get("response")


    # --------------------------------------------------
    # GET FINAL ANSWER
    # --------------------------------------------------

    final_answer = result.get(
        "answer",
        ""
    )


    if not final_answer and response is not None:

        final_answer = response.text


    # --------------------------------------------------
    # IF NO ANSWER
    # --------------------------------------------------

    if not final_answer:

        st.error(
            "Sorry, Bondhu could not generate a response."
        )

        st.stop()


    # --------------------------------------------------
    # DISPLAY ANSWER
    # --------------------------------------------------

    with st.chat_message("assistant"):

        st.write(final_answer)


        # --------------------------------------------------
        # DISPLAY WEB SOURCES
        # --------------------------------------------------

        if response is not None:

            if (
                response.candidates
                and response.candidates[0].grounding_metadata
            ):

                grounding_metadata = (
                    response
                    .candidates[0]
                    .grounding_metadata
                )


                if grounding_metadata.grounding_chunks:

                    web_sources = []

                    for chunk in grounding_metadata.grounding_chunks:

                        if chunk.web:

                            title = chunk.web.title
                            uri = chunk.web.uri

                            if uri:

                                web_sources.append(
                                    (title, uri)
                                )


                    if web_sources:

                        st.markdown(
                            "### 🔎 Sources"
                        )

                        for title, uri in web_sources:

                            st.markdown(
                                f"- [{title}]({uri})"
                            )


    # --------------------------------------------------
    # SAVE ASSISTANT ANSWER
    # --------------------------------------------------

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": final_answer
        }
    )


# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.markdown(
    '<div class="bondhu-footer">© Tapomoy Das</div>',
    unsafe_allow_html=True
)