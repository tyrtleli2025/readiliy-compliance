import json
import os
import re
import warnings
from collections.abc import Callable

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
_EXTRACT_CHUNK_SIZE = 20_000


def _call(prompt: str) -> str:
    response = _client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[{"role": "user", "parts": [{"text": prompt}]}],
        config=types.GenerateContentConfig(temperature=0, max_output_tokens=65536),
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


def _extract_prompt(text: str) -> str:
    return (
        "You are a compliance analyst extracting requirements from a regulatory document.\n\n"
        "STEP 1 — Detect document type:\n"
        "- If the document consists primarily of numbered items already phrased as yes/no "
        "questions (e.g., 'Does the P&P state that...', 'Does the plan ensure...'), it is "
        "a CHECKLIST document.\n"
        "- Otherwise it is a NARRATIVE document.\n\n"
        "STEP 2 — Extract requirements based on document type:\n\n"
        "CHECKLIST: Extract exactly one requirement per numbered item, preserving each "
        "question exactly as written. Do NOT split a numbered item into sub-parts even if "
        "it references multiple elements (e.g., '12 listed services', 'five elements'). "
        "The numbered item is the unit.\n\n"
        "NARRATIVE: A requirement is any normative obligation — a statement where a party "
        "(MCP, provider, contractor, plan, etc.) MUST, SHALL, IS REQUIRED TO, MAY NOT, or "
        "MUST NOT do something, or IS RESPONSIBLE FOR something. Trigger words: must, "
        "shall, required to, may not, must not, are required, are responsible for.\n"
        "- Granularity: one normative statement = one requirement. If a paragraph contains "
        "three 'shall' clauses, extract three requirements. If a sentence enumerates a list "
        "of things a party must do, treat the whole sentence as one requirement — do NOT "
        "fragment the list items.\n"
        "- Phrasing: rewrite each extracted obligation as a yes/no compliance question "
        "starting with 'Does the P&P state that...'. Example: 'MCPs must ensure that ECM "
        "Providers comply with all applicable state and federal laws' → 'Does the P&P state "
        "that MCPs must ensure ECM Providers comply with all applicable state and federal "
        "laws?'\n"
        "- Exclude: definitions, background context, legislative history, "
        "table-of-contents entries, references to external documents, and descriptive prose "
        "that does not impose an obligation. Only extract obligations.\n\n"
        "Return ONLY a JSON array of strings, no prose, no markdown fences.\n\n"
        f"{text}"
    )


def extract_requirements(
    regulatory_text: str,
    on_chunk: Callable[[int, int], None] | None = None,
) -> list[str]:
    chunks = [
        regulatory_text[i : i + _EXTRACT_CHUNK_SIZE]
        for i in range(0, len(regulatory_text), _EXTRACT_CHUNK_SIZE)
    ]
    all_requirements: list[str] = []
    for idx, chunk in enumerate(chunks):
        all_requirements.extend(_parse_json(_call(_extract_prompt(chunk))))
        if on_chunk:
            on_chunk(idx + 1, len(chunks))
    return all_requirements


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
