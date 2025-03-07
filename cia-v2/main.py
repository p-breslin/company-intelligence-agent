import asyncio
import logging
import streamlit as st
from tavily_piepline import search_engine
from backend.LLM_integration import LocalLLM
from orchestrator.embedding_search import EmbeddingSearch


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


# Track any background Firecrawl tasks
if "firecrawl_task" not in st.session_state:
    st.session_state.firecrawl_task = None


def wait_for_firecrawl():
    """Waits for the Firecrawl background process to complete."""
    if st.session_state.firecrawl_task is not None:
        process = st.session_state.firecrawl_task
        if process.poll() is None:  # Check if it's still running
            logging.info("Waiting for Firecrawl to finish...")
            process.wait()
            logging.info("Firecrawl process completed.")

        # Cleanup after completion
        st.session_state.firecrawl_task = None


def main():
    LLM = LocalLLM()
    database = "weaviate"

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
        company = st.text_input("Enter a company of interest:")
        if st.button("Submit company"):
            if not company:
                st.warning("Please enter a company name.")
            else:
                with st.spinner("Searching the Web..."):
                    result, firecrawl_task = asyncio.run(search_engine(company))
                    st.session_state.firecrawl_task = firecrawl_task

                st.subheader("Results")
                st.write(f"**Products:** {result['products']}")
                st.write(f"**Competitors:** {result['competitors']}")
                st.write(f"**Links:** {result['links']}")

        # Option to query the results
        query = st.text_area("Ask more about these companies or products:")
        if st.button("Submit query"):
            with st.spinner("Storing new data..."):
                wait_for_firecrawl()

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
            st.subheader("Follow-Up Query")
            follow_up_query = st.text_area("Enter follow-up query:", key="followup")

            if st.button("Submit follow-up"):
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
