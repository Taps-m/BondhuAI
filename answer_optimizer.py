import os

from google import genai
from google.genai import types
from dotenv import load_dotenv


load_dotenv()


client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY"),
    http_options=types.HttpOptions(
        timeout=120000,
        retry_options=types.HttpRetryOptions(
            attempts=2
        )
    )
)


def optimize_answer(question, answer):
    """
    Improve answer precision using a single Gemini API call.

    The optimizer:
    - Determines the question scope internally.
    - Answers only what was asked.
    - Preserves factual accuracy.
    - Does not retrieve additional information.
    - Does not add new facts.
    """

    try:

        response = client.models.generate_content(
            model="gemini-3.5-flash",

            contents=f"""
USER QUESTION:
{question}

ORIGINAL ANSWER:
{answer}

Your task is to produce the FINAL answer.

First, internally determine whether the question is:

SINGLE
The user wants one direct fact, value, limit, amount, date,
number, name, definition, purpose, or general answer.

SPECIFIC
The user asks about one particular category, case, sector,
condition, type, or situation.

MULTIPLE
The user explicitly asks for multiple values, categories,
cases, conditions, reasons, models, differences, or a list.

Do not output this classification.

Then follow these rules strictly.

GENERAL RULES:

1. Answer ONLY the user's question.

2. Use ONLY information contained in the original answer.

3. Never invent information.

4. Never change numbers, dates, names, amounts, limits,
   percentages, or eligibility criteria.

5. Do not add outside knowledge.

6. Remove unrelated information.

7. Do not summarize the whole original answer.

8. Return only the final answer.

SINGLE QUESTION RULES:

If the question asks for ONE fact or value:

- Return ONE direct answer.
- Do NOT return a list.
- Do NOT mention other categories or cases.
- Do NOT mention exceptions that apply to other categories.
- Do NOT append additional qualifications from other cases.
- If the original answer contains several categories, select
  the MAIN or PRIMARY case that directly answers the general
  question.
- Unless the question explicitly names a category, sector,
  borrower type, case, or condition, do not select or mention
  a category-specific alternative.
- If multiple primary cases contain the same requested value,
  state the value only once.
- Keep the answer to one sentence whenever possible.

SPECIFIC QUESTION RULES:

If the question explicitly identifies a category, case, sector,
condition, type, or situation:

- Answer only that specific case.
- Ignore unrelated cases.
- Do not list other categories.

MULTIPLE QUESTION RULES:

If the question explicitly asks for multiple values, cases,
categories, conditions, reasons, models, or parts:

- Answer all requested parts.
- Keep each part concise.
- Do not add information beyond what was requested.

IMPORTANT:

For a question such as:

"What is the exposure limit for [model]?"

the answer should contain the primary exposure limit only.

It should NOT become a list of all categories under that model.

Do not mention the reasoning used to select the answer.

Return ONLY the final answer.
""",

            config=types.GenerateContentConfig(
                system_instruction=(
                    "You are Bondhu AI's answer precision module. "
                    "Your job is to return the smallest accurate answer "
                    "that directly satisfies the user's question. "
                    "For singular questions, never append information "
                    "belonging to other categories or cases."
                )
            )
        )

        return response.text.strip()

    except Exception:
        # If optimization fails, preserve the original answer.
        return answer