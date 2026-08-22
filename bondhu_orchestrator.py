import os

from google import genai
from google.genai import types
from dotenv import load_dotenv

from error_handler import handle_api_error
from answer_optimizer import optimize_answer


load_dotenv()


# ==================================================
# GEMINI CLIENT
# ==================================================

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY"),
    http_options=types.HttpOptions(
        timeout=120000,
        retry_options=types.HttpRetryOptions(
            attempts=2
        )
    )
)


# ==================================================
# FILE SEARCH STORE
# ==================================================

STORE_NAME = "fileSearchStores/bondhu-scheme-knowledge-bas-ctfr29lzsi9o"


# ==================================================
# ROUTER
# ==================================================

def route_question(question):

    try:

        response = client.models.generate_content(
            model="gemini-3.5-flash",

            contents=f"""
You are the ROUTER of Bondhu AI.

Your ONLY job is to classify the user's question.

Return EXACTLY ONE WORD:

RAG
WEB
GENERAL

Do NOT explain your choice.
Do NOT return any other text.

--------------------------------------------------
RAG
--------------------------------------------------

Choose RAG when the user is asking about information
that should come from Bondhu AI's uploaded documents,
government scheme documents, banking circulars,
guidelines, or knowledge base.

Examples:

"According to the PM-KISAN guidelines..."
"What does the circular say?"
"Who is eligible according to the document?"
"How much loan is allowed according to the circular?"
"What are the conditions mentioned in the guidelines?"

If the question could reasonably be answered from
Bondhu's stored documents, prefer RAG.

--------------------------------------------------
WEB
--------------------------------------------------

Choose WEB ONLY when the user needs CURRENT or
TIME-SENSITIVE information.

Examples:

"What's the weather today?"
"What is the current RBI repo rate?"
"What are today's gold prices?"
"What is the latest government announcement?"
"Who is the current Chief Minister?"
"What is the latest news?"

--------------------------------------------------
GENERAL
--------------------------------------------------

Choose GENERAL for:

- Greetings
- Casual conversation
- Thanks
- Good morning / good evening
- "How are you?"
- "What can you do?"
- General explanations
- Stable general knowledge
- Basic mathematics
- Basic science
- Writing help
- Translation
- Brainstorming
- Questions that do not require documents or current web data

Examples:

"Hi"
"Hello"
"How are you?"
"Who are you?"
"Tell me a joke"
"What is photosynthesis?"
"Explain inflation"
"Help me write a letter"

IMPORTANT:

A greeting or casual conversation MUST ALWAYS be GENERAL.

--------------------------------------------------
USER QUESTION
--------------------------------------------------

{question}

--------------------------------------------------
RETURN ONLY:

RAG
WEB
GENERAL
--------------------------------------------------
"""
        )

        route = response.text.strip().upper()

        if "RAG" in route and "WEB" not in route and "GENERAL" not in route:
            return "RAG"

        if "WEB" in route and "RAG" not in route and "GENERAL" not in route:
            return "WEB"

        if "GENERAL" in route and "RAG" not in route and "WEB" not in route:
            return "GENERAL"

        return "GENERAL"

    except Exception as error:

        handle_api_error(error)

        return "GENERAL"


# ==================================================
# RAG ANSWER
# ==================================================

def answer_with_rag(contents, system_instruction):

    try:

        rag_system_instruction = f"""
{system_instruction}

You are Bondhu AI answering from its official
knowledge-base documents.

STRICT RULES:

1. Answer ONLY the user's actual question.

2. Use the retrieved documents as the source of truth.

3. Do NOT use outside knowledge.

4. Do NOT invent information.

5. If the document does not contain the answer,
say:

"I could not find this information in my
available documents."

6. If the user asks for a number, amount, date,
eligibility condition, name, limit or other
specific fact, give that fact FIRST.

7. Keep answers concise and easy to understand.

8. Prefer 1–4 short sentences or concise bullets.

9. Do not unnecessarily summarize the entire document.

10. Do not add unrelated information.

11. Never mention internal routing.
12. Never mention RAG, WEB or GENERAL.
"""

        response = client.models.generate_content(
            model="gemini-3.5-flash",

            contents=contents,

            config=types.GenerateContentConfig(
                system_instruction=rag_system_instruction,

                tools=[
                    types.Tool(
                        file_search=types.FileSearch(
                            file_search_store_names=[STORE_NAME]
                        )
                    )
                ]
            )
        )

        retrieved_contexts = []

        if response.candidates:

            metadata = response.candidates[0].grounding_metadata

            if metadata and metadata.grounding_chunks:

                for chunk in metadata.grounding_chunks:

                    if chunk.retrieved_context:

                        retrieved_contexts.append(
                            chunk.retrieved_context
                        )

        return response, retrieved_contexts

    except Exception as error:

        handle_api_error(error)

        return None, []


