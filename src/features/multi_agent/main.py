import asyncio
import logging
import streamlit as st


def main():
    if "query" not in st.session_state:
        st.session_state.query = None

    if "results" not in st.session_state:
        st.session_state.results = None

    # Title of webpage
    st.title("Mult-Agent Workflow")

    # Sidebar for navigation
    page = st.sidebar.radio("Navigation", "Query Interface")

    if page == "Query Interface":
        query = st.text_input("Enter a query:")
        if st.button("Submit"):
            if not query:
                st.warning("Please enter a query.")
