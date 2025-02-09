import { useState } from "react";
import QueryInput from "../components/QueryInput";
import CategorySelection from "../components/CategorySelection";
import ResultCard from "../components/ResultCard";
import ChatHistory from "../components/ChatHistory";
import { fetchResults } from "../services/api"; // Import API function


export default function UserInterface() {
  const [query, setQuery] = useState("");
  const [categories, setCategories] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState(null);
  const [results, setResults] = useState([]);
  const [followUpQuery, setFollowUpQuery] = useState("");
  const [conversation, setConversation] = useState([]);


  // Step 1: Handle first search (only show categories)
  const handleQuerySubmit = async () => {
    if (!query) return; // Prevent empty searches
    setCategories(["Company Strategy", "Technology Stack", "Major Players"]); // Show categories
    setSelectedCategory(null); // Reset selection
    setResults([]); // Hide results initially
  };


  // Step 2: Handle category selection (fetch actual results)
  const handleCategorySelect = async (category) => {
    setSelectedCategory(category);
    setCategories([]); // Hide category selection
  
    const data = await fetchResults(query, category); // Fetch results from ChromaDB
  
    console.log("ChromaDB Results:", data.results); // Debugging
  
    setResults(data.results); // Show results
    
    // Add to conversation history only AFTER results are shown
    if (data.results.length > 0) {
      setConversation([...conversation, { question: query, response: `Filtered results for: ${category}` }]);
    } else {
      console.warn("No results found for this category!");
    }
  };

  
  // Step 3: Handle follow-up questions
  const handleFollowUp = async () => {
    if (!followUpQuery) return;
    setConversation([
      ...conversation,
      { question: followUpQuery, response: "Here's a more detailed breakdown..." },
    ]);
    setFollowUpQuery(""); // Clear input
  };


  return (
    <div className="p-6 max-w-3xl mx-auto">
      <h1 className="text-2xl font-bold mb-4">Company Intelligence Agent</h1>
      
      {/* Step 1: Enter search query */}
      <QueryInput query={query} setQuery={setQuery} onSubmit={handleQuerySubmit} />
      
      {/* Step 2: Select category */}
      {categories.length > 0 && (
        <CategorySelection categories={categories} onSelect={handleCategorySelect} />
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
          <QueryInput query={followUpQuery} setQuery={setFollowUpQuery} onSubmit={handleFollowUp} />
        </div>
      )}

      {/* Step 5: Show chat history */}
      {conversation.length > 0 && <ChatHistory conversation={conversation} />}
    </div>
  );
}