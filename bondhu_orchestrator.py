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


def answer_with_rag(question):
    response = client.models.generate_content(
        model="gemini-3.5-flash",
        contents=question,
        config=types.GenerateContentConfig(
            tools=[
                types.Tool(
                    file_search=types.FileSearch(
                        file_search_store_names=[STORE_NAME]
                    )
                )
            ]
        )
    )

    return response.text


def answer_with_web(question):
    grounding_tool = types.Tool(
        google_search=types.GoogleSearch()
    )

    response = client.models.generate_content(
        model="gemini-3.5-flash",
        contents=question,
        config=types.GenerateContentConfig(
            tools=[grounding_tool]
        )
    )

    return response.text


def answer_with_general(question):
    response = client.models.generate_content(
        model="gemini-3.5-flash",
        contents=question
    )

    return response.text


question = input("Ask Bondhu: ")

route = route_question(question)

print("\nRoute selected:", route)

if route == "RAG":
    answer = answer_with_rag(question)

elif route == "WEB":
    answer = answer_with_web(question)

else:
    answer = answer_with_general(question)

print("\nBONDHU ANSWER:\n")
print(answer)