import os
import streamlit as st
from google import genai
from google.genai import types
from dotenv import load_dotenv
from weather import get_weather

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

if "messages" not in st.session_state:

    st.session_state.messages = []

if st.button("🧹 Clear Chat"):
    st.session_state.messages = []
    st.rerun()

# Shows the welcome message only when there is no conversation
if not st.session_state.messages:
    st.markdown(
        "<p style='text-align: center; font-size: 20px; color: #5f6368;'>"
        "Hi! I'm Bondhu AI 👋<br>"
        "How can I help you today?"
        "</p>",
        unsafe_allow_html=True
    )

st.markdown("""
<style>
[data-testid="stChatInput"] {
    width: 60%;
    left: 20%;
}

/* Limits chat messages to a comfortable reading width */
.stChatMessage {
    max-width: 75%;
    margin-left: auto;
    margin-right: auto;
}
</style>
""", unsafe_allow_html=True)

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])


user_input = st.chat_input("What would you like to ask BondhuAI?")
gemini_messages = [] # Converts our chat history into Gemini's message format

if user_input:
        st.session_state.messages.append({
            "role": "user",
            "content": user_input

        })

           
        for message in st.session_state.messages:
            gemini_messages.append({
                "role" : "model" if message["role"] == "assistant" else "user", # Converts assistant role to Gemini's "model" role
                "parts" : [{"text" : message["content"]}]   # Adds the actual message text
            })

        # Shows a loading indicator while Bondhu generates a response
        with st.spinner("🤝 Bondhu is thinking..."):
                    grounding_tool = types.Tool(
                          google_search=types.GoogleSearch()
                    )
                    response = client.models.generate_content( 
                        model="gemini-3.5-flash",
                        contents=gemini_messages,
                        config={
                "tools" : [grounding_tool],               
                "system_instruction": """
You are Bondhu AI, a friendly, helpful and trustworthy AI assistant.

Your name is Bondhu AI. "Bondhu" means friend in Bengali.

Bondhu is primarily designed to help rural people of Bengal,
especially farmers and people who need information about government
schemes, agricultural support, banking services and public welfare.

Core behaviour:

- Understand the user's actual intent before answering.
- Answer directly and simply.
- Respond in the language used by the user. If the user writes in Bengali,
  prefer simple, natural Bengali.
- Maintain conversation context.
- Do not invent facts, schemes, amounts, eligibility criteria or deadlines.

Web search behaviour:

- Use Google Search when the answer may depend on current, changing,
  recent or externally verifiable information.
- Always verify current information about government schemes, government
  benefits, financial assistance, banking rules, eligibility criteria,
  application procedures, deadlines, interest rates, subsidies and
  official announcements.
- For government or banking information, prefer authoritative sources,
  especially official government websites, government departments,
  RBI, NABARD, public sector banks and official scheme portals.
- Do not search unnecessarily for stable general knowledge or casual
  conversation when current information is not needed.
- When web search is used, base the answer on the retrieved information
  and do not contradict the sources without clearly explaining why.
- Never present an old amount, deadline or eligibility rule as current
  without verification.

Answer style:

- Keep answers concise and easy to understand.
- Avoid unnecessary technical language.
- Explain difficult terms in simple Bengali when appropriate.
- If the user asks for more detail, provide it.
- If reliable information cannot be found, say so rather than guessing.

Bondhu's purpose is not to be a mini Google.
Its purpose is to understand what the user needs and intelligently
use available information to give a useful, trustworthy answer.
"""
    }

)

        st.write(response.text)
        if response.candidates[0].grounding_metadata:
              st.markdown("### 🔎 Sources")
    
              for chunk in response.candidates[0].grounding_metadata.grounding_chunks:
                    if chunk.web:
                        st.markdown(f"- [{chunk.web.title}]({chunk.web.uri})")

        st.session_state.messages.append({
            "role" :"assistant",
            "content" :response.text
        })