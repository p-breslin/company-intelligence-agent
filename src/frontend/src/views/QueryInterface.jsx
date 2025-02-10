/**
 * QueryInterface Component
 * ------------------------
 * The main interface for interacting with the Company Intelligence Agent.
 * It allows users to:
 * - Enter a search query.
 * - Select a category to refine the search.
 * - View the search results.
 * - Ask follow-up questions.
 * - See their conversation history.
 *
 * State Variables:
 * - query (string): Stores the user's search input.
 * - categories (array): Holds available categories from the config.
 * - selectedCategory (string | null): Tracks the currently selected category.
 * - LLM response (string): Generated LLM response
 * - data (dict): full content and metadata fetched from ChrombaDB
 * - followUpQuery (string): Stores user input for follow-up questions.
 * - conversation (array): Maintains the chat history of queries and responses.
 *
 * Functions:
 * - handleQuerySubmit: Loads categories based on the query.
 * - handleCategorySelect: Fetches + displays results for the selected category.
 * - handleFollowUp: Allows follow-up questions on displayed results.
 *
 * Usage:
 * <QueryInterface />
 *
 * Dependencies:
 * - Uses React's useState for state management.
 * - UI components (QueryInput, CategorySelection, ResultCard, ChatHistory).
 * - Fetches results from the FastAPI service.
 * - Reads categories from a frontend configuration file.
 */

import { useState } from "react";
import { fetchResults } from "../services/api"; // API function
import QueryInput from "../components/QueryInput";
import CategorySelection from "../components/CategorySelection";
import ResponseCard from "../components/ResponseCard";
import ChatHistory from "../components/ChatHistory";
import frontendConfig from "@configs/frontendConfig.json";

// Debugging logs to verify loaded configuration
// console.log("frontendConfig", frontendConfig);
// console.log("Categories:", frontendConfig.categories);

export default function QueryInterface() {
  // State Variables
  const [query, setQuery] = useState("");
  const [categories, setCategories] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState(null);
  const [LLMResponse, setLLMResponse] = useState("");
  const [data, setData] = useState([]);
  const [followUpQuery, setFollowUpQuery] = useState("");
  const [conversation, setConversation] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showConversation, setShowConversation] = useState(false);

  // Step 1: Handle intial query and its submission
  const handleQuerySubmit = async () => {
    if (!query) return; // Prevents empty searches

    // Fetches categories as defined in the config file
    setCategories(frontendConfig.categories); // Shows categories
    setSelectedCategory(null); // Resets selection
    setLLMResponse(""); // Clears previous LLM response
    setData([]); // Clear previous data
    setLoading(true); // Set loading state to true before API call
  };

  // Step 2: Handle category selection and fetch the results
  const handleCategorySelect = async (category) => {
    setSelectedCategory(category); // Uses chosen category
    setCategories([]); // Hides category selection
    setLoading(true);

    try {
      // Fetch ChromaDB results from API based on query and category
      const fetchedResults = await fetchResults(query, category);

      // Ensure fetchedResults.results is valid
      if (
        Array.isArray(fetchedResults.results) &&
        fetchedResults.results.length > 0
      ) {
        setData(fetchedResults.results);
      } else {
        console.warn("Unexpected results structure:", fetchedResults.results);
        setData([]); // Prevents UI errors
      }

      // Add the LLM generated response
      setLLMResponse(fetchedResults.llm_response || "No response available.");

      // Add the query and response to conversation history
      setConversation([
        ...conversation,
        { query, category, response: fetchedResults.llm_response },
      ]);
    } catch (error) {
      console.error("Error fetching LLM response:", error);
      setLLMResponse("Error retrieving response. Please try again.");
    } finally {
      setLoading(false); // Reset loading state after API call finishes
    }
  };

  // Step 3: Handle follow-up questions for the fetched results
  const handleFollowUp = async () => {
    if (!followUpQuery) return; // Prevent empty follow-ups

    // Add follow-up question and placeholder response to conversation history
    setConversation([
      ...conversation,
      {
        question: followUpQuery,
        response: "Processing follow-up response...",
      },
    ]);
    setFollowUpQuery(""); // Clear input after submission
  };

  return (
    <div className="p-6 max-w-3xl mx-auto">
      <h1 className="text-2xl font-bold mb-4">Company Intelligence Agent</h1>

      {/* Step 1: Make a query */}
      <QueryInput
        query={query}
        setQuery={setQuery}
        onSubmit={handleQuerySubmit}
      />

      {/* Step 2: Select category from selection */}
      {categories.length > 0 && (
        <CategorySelection
          categories={categories}
          onSelect={handleCategorySelect}
        />
      )}

      {/* Step 3: Show LLM response */}
      {selectedCategory && (
        <div className="mt-6">
          <h2 className="text-lg font-semibold">LLM Response</h2>

          {loading ? (
            <div className="border p-4 rounded shadow-md bg-gray-100 text-gray-600">
              Loading...
            </div>
          ) : (
            <ResponseCard
              title={data?.[0]?.title || "No Title Available"}
              summary={LLMResponse || "No response available."}
            />
          )}
        </div>
      )}

      {/* Step 4: Allow follow-up questions */}
      {selectedCategory && LLMResponse && (
        <div className="mt-6">
          <h2 className="text-lg font-semibold">Ask More About the Results</h2>
          <QueryInput
            query={followUpQuery}
            setQuery={setFollowUpQuery}
            onSubmit={handleFollowUp}
          />
        </div>
      )}

      {/* Step 5: Toggle conversation history */}
      <div className="mt-6">
        <button
          onClick={() => setShowConversation(!showConversation)} // Toggle visibility
          className="bg-blue-500 text-white px-4 py-2 rounded shadow hover:bg-blue-600"
        >
          {showConversation
            ? "Hide Conversation History"
            : "Show Conversation History"}
        </button>

        {showConversation && conversation.length > 0 && (
          <div className="mt-4">
            <ChatHistory conversation={conversation} />
          </div>
        )}
      </div>
    </div>
  );
}
