import os
from html import escape
from urllib.parse import urlsplit

import streamlit as st
from google import genai
from dotenv import load_dotenv
from bondhu_orchestrator import answer_question
from language import select_language
from visitor_counter import unique_visitor_count
from master_voice.voice_component import record_voice
from master_voice.voice import transcribe_audio

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
st.set_page_config(page_title="Bondhu AI", page_icon="🤝", layout="wide", initial_sidebar_state="auto")
with open("style.css", "r", encoding="utf-8-sig") as stylesheet:
    st.markdown(f"<style>{stylesheet.read()}</style>", unsafe_allow_html=True)

for name, default in (("messages", []), ("voice_answer_ready", None), ("voice_session_id", 0),
                      ("input_mode", "text"), ("bondhu_input_method", "⌨️ Type")):
    if name not in st.session_state:
        st.session_state[name] = default


def submit_suggestion(question):
    # Consume this once in the normal question-processing flow.
    st.session_state.bondhu_input_method = "⌨️ Type"
    st.session_state.pending_question = question
    st.session_state.bondhu_question_input = ""


def answer_sources(result):
    """Present only source metadata returned with this answer."""
    sources = []
    response = result.get("response")
    candidates = getattr(response, "candidates", None) or []
    metadata = getattr(candidates[0], "grounding_metadata", None) if candidates else None
    for chunk in getattr(metadata, "grounding_chunks", None) or []:
        source = getattr(chunk, "web", None) or getattr(chunk, "retrieved_context", None)
        if source:
            sources.append(source)
    sources.extend(result.get("retrieved_contexts") or [])
    output, seen = [], set()
    for source in sources:
        title = getattr(source, "title", None) or ""
        uri = getattr(source, "uri", None) or ""
        excerpt = getattr(source, "text", None) or ""
        if not (title or uri or excerpt) or (title, uri, excerpt) in seen:
            continue
        seen.add((title, uri, excerpt))
        output.append({"title": title, "uri": uri, "excerpt": excerpt[:500]})
    return output


def show_sources(message):
    sources = message.get("sources", [])
    if sources:
        label = f"উৎস দেখুন · {len(sources)}" if bengali else f"View sources · {len(sources)}"
        with st.expander(label):
            for index, source in enumerate(sources, 1):
                title = source["title"] or (f"উৎস {index}" if bengali else f"Source {index}")
                uri = source["uri"]
                if urlsplit(uri).scheme in ("http", "https"):
                    st.markdown(
                        f'<a href="{escape(uri, quote=True)}" target="_blank" rel="noopener noreferrer">{escape(title)}</a>',
                        unsafe_allow_html=True
                    )
                else:
                    st.write(title)
                if source["excerpt"]:
                    st.caption(source["excerpt"])
    elif message.get("route") in ("RAG", "WEB"):
        st.caption("এই উত্তরের সাথে উৎসের বিবরণ পাওয়া যায়নি।" if bengali else "Source details were not returned with this answer.")


