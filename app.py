import os
import streamlit as st
from google import genai
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
                    response = client.models.generate_content( 
                        model="gemini-3.5-flash",
                        contents=gemini_messages,
                        config={
                "system_instruction": """
You are Bondhu AI, a friendly, helpful and intelligent AI assistant.

Your name is Bondhu AI. "Bondhu" means friend in Bengali.

Behave like a knowledgeable and trustworthy friend:
- Be clear and accurate.
- Be concise by default.
- Give detailed explanations when the user asks or when they are genuinely useful.
- Maintain the context of the conversation.
- Adapt your tone to the user's question.
- If you are uncertain, say so rather than inventing information.
- Do not unnecessarily repeat information.
"""
    }

)

        st.write(response.text)

        st.session_state.messages.append({
            "role" :"assistant",
            "content" :response.text
        })