import os

from google import genai
from google.genai import types
from dotenv import load_dotenv


load_dotenv()


STORE_NAME = "fileSearchStores/bondhu-scheme-knowledge-bas-ctfr29lzsi9o"


def test_rag_retrieval():
    """
    Verify that Bondhu's RAG system can retrieve information
    from the uploaded knowledge base.
    """

    client = genai.Client(
        api_key=os.getenv("GEMINI_API_KEY"),
        http_options=types.HttpOptions(
            timeout=30000,
            retry_options=types.HttpRetryOptions(
                attempts=1
            )
        )
    )

    question = "What is the exposure limit for ENBM model?"

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

    # The API should return a response.
    assert response is not None

    # The response should contain candidates.
    assert response.candidates

    # The response should contain text.
    assert response.text

    # Verify that document retrieval actually happened.
    metadata = response.candidates[0].grounding_metadata

    assert metadata is not None
    assert metadata.grounding_chunks

    retrieved_contexts = []

    for chunk in metadata.grounding_chunks:

        if chunk.retrieved_context:
            retrieved_contexts.append(
                chunk.retrieved_context
            )

    # At least one document context must be retrieved.
    assert len(retrieved_contexts) > 0