import logging
import streamlit as st
from backend.LLM_integration import LocalLLM
from orchestrator.embedding_search import EmbeddingSearch

logging.basicConfig(level=logging.INFO)


def main():
    LLM = LocalLLM()
    database = "weaviate"
    API_BASE_URL = "http://localhost:8501"

    # Stores chat history
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # Stores previous LLM context for follow-up
    if "last_context" not in st.session_state:
        st.session_state.last_context = None

    # Title of webpage
    st.title("Company Intelligence Agent")

    # Sidebar for navigation
    page = st.sidebar.radio("Navigation", ["Query Interface", "Chat History"])

    if page == "Query Interface":
        st.header("Submit a Query")

        query = st.text_area("Enter your search query:")
        if st.button("Submit"):
            with st.status("Extracting data...", expanded=True) as status:
                vector_search = EmbeddingSearch(query, database=database)
                retrieved_data, LLM_context = vector_search.run()
                logging.info("Generating response...")
                status.update(label="Querying LLM...", state="running")
                llm_response = LLM.generate_response(query, LLM_context)
                status.update(
                    label="Extraction complete!", state="complete", expanded=False
                )

            st.subheader("Response")
            st.write(f"**Title:** {retrieved_data['title']}")
            st.write(f"**Link:** {retrieved_data['link']}")
            st.write(llm_response)

            # Store query, response, and context in chat history
            st.session_state.chat_history.append(
                {
                    "query": query,
                    "response": llm_response,
                    "title": retrieved_data["title"],
                    "link": retrieved_data["link"],
                }
            )

            # Store context for follow-up
            st.session_state.last_context = LLM_context

        # Follow-up queries
        st.subheader("Follow-Up Question")
        follow_up_query = st.text_area("Enter follow-up question:", key="followup")

        if st.button("Submit Follow-Up"):
            if st.session_state.last_context:
                logging.info("Generating follow-up response...")
                follow_up_response = LLM.generate_response(
                    follow_up_query, st.session_state.last_context
                )

                # Store follow-up in chat history
                st.session_state.chat_history.append(
                    {
                        "query": follow_up_query,
                        "response": follow_up_response,
                        "title": "Follow-Up",
                        "link": "N/A",
                    }
                )

                st.subheader("Follow-Up Response")
                st.write(follow_up_response)
            else:
                st.error("No previous query to follow up on.")

    elif page == "Chat History":
        st.header("Previous Queries")
        if not st.session_state.chat_history:
            st.write("No previous queries.")
        else:
            for chat in st.session_state.chat_history:
                st.write(f"**Query:** {chat['query']}")
                st.write(f"**Response:** {chat['response']}")
                st.write(f"**Title:** {chat['title']}")
                st.write(f"**Link:** {chat['link']}")
                st.write("---")


if __name__ == "__main__":
    main()
