import streamlit as st

st.title("Compliance Checker")

with st.sidebar:
    regulatory_file = st.file_uploader("Regulatory document", type=["pdf"])
    policy_file = st.file_uploader("Policy document", type=["pdf"])

st.write("Upload documents to begin.")
