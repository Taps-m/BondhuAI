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
        timeout=60000,
        retry_options=types.HttpRetryOptions(
            attempts=1
        )
    )
)


# ==================================================
# FILE SEARCH STORE
# ==================================================

STORE_NAME = (
    "fileSearchStores/"
    "bondhu-scheme-knowledge-bas-ctfr29lzsi9o"
)


# ==================================================
# ROUTER
# ==================================================

def route_question(question):

    try:

        response = client.models.generate_content(
            model="gemini-3.5-flash",

            contents=f"""
You are Bondhu AI's routing system.

Choose exactly ONE route:

RAG
WEB
GENERAL

RAG:
Use when the question is about information that may exist
inside Bondhu AI's uploaded knowledge base.

Examples:
- Government schemes
- Banking schemes
- Agricultural schemes
- Welfare schemes
- Questions about uploaded documents
- "According to the document..."
- Eligibility, benefits, amounts or rules contained in documents

WEB:
Use when the question requires current information.

Examples:
- Current RBI repo rate
- Latest government announcement
- Current prices
- Current deadlines
- Latest news

GENERAL:
Use for stable general knowledge.

Examples:
- Basic science
- Mathematics
- General explanations
- Greetings
- Casual conversation

IMPORTANT:

Return ONLY:

RAG

or

WEB

or

GENERAL

User question:
{question}
"""
        )

        route = response.text.strip().upper()

        if route not in {"RAG", "WEB", "GENERAL"}:
            return "GENERAL"

        return route

    except Exception as error:

        handle_api_error(error)

        return "GENERAL"


# ==================================================
# RAG ANSWER
# ==================================================

def answer_with_rag(question, system_instruction):

    try:

        rag_instruction = f"""
{system_instruction}

You are answering using Bondhu AI's uploaded knowledge base.

IMPORTANT:

- Use the uploaded documents as the source of truth.
- Answer ONLY the user's question.
- Keep the answer concise.
- Do not summarize unrelated parts of the documents.
- Do not use outside knowledge.
- If the documents do not contain the answer, say:
  "I could not find this information in Bondhu's knowledge base."
"""

        response = client.models.generate_content(
            model="gemini-3.5-flash",

            contents=[
                {
                    "role": "user",
                    "parts": [
                        {
                            "text": question
                        }
                    ]
                }
            ],

            config=types.GenerateContentConfig(
                system_instruction=rag_instruction,

                tools=[
                    types.Tool(
                        file_search=types.FileSearch(
                            file_search_store_names=[
                                STORE_NAME
                            ]
                        )
                    )
                ]
            )
        )

        if response is None:
            return None, []

        retrieved_contexts = []

        if response.candidates:

            metadata = (
                response
                .candidates[0]
                .grounding_metadata
            )

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

        response = client.models.generate_content(
            model="gemini-3.5-flash",

            contents=contents,

            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
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

        response = client.models.generate_content(
            model="gemini-3.5-flash",

            contents=contents,

            config=types.GenerateContentConfig(
                system_instruction=system_instruction
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
    # ROUTE
    # ==================================================

    route = route_question(question)


    # ==================================================
    # RAG
    # ==================================================

    if route == "RAG":

        response, retrieved_contexts = answer_with_rag(
            question,
            system_instruction
        )

        if response is None:

            return {
                "route": "RAG",
                "response": None,
                "answer": "",
                "retrieved_contexts": []
            }

        final_answer = response.text or ""


        # ----------------------------------------------
        # OPTIMIZE RAG ANSWER
        # ----------------------------------------------

        if final_answer:

            try:

                final_answer = optimize_answer(
                    question,
                    final_answer
                )

            except Exception as error:

                handle_api_error(error)


        return {
            "route": "RAG",
            "response": response,
            "answer": final_answer,
            "retrieved_contexts": retrieved_contexts
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
            "answer": response.text or "",
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
        "answer": response.text or "",
        "retrieved_contexts": []
    }