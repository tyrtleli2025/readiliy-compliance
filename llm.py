import json
import os
import re
import warnings

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def _call(prompt: str) -> str:
    response = _client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[{"role": "user", "parts": [{"text": prompt}]}],
        config=types.GenerateContentConfig(temperature=0),
    )
    return response.text.strip()


def _parse_json(raw: str):
    # Strip markdown fences
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw.strip())
    # Seek to the first JSON value delimiter so leading prose is ignored
    start = min(
        (raw.find(c) for c in ("{", "[") if raw.find(c) != -1),
        default=0,
    )
    # raw_decode stops after the first complete JSON value, ignoring trailing text
    value, _ = json.JSONDecoder().raw_decode(raw, start)
    return value


def extract_requirements(regulatory_text: str) -> list[str]:
    prompt = (
        "You are a compliance analyst reviewing a regulatory checklist document. "
        "Requirements in these documents are typically numbered questions beginning with "
        "phrases like 'Does the P&P state that...' or 'Does the plan ensure...'.\n\n"
        "Rules:\n"
        "- Extract exactly one requirement per numbered item in the source document.\n"
        "- Do NOT split a numbered item into sub-parts, even if it references multiple "
        "sub-items (e.g., '12 listed services', 'five elements', 'four special "
        "considerations'). The numbered item is the unit of extraction.\n"
        "- Preserve each requirement as a complete, standalone question exactly as written.\n"
        "- Return ONLY a JSON array of strings, no prose, no markdown fences.\n\n"
        f"{regulatory_text}"
    )
    return _parse_json(_call(prompt))


def check_requirements_batch(requirements: list[str], policy_text: str) -> list[dict]:
    n = len(requirements)
    numbered = "\n".join(f"{i}. {req}" for i, req in enumerate(requirements))
    prompt = (
        "You are a compliance analyst. For each numbered requirement below, determine "
        "whether the policy text satisfies it.\n\n"
        f"Requirements:\n{numbered}\n\n"
        f"Policy text:\n{policy_text}\n\n"
        "Each document in the policy text is preceded by a '--- Document: <filename> ---' "
        "header. If a requirement is met, identify which document the evidence came from.\n\n"
        f"Return ONLY a JSON array of exactly {n} objects, one per requirement, in order. "
        "Do not skip any. No prose, no markdown fences. Each object must have exactly "
        'these keys: {"requirement_index": int (0-based), "met": bool, '
        '"evidence": "verbatim quote or null", "source_document": "filename or null", '
        '"reasoning": "one sentence"}'
    )
    raw = _parse_json(_call(prompt))

    if not isinstance(raw, list):
        warnings.warn(f"Batch response was not a list; got {type(raw)}")
        raw = []

    indexed = {item.get("requirement_index", i): item for i, item in enumerate(raw)}
    results = []
    for i in range(n):
        if i not in indexed:
            warnings.warn(f"Missing result for requirement index {i}; marking not met")
            results.append({
                "met": False,
                "evidence": None,
                "source_document": None,
                "reasoning": "No result returned by model.",
            })
        else:
            results.append(indexed[i])
    return results


def check_requirement(requirement: str, policy_text: str) -> dict:
    return check_requirements_batch([requirement], policy_text)[0]