with st.container(key="bondhu_header"):
    brand_column, language_column, help_column = st.columns([5, 1.5, 1.5], vertical_alignment="center")
    with language_column:
        language = select_language()
    bengali = language == "bn"
    with brand_column:
        tagline = "আপনার প্রশ্ন, সহজ উত্তর" if bengali else "Your questions. Clear answers."
        st.markdown(
            '<div class="bondhu-brand"><div class="bondhu-logo">ব</div>'
            f'<div><div class="bondhu-name">Bondhu AI</div><div class="bondhu-tagline">{tagline}</div></div></div>',
            unsafe_allow_html=True
        )

    with help_column:
        with st.popover("হেল্পলাইন" if bengali else "Helpline", use_container_width=True):
            st.markdown("### সরকারি প্রকল্পের যোগাযোগ" if bengali else "### Scheme contacts")
            contacts = [
                ("কৃষক বন্ধু" if bengali else "Krishak Bandhu", "033-23570021", "+913323570021",
                 "kbhelpdeskwebel@gmail.com", "সকাল ১০টা – বিকেল ৫টা" if bengali else "10 am – 5 pm",
                 "https://krishakbandhu.wb.gov.in/"),
                ("খাদ্য ও রেশন সহায়তা" if bengali else "Food & ration support", "1967", "1967", "", "",
                 "https://food.wb.gov.in/index.aspx"),
                ("বাংলা সহায়তা কেন্দ্র" if bengali else "Bangla Sahayata Kendra", "033-2214-0080", "+913322140080",
                 "bsk@wb.gov.in", "", "https://bsk.wb.gov.in/")
            ]
            for title, phone, dial, email, hours, source in contacts:
                st.markdown(f"**{title}**")
                st.markdown(f'<a class="contact-link" href="tel:{dial}">☎ {phone}</a>', unsafe_allow_html=True)
                if email:
                    st.markdown(f'<a class="contact-link" href="mailto:{email}">{email}</a>', unsafe_allow_html=True)
                if hours:
                    st.caption(hours)
                st.markdown(f"[{'সরকারি তথ্যসূত্র' if bengali else 'Official source'}]({source})")
                st.divider()
            st.caption("তথ্য যাচাই: ৩ অক্টোবর ২০২৬" if bengali else "Contacts checked: 3 October 2026")

SCHEMES = [
    ("কৃষক বন্ধু", "Krishak Bandhu"), ("পিএম-কিসান", "PM-KISAN"),
    ("কন্যাশ্রী", "Kanyashree"), ("রূপশ্রী", "Rupashree"),
    ("খাদ্যসাথী", "Khadya Sathi"), ("স্টুডেন্ট ক্রেডিট কার্ড", "Student Credit Card"),
    ("ভবিষ্যৎ ক্রেডিট কার্ড", "Bhabishyat Credit Card"), ("বাংলার বাড়ি", "Banglar Bari"),
    ("প্রধানমন্ত্রী ফসল বিমা যোজনা", "PM Fasal Bima Yojana"),
    ("পিএম-কুসুম", "PM-KUSUM"), ("সয়েল হেলথ কার্ড", "Soil Health Card")
]

examples = (
    [("সরকারি প্রকল্প", "কৃষক বন্ধু প্রকল্পে কত টাকা পাব?"),
     ("কৃষি সহায়তা", "সয়েল হেলথ কার্ড কী কাজে লাগে?"),
     ("পড়াশোনার সহায়তা", "স্টুডেন্ট ক্রেডিট কার্ডের জন্য কোথায় আবেদন করব?")]
    if bengali else
    [("Government schemes", "How much does Krishak Bandhu provide?"),
     ("Farming support", "What is a Soil Health Card used for?"),
     ("Education support", "Where can I apply for a Student Credit Card?")]
)

