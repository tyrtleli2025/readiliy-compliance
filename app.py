import hashlib
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from math import ceil

import streamlit as st

from pdf_utils import extract_pdf_text
from llm import extract_requirements, check_requirements_batch

BATCH_SIZE = 12
MAX_WORKERS = 5


@st.cache_resource
def load_policy_library() -> tuple[str, int]:
    with open("policies.json") as f:
        library: dict[str, str] = json.load(f)
    parts = [f"--- Document: {name} ---\n{text}" for name, text in library.items()]
    return "\n\n".join(parts), len(library)


@st.cache_data
def run_compliance_check(
    requirements: tuple[str, ...], policy_text_hash: str, policy_text: str
) -> list[dict]:
    chunks = [
        list(requirements[i : i + BATCH_SIZE])
        for i in range(0, len(requirements), BATCH_SIZE)
    ]
    results_by_chunk: dict[int, list[dict]] = {}

    progress = st.progress(0.0)
    completed = 0

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(check_requirements_batch, chunk, policy_text): idx
            for idx, chunk in enumerate(chunks)
        }
        for future in as_completed(futures):
            idx = futures[future]
            results_by_chunk[idx] = future.result()
            completed += 1
            progress.progress(completed / len(chunks))

    return [r for idx in range(len(chunks)) for r in results_by_chunk[idx]]


policy_text, policy_count = load_policy_library()

st.title("Compliance Checker")

with st.sidebar:
    regulatory_file = st.file_uploader("Regulatory document", type=["pdf"])
    st.caption(f"📚 Policy library: {policy_count} document(s) loaded")

if regulatory_file:
    regulatory_text = extract_pdf_text(regulatory_file)
    st.subheader("Regulatory document — first 1000 chars")
    st.text(regulatory_text[:1000])

    st.subheader("Extracted requirements")
    with st.spinner("Extracting requirements…"):
        requirements = extract_requirements(regulatory_text)
    for i, req in enumerate(requirements, 1):
        st.write(f"{i}. {req}")

    st.subheader("Compliance check")
    policy_hash = hashlib.md5(policy_text.encode()).hexdigest()
    with st.spinner("Checking requirements…"):
        results = run_compliance_check(tuple(requirements), policy_hash, policy_text)

    for req, result in zip(requirements, results):
        met = result.get("met", False)
        icon = "✅" if met else "❌"
        with st.expander(f"{icon} {req}"):
            st.write(f"**Reasoning:** {result.get('reasoning', '')}")
            evidence = result.get("evidence")
            if evidence:
                source = result.get("source_document")
                if source:
                    st.write(f"**Source:** {source}")
                st.write(f"**Evidence:** _{evidence}_")

if not regulatory_file:
    st.write("Upload a regulatory document to begin.")