# ==================================================
# WEB ANSWER
# ==================================================

def answer_with_web(contents, system_instruction):

    try:

        grounding_tool = types.Tool(
            google_search=types.GoogleSearch()
        )

        web_system_instruction = f"""
{system_instruction}

You are Bondhu AI.

Answer the user's question using current web
information when required.

Rules:

- Give the direct answer first.
- Keep the response concise.
- Use current information.
- Do not invent facts.
- If current information cannot be verified,
say so clearly.
- Never mention internal routing.
- Never mention RAG, WEB or GENERAL.
- Never write "ROUTE:".
"""

        response = client.models.generate_content(
            model="gemini-3.5-flash",

            contents=contents,

            config=types.GenerateContentConfig(
                system_instruction=web_system_instruction,
                tools=[grounding_tool]
            )
        )

        return response

    except Exception as error:

        handle_api_error(error)

        return None


# ==================================================
# GENERAL ANSWER
# ==================================================

def answer_with_general(contents, system_instruction):

    try:

        general_system_instruction = f"""
{system_instruction}

You are Bondhu AI.

You are a friendly assistant for people of Rural Bengal.

IMPORTANT:

- Answer naturally and conversationally.
- Answer ONLY what the user asks.
- Never mention routing.
- Never mention RAG, WEB or GENERAL.
- Never write "ROUTE:".
- Never explain your internal systems.
- Keep simple questions very short.
- Do not unnecessarily introduce yourself.
- Do not list your services unless the user asks.
- Do not explain that Bondhu means friend unless asked.
- Respond in the user's language.

GREETING RULE:

If the user says only:

Hi
Hello
Hey
Good morning
Good afternoon
Good evening

respond with ONLY a short greeting.

For example:

"Hi! I'm Bondhu AI 👋 How can I help you today?"

Do NOT add:
- a description of Bondhu AI
- a list of services
- an explanation of the name Bondhu
- Bengali instructions
- unnecessary introductory text

For "How are you?", respond briefly and naturally.

For "What can you do?", explain your capabilities briefly.
"""

        response = client.models.generate_content(
            model="gemini-3.5-flash",

            contents=contents,

            config=types.GenerateContentConfig(
                system_instruction=general_system_instruction
            )
        )

        return response

    except Exception as error:

        handle_api_error(error)

        return None


# ==================================================
# MAIN ORCHESTRATOR
# ==================================================

def answer_question(
    question,
    conversation_history=None,
    system_instruction=None
):

    if conversation_history is None:
        conversation_history = []

    if system_instruction is None:
        system_instruction = ""


    # ==================================================
    # DIRECT GREETING HANDLING
    # ==================================================

    normalized_question = question.strip().lower()

    greetings = {
        "hi",
        "hello",
        "hey",
        "good morning",
        "good afternoon",
        "good evening"
    }

    if normalized_question in greetings:

        return {
            "route": "GENERAL",
            "response": None,
            "answer": "Hi! I'm Bondhu AI 👋 How can I help you today?",
            "retrieved_contexts": []
        }


    # ==================================================
    # BUILD CONVERSATION
    # ==================================================

    contents = conversation_history + [
        {
            "role": "user",
            "parts": [
                {
                    "text": question
                }
            ]
        }
    ]


    # ==================================================
    # ROUTE
    # ==================================================

    route = route_question(question)


    # ==================================================
    # RAG
    # ==================================================

    if route == "RAG":

        rag_contents = [
            {
                "role": "user",
                "parts": [
                    {
                        "text": question
                    }
                ]
            }
        ]

        response, retrieved_contexts = answer_with_rag(
            rag_contents,
            system_instruction
        )

        if response is None:

            return {
                "route": "RAG",
                "response": None,
                "answer": "",
                "retrieved_contexts": []
            }


        try:

            optimized_answer = optimize_answer(
                question,
                response.text
            )

        except Exception as error:

            handle_api_error(error)

            optimized_answer = response.text


        return {
            "route": "RAG",
            "response": response,
            "answer": optimized_answer,
            "retrieved_contexts": retrieved_contexts
        }


    # ==================================================
    # WEB
    # ==================================================

    if route == "WEB":

        response = answer_with_web(
            contents,
            system_instruction
        )

        if response is None:

            return {
                "route": "WEB",
                "response": None,
                "answer": "",
                "retrieved_contexts": []
            }

        return {
            "route": "WEB",
            "response": response,
            "answer": response.text,
            "retrieved_contexts": []
        }


    # ==================================================
    # GENERAL
    # ==================================================

    response = answer_with_general(
        contents,
        system_instruction
    )

    if response is None:

        return {
            "route": "GENERAL",
            "response": None,
            "answer": "",
            "retrieved_contexts": []
        }

    return {
        "route": "GENERAL",
        "response": response,
        "answer": response.text,
        "retrieved_contexts": []
    }