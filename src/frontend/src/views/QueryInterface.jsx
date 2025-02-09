import { useState } from "react";
import QueryInput from "../components/QueryInput";
import CategorySelection from "../components/CategorySelection";
import ResultCard from "../components/ResultCard";
import ChatHistory from "../components/ChatHistory";

export default function UserInterface() {
  const [query, setQuery] = useState("");
  const [categories, setCategories] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState(null);
  const [results, setResults] = useState([]);
  const [followUpQuery, setFollowUpQuery] = useState("");
  const [conversation, setConversation] = useState([]);

  // Handles query submission and sets mock categories
  const handleQuerySubmit = async () => {
    const mockCategories = ["Company Strategy", "Technology Stack", "Major Players"];
    setCategories(mockCategories);
  };

  // Handles category selection and sets mock results
  const handleCategorySelect = async (category) => {
    setSelectedCategory(category);
    setCategories([]); // Hide categories
    setResults([
      { id: 1, title: "Apple's AI Strategy", summary: "Apple is investing in AI..." },
      { id: 2, title: "Apple's New Chip", summary: "The new M4 chip will..." },
    ]);
  };

  // Handles follow-up queries and updates conversation
  const handleFollowUp = async () => {
    setConversation([
      ...conversation,
      { question: followUpQuery, response: "Here's a more detailed breakdown..." },
    ]);
    setFollowUpQuery(""); // Clear input
  };

  return (
    <div className="p-6 max-w-3xl mx-auto">
      <h1 className="text-2xl font-bold mb-4">Company Intelligence Agent</h1>
      <QueryInput query={query} setQuery={setQuery} onSubmit={handleQuerySubmit} />
      {categories.length > 0 && (
        <CategorySelection categories={categories} onSelect={handleCategorySelect} />
      )}
      {results.length > 0 && (
        <div className="mt-6">
          <h2 className="text-lg font-semibold">Results</h2>
          {results.map((res) => (
            <ResultCard key={res.id} title={res.title} summary={res.summary} />
          ))}
        </div>
      )}
      {results.length > 0 && (
        <div className="mt-6">
          <h2 className="text-lg font-semibold">Ask more about the results</h2>
          <QueryInput query={followUpQuery} setQuery={setFollowUpQuery} onSubmit={handleFollowUp} />
        </div>
      )}
      {conversation.length > 0 && <ChatHistory conversation={conversation} />}
    </div>
  );
}