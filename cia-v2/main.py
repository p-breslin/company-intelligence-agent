import asyncio
import logging
import streamlit as st
from tavily_piepline import TavilySearch
from backend.LLM_integration import LocalLLM
from orchestrator.embedding_search import EmbeddingSearch

logging.basicConfig(level=logging.INFO)


def main():
    LLM = LocalLLM()
    search = TavilySearch()
    database = "weaviate"

    # Stores chat history
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # Stores previous LLM context for follow-up
    if "last_context" not in st.session_state:
        st.session_state.last_context = None

    # Stores the entire conversation history
    if "conversation_chain" not in st.session_state:
        st.session_state.conversation_chain = []

    # Title of webpage
    st.title("Company Intelligence Agent")

    # Sidebar for navigation
    page = st.sidebar.radio("Navigation", ["Query Interface", "Chat History"])

    if page == "Query Interface":
        st.header("Submit a Query")

        query = st.text_area("Enter a Company of Interest:")
        if st.button("Submit"):
            with st.status("Searching the Web...", expanded=True) as status:
                results, engine = asyncio.run(search.run(query))
                status.update(
                    label="Search complete!", state="complete", expanded=False
                )

            st.subheader("Results")
            st.write(f"**Products:** {results['products']}")
            st.write(f"**Competitors:** {results['competitors']}")

        st.header("Further information")
        query = st.text_area("Ask more about these companies or products")
        if st.button("Submit"):
            # Wait for background tasks to complete
            with st.spinner("Storing new data..."):
                asyncio.run(engine.wait_for_firecrawl())
            st.success("Background tasks complete.")

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
            chat_entry = {
                "query": query,
                "response": llm_response,
                "title": retrieved_data["title"],
                "link": retrieved_data["link"],
            }
            st.session_state.chat_history.append(chat_entry)
            st.session_state.conversation_chain.append(chat_entry)

            # Store context for follow-ups
            st.session_state.last_context = LLM_context

        # Allow follow-ups ONLY if an initial query has been asked
        if st.session_state.last_context:
            st.subheader("Follow-Up Question")
            follow_up_query = st.text_area("Enter follow-up question:", key="followup")

            if st.button("Submit Follow-Up"):
                logging.info("Generating follow-up response...")
                with st.status("Querying LLM...", expanded=True) as status:
                    follow_up_response = LLM.generate_response(
                        follow_up_query,
                        retrieved_text=st.session_state.last_context,
                        prompt="follow_up",
                        multi_turn=True,
                    )
                    status.update(
                        label="Extraction complete!", state="complete", expanded=False
                    )

                st.subheader("Follow-Up Response")
                st.write(follow_up_response)

                # Store follow-up in chat history
                prev_resp = st.session_state.chat_history[-1]
                follow_up_entry = {
                    "query": follow_up_query,
                    "response": follow_up_response,
                    "title": prev_resp["title"],
                    "link": prev_resp["link"],
                }
                st.session_state.chat_history.append(follow_up_entry)
                st.session_state.conversation_chain.append(follow_up_entry)

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
