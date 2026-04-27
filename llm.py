import json
import os
import re

from dotenv import load_dotenv
from google import genai

load_dotenv()

_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def extract_requirements(regulatory_text: str) -> list[str]:
    prompt = (
        "You are a compliance analyst. Extract every distinct regulatory requirement "
        "from the text below. Return ONLY a JSON array of strings, no prose, no markdown fences.\n\n"
        f"{regulatory_text}"
    )

    response = _client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[{"role": "user", "parts": [{"text": prompt}]}],
    )

    raw = response.text.strip()
    # Strip markdown fences if the model wrapped the JSON
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)

    return json.loads(raw)
