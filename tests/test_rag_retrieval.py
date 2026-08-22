import os

from google import genai
from google.genai import types
from dotenv import load_dotenv


load_dotenv()


client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY"),
    http_options=types.HttpOptions(
        timeout=30000,
        retry_options=types.HttpRetryOptions(
            attempts=1
        )
    )
)


STORE_NAME = "fileSearchStores/bondhu-scheme-knowledge-bas-ctfr29lzsi9o"


question = input("Ask a question about Bondhu's knowledge base: ").strip()

if not question:
    print("No question entered.")
    raise SystemExit


try:

    response = client.models.generate_content(
        model="gemini-3.5-flash",
        contents=question,
        config=types.GenerateContentConfig(
            system_instruction=(
                "Answer using only information retrieved from "
                "Bondhu's uploaded documents. "
                "Do not use general knowledge. "
                "If the documents do not contain enough information, "
                "say that the information was not found in the documents."
            ),
            tools=[
                types.Tool(
                    file_search=types.FileSearch(
                        file_search_store_names=[STORE_NAME]
                    )
                )
            ]
        )
    )

except Exception as error:

    print("\n========== RAG ERROR ==========\n")
    print(type(error).__name__)
    print(error)
    raise SystemExit


print("\n========== ANSWER ==========\n")
print(response.text)


print("\n========== RETRIEVED CONTEXT ==========\n")


retrieved_contexts = []


if response.candidates:

    metadata = response.candidates[0].grounding_metadata

    if metadata and metadata.grounding_chunks:

        for chunk in metadata.grounding_chunks:

            if chunk.retrieved_context:

                context = chunk.retrieved_context
                retrieved_contexts.append(context)

                print("DOCUMENT :", context.title)
                print("PAGE     :", context.page_number)
                print("STORE    :", context.file_search_store)
                print("URI      :", context.uri)

                print("\nTEXT:")
                print(context.text)

                print("\n" + "-" * 60)


print("\n========== RAG RESULT ==========\n")


if retrieved_contexts:

    print("RAG SUCCESS")
    print("Retrieved contexts:", len(retrieved_contexts))

else:

    print("RAG FAILED")
    print("No document context was retrieved.")