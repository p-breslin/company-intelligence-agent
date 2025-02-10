import { useState } from "react";
import QueryInput from "../components/QueryInput";
import CategorySelection from "../components/CategorySelection";
import ResultCard from "../components/ResultCard";
import ChatHistory from "../components/ChatHistory";
import { fetchResults } from "../services/api"; // API function
import frontendConfig from "@configs/frontendConfig.json";

// Debugging logs to verify loaded configuration
// console.log("frontendConfig", frontendConfig);
// console.log("Categories:", frontendConfig.categories);

export default function QueryInterface() {
  // State Variables to store the:
  //  – user's input in the search field
  //  – categories for filtering search results
  //  – currently selected category
  //  – search results based on the user's query and selected category
  //  – follow-up queries
  //  – the conversation history
  const [query, setQuery] = useState("");
  const [categories, setCategories] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState(null);
  const [results, setResults] = useState([]);
  const [followUpQuery, setFollowUpQuery] = useState("");
  const [conversation, setConversation] = useState([]);

  // Step 1: Handle intial query and its submission
  const handleQuerySubmit = async () => {
    if (!query) return; // Prevents empty searches

    // Fetches categories as defined in the config file
    setCategories(frontendConfig.categories); // Shows categories
    setSelectedCategory(null); // Resets selection
    setResults([]); // Clears the previous results
  };

  // Step 2: Handle category selection and fetch the results
  const handleCategorySelect = async (category) => {
    setSelectedCategory(category); // Uses chosen category
    setCategories([]); // Hides category selection

    try {
      // Fetch ChromaDB results from API based on query and category
      const fetchedResults = await fetchResults(query, category);

      // Update results state with retrieved data
      setResults(fetchedResults.results);

      // Add the query and results to conversation history
      if (fetchedResults.results.length > 0) {
        setConversation([
          ...conversation,
          { query, category, results: fetchedResults },
        ]);
      } else {
        console.warn("No results found for this category.");
      }
    } catch (error) {
      console.error("Error fetching results:", error);
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
        response: "Here's a more detailed breakdown...",
      },
    ]);
    setFollowUpQuery(""); // Clear input after submission
  };

  return (
    <div className="p-6 max-w-3xl mx-auto">
      <h1 className="text-2xl font-bold mb-4">Company Intelligence Agent</h1>

      {/* Step 1: Make a query to the search input field */}
      <QueryInput
        query={query}
        setQuery={setQuery}
        onSubmit={handleQuerySubmit}
      />

      {/* Step 2: Select category from category selection */}
      {categories.length > 0 && (
        <CategorySelection
          categories={categories}
          onSelect={handleCategorySelect}
        />
      )}

      {/* Step 3: Show results after category selection */}
      {selectedCategory && results.length > 0 && (
        <div className="mt-6">
          <h2 className="text-lg font-semibold">Results</h2>
          {results.map((res) => (
            <ResultCard key={res.id} title={res.title} summary={res.summary} />
          ))}
        </div>
      )}

      {/* Step 4: Allow follow-up questions */}
      {selectedCategory && results.length > 0 && (
        <div className="mt-6">
          <h2 className="text-lg font-semibold">Ask more about the results</h2>
          <QueryInput
            query={followUpQuery}
            setQuery={setFollowUpQuery}
            onSubmit={handleFollowUp}
          />
        </div>
      )}

      {/* Step 5: Show the chat history */}
      {conversation.length > 0 && <ChatHistory conversation={conversation} />}
    </div>
  );
}