with st.sidebar:
    st.markdown("#### প্রধান প্রকল্পসমূহ" if bengali else "#### Major schemes")
    scheme_names = [names[0 if bengali else 1] for names in SCHEMES]
    items = "".join(f'<li><span>›</span>{escape(name)}</li>' for name in scheme_names)
    st.markdown(
        '<section class="schemes-panel" aria-label="' + ("প্রধান প্রকল্পসমূহ" if bengali else "Major schemes") + '">'
        '<div class="schemes-window"><div class="schemes-track">'
        '<ul>' + items + '</ul><ul aria-hidden="true">' + items + '</ul></div></div></section>',
        unsafe_allow_html=True
    )
    with st.expander("সব প্রকল্প দেখুন" if bengali else "View all schemes"):
        for name in scheme_names:
            st.write("• " + name)
    with st.expander("কথা বলবেন যেভাবে" if bengali else "How voice works"):
        st.write("১. মাইক্রোফোন চালু করে প্রশ্ন বলুন।\n\n২. বলা শেষ হলে ২ সেকেন্ড চুপ থাকুন।\n\n৩. পুরো উত্তর দেখার পরে পরের প্রশ্ন বলার জন্য ১০ সেকেন্ড পাবেন।" if bengali else
                 "1. Turn on the microphone and ask.\n\n2. Pause for 2 seconds when finished.\n\n3. After the full answer appears, you have 10 seconds to start your next question.")
    with st.expander("তথ্যের উৎস সম্পর্কে" if bengali else "About the sources"):
        st.write("বন্ধু সংরক্ষিত নথি ও প্রয়োজনে ওয়েবের তথ্য ব্যবহার করে। উত্তরের সাথে উৎস পাওয়া গেলে ‘উৎস দেখুন’ থেকে পড়তে পারবেন।" if bengali else
                 "Bondhu uses stored documents and web information when needed. When sources are returned, open ‘View sources’ beneath the answer.")
    with st.container(key="session_questions"):
        questions = [message["content"] for message in st.session_state.messages if message["role"] == "user"]
        if questions:
            st.markdown("#### এই আলোচনার প্রশ্ন" if bengali else "#### In this conversation")
            for question in questions[-5:]:
                st.caption(question)
    st.markdown('<div class="sidebar-footer">Bondhu AI · 2026 © Tapomoy Das</div>', unsafe_allow_html=True)
    with st.container(key="bondhu_visitor_identity"):
        visitor_count = unique_visitor_count()
    count_text = f"{visitor_count:,}" if visitor_count is not None else "—"
    if bengali:
        count_text = count_text.translate(str.maketrans("0123456789", "০১২৩৪৫৬৭৮৯"))
    st.markdown(
        '<div class="visitor-count"><span>'
        + ("অনন্য দর্শনার্থী" if bengali else "Unique visitors")
        + f'</span><strong>{count_text}</strong></div>', unsafe_allow_html=True
    )

# One stable container keeps additions to chat history from remounting the recorder.
chat_area = st.container(key="bondhu_chat_history")
with chat_area:
    if not st.session_state.messages:
        st.markdown(
            '<div class="bondhu-welcome"><div class="bondhu-eyebrow">'
            + ("সরকারি প্রকল্প · কৃষি · ব্যাংকিং" if bengali else "SCHEMES · FARMING · BANKING")
            + '</div><h1>' + ("জানতে চান? বন্ধুকে বলুন।" if bengali else "A question? Ask Bondhu.")
            + '</h1><p>' + ("কঠিন নিয়ম, সহজ ভাষায়। আপনার প্রশ্ন বলুন বা লিখুন—বন্ধু বুঝিয়ে বলবে।" if bengali else
              "Make sense of the details. Speak or type your question—Bondhu will explain it simply.")
            + '</p></div>', unsafe_allow_html=True
        )
        if st.session_state.bondhu_input_method == "⌨️ Type":
            st.markdown('<div class="suggestions-label">' + ("অথবা এই প্রশ্ন দিয়ে শুরু করুন" if bengali else "Or start with a question") + '</div>', unsafe_allow_html=True)
            with st.container(key="bondhu_suggestions"):
                columns = st.columns(3)
                for index, ((title, question), column) in enumerate(zip(examples, columns)):
                    with column:
                        st.caption(title)
                        st.button(question + " →", key=f"example_{index}", on_click=submit_suggestion,
                                  args=(question,), use_container_width=True)
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.caption(("আপনি" if bengali else "You") if message["role"] == "user" else "Bondhu AI")
            st.write(message["content"])
            if message["role"] == "assistant":
                show_sources(message)
    if st.session_state.voice_answer_ready:
        st.markdown(f'<span id="bondhu-answer-{st.session_state.voice_answer_ready}"></span>', unsafe_allow_html=True)

