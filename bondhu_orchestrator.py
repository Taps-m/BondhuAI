import os
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

STORE_NAME = "fileSearchStores/bondhu-scheme-knowledge-bas-ctfr29lzsi9o"


def route_question(question):
    response = client.models.generate_content(
        model="gemini-3.5-flash",
        contents=f"""
You are the routing brain for Bondhu AI.

Classify the user's question into exactly ONE category:

RAG = the answer should come from Bondhu's uploaded documents.
WEB = the answer requires current or changing information from the internet.
GENERAL = the answer can be answered from general knowledge.

User question:
{question}

Return ONLY one word:
RAG
WEB
GENERAL
"""
    )

    return response.text.strip().upper()


def answer_with_rag(contents, system_instruction):
    response = client.models.generate_content(
        model="gemini-3.5-flash",
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            tools=[
                types.Tool(
                    file_search=types.FileSearch(
                        file_search_store_names=[STORE_NAME]
                    )
                )
            ]
        )
    )

    return response


def answer_with_web(contents, system_instruction):
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


def answer_with_general(contents, system_instruction):
    response = client.models.generate_content(
        model="gemini-3.5-flash",
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction
        )
    )

    return response


def answer_question(
    question,
    conversation_history=None,
    system_instruction=None
):

    if conversation_history is None:
        conversation_history = []

    if system_instruction is None:
        system_instruction = ""

    # Build conversation context
    contents = conversation_history + [
        {
            "role": "user",
            "parts": [{"text": question}]
        }
    ]

    # Decide which knowledge source to use
    route = route_question(question)

    if route == "RAG":

        response = answer_with_rag(
            contents,
            system_instruction
        )

    elif route == "WEB":

        response = answer_with_web(
            contents,
            system_instruction
        )

    else:

        route = "GENERAL"

        response = answer_with_general(
            contents,
            system_instruction
        )

    return {
        "route": route,
        "response": response,
        "answer": response.text
    }