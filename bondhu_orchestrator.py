import os

from google import genai
from google.genai import types
from dotenv import load_dotenv

from error_handler import handle_api_error
from answer_optimizer import optimize_answer


load_dotenv()


# --------------------------------------------------
# GEMINI CLIENT
# --------------------------------------------------

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY"),
    http_options=types.HttpOptions(
        timeout=120000,
        retry_options=types.HttpRetryOptions(
            attempts=2
        )
    )
)


# --------------------------------------------------
# FILE SEARCH STORE
# --------------------------------------------------

STORE_NAME = "fileSearchStores/bondhu-scheme-knowledge-bas-ctfr29lzsi9o"


# --------------------------------------------------
# ROUTER
# --------------------------------------------------

def route_question(question):
    """
    Decide which knowledge source should answer the question.

    RAG     -> Uploaded documents / knowledge base
    WEB     -> Current internet information
    GENERAL -> Stable general knowledge
    """

    try:

        response = client.models.generate_content(
            model="gemini-3.5-flash",

            contents=f"""
You are Bondhu AI's routing system.

Your job is to decide where the user's question should be answered from.

Choose exactly ONE:

RAG

Use RAG when the question is asking about information that may
exist in Bondhu's uploaded documents or knowledge base.

Examples:
- According to the circular...
- As per the guidelines...
- What does the document say...
- How many models are mentioned...
- Questions about government schemes, banking circulars,
  guidelines or documents that Bondhu may have stored.

WEB

Use WEB when the answer requires current, changing or
time-sensitive information from the internet.

Examples:
- Current interest rates
- Current government announcements
- Current weather
- Latest news
- Current prices or deadlines

GENERAL

Use GENERAL when the answer can be answered from stable
general knowledge and does not require Bondhu's documents
or current internet information.

Examples:
- Basic science
- Basic mathematics
- General explanations
- General knowledge

Important:

Return ONLY one of:

RAG
WEB
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

        return None


# --------------------------------------------------
# RAG ANSWER
# --------------------------------------------------

def answer_with_rag(contents, system_instruction):

    try:

        rag_system_instruction = f"""
{system_instruction}

Additional instructions specifically for document-based questions:

- Answer ONLY the specific question the user asked.
- Use the retrieved document information as the source of truth.
- Do not summarize the entire retrieved section.
- Do not list related categories, exceptions, or additional cases
  unless they are necessary to answer the question.
- If the user asks for a limit, amount, date, number, name,
  eligibility criterion, or other specific fact, give that fact
  directly first.
- Prefer 1–3 short sentences or a small number of concise
  bullet points.
- If there are multiple conditions that directly affect the
  requested answer, mention only those relevant conditions.
- Do not add unrelated information.
- Do not use outside knowledge.
- If the retrieved documents do not contain enough information,
  clearly say that the information was not found in the documents.
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


        # --------------------------------------------------
        # COLLECT RETRIEVED CONTEXT
        # --------------------------------------------------

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


# --------------------------------------------------
# WEB ANSWER
# --------------------------------------------------

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


# --------------------------------------------------
# GENERAL ANSWER
# --------------------------------------------------

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


# --------------------------------------------------
# MAIN ORCHESTRATOR
# --------------------------------------------------

def answer_question(
    question,
    conversation_history=None,
    system_instruction=None
):

    if conversation_history is None:
        conversation_history = []


    if system_instruction is None:
        system_instruction = ""


    # --------------------------------------------------
    # BUILD CONVERSATION CONTENT
    # --------------------------------------------------

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


    # --------------------------------------------------
    # ROUTE QUESTION
    # --------------------------------------------------

    route = route_question(question)


    if route is None:

        return {
            "route": "ERROR",
            "response": None,
            "answer": "",
            "retrieved_contexts": []
        }


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


        # --------------------------------------------------
        # ANSWER PRECISION OPTIMIZATION
        # --------------------------------------------------

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