user_input = None
with st.container(key="bondhu_composer"):
    input_mode = st.radio(
        "প্রশ্ন করার মাধ্যম" if bengali else "Question input",
        ["⌨️ Type", "🎙️ Voice"], horizontal=True, label_visibility="collapsed",
        format_func=lambda mode: ({"⌨️ Type": "⌨️ লিখে বলুন", "🎙️ Voice": "🎙️ কথা বলুন"}[mode]
                                 if bengali else {"⌨️ Type": "⌨️ Type", "🎙️ Voice": "🎙️ Speak"}[mode]),
        key="bondhu_input_method"
    )
    st.session_state.input_mode = "voice" if input_mode == "🎙️ Voice" else "text"
    if st.session_state.input_mode == "text":
        user_input = st.chat_input("আপনার প্রশ্ন লিখুন…" if bengali else "Ask your question…", key="bondhu_question_input")
        user_input = st.session_state.pop("pending_question", None) or user_input
        st.caption("একবারে একটি প্রশ্ন করুন। পরের প্রশ্নও এখানেই করতে পারবেন।" if bengali else "Ask one question at a time. You can follow up right here.")
    else:
        audio = record_voice(answer_ready=st.session_state.voice_answer_ready, language=language,
                             session_id=st.session_state.voice_session_id)
        if audio:
            with st.spinner("আপনার কথা বোঝার চেষ্টা করছি…" if bengali else "Transcribing your question…"):
                try:
                    user_input = transcribe_audio(audio_bytes=audio, language=language)
                except Exception as error:
                    st.error("কথাটি বোঝা যায়নি। আবার চেষ্টা করুন অথবা লিখে পাঠান।" if bengali else "I couldn't understand the recording. Please try again or type your question.")
                    user_input = None


# ==================================================
# PROCESS USER QUESTION
# ==================================================

if user_input:

    user_input = user_input.strip()


    if not user_input:

        st.stop()


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
    # CONVERSATION HISTORY FOR GEMINI
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
    # BONDHU SYSTEM INSTRUCTION
    # --------------------------------------------------

    system_instruction = f"""
You are Bondhu AI, a friendly, helpful and trustworthy AI assistant.

Your name is Bondhu AI. "Bondhu" means friend in Bengali.

The user's selected language is: {language}

LANGUAGE BEHAVIOUR:

- Respond in the user's selected language.
- If the selected language is unsupported, respond in BOTH
  English and Bengali.
- Maintain the selected language throughout the conversation.
- Do not unnecessarily switch languages.

Bondhu is primarily designed to help rural people of Bengal,
especially farmers and people who need information about government
schemes, agricultural support, banking services and public welfare.

CORE BEHAVIOUR:

- Understand the user's actual intent before answering.
- Answer directly and simply.
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


    # --------------------------------------------------
    # ASK BONDHU
    # --------------------------------------------------

    with st.spinner(
        "বন্ধু উত্তর তৈরি করছে…" if bengali else "Bondhu is preparing your answer…"
    ):

        try:

            result = answer_question(
                question=user_input,

                conversation_history=gemini_messages[:-1],

                system_instruction=system_instruction
            )

        except Exception as error:

            st.error(
                "DEBUG: Bondhu processing failed"
            )

            st.exception(error)

            st.stop()


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

    response = result.get(
        "response"
    )


    # --------------------------------------------------
    # GET FINAL ANSWER
    # --------------------------------------------------

    final_answer = result.get(
        "answer",
        ""
    )


    if (
        not final_answer
        and response is not None
    ):

        final_answer = response.text


    # --------------------------------------------------
    # NO ANSWER
    # --------------------------------------------------

    if not final_answer:

        st.error(
            "Sorry, Bondhu could not generate a response."
        )

        st.stop()


    sources = answer_sources(result)

    # --------------------------------------------------
    # SAVE ASSISTANT ANSWER
    # --------------------------------------------------

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": final_answer,
            "sources": sources,
            "route": result.get("route")
        }
    )


    # The next render displays the saved answer and sources before the marker.
    if st.session_state.input_mode == "voice":
        st.session_state.voice_answer_ready = st.session_state.voice_recording_id
    st.rerun()
