import streamlit as st
from pdf_utils import extract_pdf_text
from llm import extract_requirements

st.title("Compliance Checker")

with st.sidebar:
    regulatory_file = st.file_uploader("Regulatory document", type=["pdf"])
    policy_file = st.file_uploader("Policy document", type=["pdf"])

if regulatory_file:
    regulatory_text = extract_pdf_text(regulatory_file)
    st.subheader("Regulatory document — first 1000 chars")
    st.text(regulatory_text[:1000])

    st.subheader("Extracted requirements")
    with st.spinner("Extracting requirements…"):
        requirements = extract_requirements(regulatory_text)
    for i, req in enumerate(requirements, 1):
        st.write(f"{i}. {req}")

if policy_file:
    policy_text = extract_pdf_text(policy_file)
    st.subheader("Policy document — first 1000 chars")
    st.text(policy_text[:1000])

if not regulatory_file and not policy_file:
    st.write("Upload documents to begin.")
