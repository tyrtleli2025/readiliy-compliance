import json
from concurrent.futures import ThreadPoolExecutor, as_completed

import streamlit as st

from pdf_utils import extract_pdf_text
from llm import extract_requirements, check_requirements_batch
from retrieval import PolicyIndex

BATCH_SIZE = 12
MAX_WORKERS = 5


@st.cache_resource
def build_policy_index() -> tuple[PolicyIndex, int]:
    with open("policies.json") as f:
        library: dict[str, str] = json.load(f)
    return PolicyIndex(library), len(library)


@st.cache_data
def cached_batch(requirements: tuple[str, ...], policy_text: str) -> list[dict]:
    return check_requirements_batch(list(requirements), policy_text)


policy_index, policy_count = build_policy_index()

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
    chunks = [
        requirements[i : i + BATCH_SIZE]
        for i in range(0, len(requirements), BATCH_SIZE)
    ]

    progress = st.progress(0.0)
    results_by_chunk: dict[int, list[dict]] = {}
    completed = 0

    with st.spinner("Checking requirements…"):
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = {
                executor.submit(
                    cached_batch,
                    tuple(chunk),
                    policy_index.retrieve(" ".join(chunk)),
                ): idx
                for idx, chunk in enumerate(chunks)
            }
            for future in as_completed(futures):
                idx = futures[future]
                results_by_chunk[idx] = future.result()
                completed += 1
                progress.progress(completed / len(chunks))

    results = [r for idx in range(len(chunks)) for r in results_by_chunk[idx]]

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
