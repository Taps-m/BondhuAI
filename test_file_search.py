import os
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

store_name = "fileSearchStores/bondhu-scheme-knowledge-bas-ctfr29lzsi9o"

response = client.models.generate_content(
    model="gemini-3.5-flash",
    contents="According to the PM-KISAN Operational Guidelines, who is eligible to receive benefits under the scheme?",
    config=types.GenerateContentConfig(
        tools=[
            types.Tool(
                file_search=types.FileSearch(
                    file_search_store_names=[store_name]
                )
            )
        ]
    )
)

print("\nANSWER:\n")
print(response.text)