// React component that provides a user interface for the Company Intelligence Agent.
// Allows the user to:
// 	1.	Enter a query (e.g., “Give me the latest news about Apple”).
// 	2.	Refine their query by selecting a category.
// 	3.	View relevant results.
// 	4.	Ask follow-up questions about the results.
// 	5.	See conversation history.


// Import necessary React hooks (useState) and UI components.
// useState: A React hook that lets us store and update variables in the component.
import { useState } from "react";
import QueryInput from "@/components/QueryInput";
import CategorySelection from "@/components/CategorySelection";
import ResultCard from "@/components/ResultCard";
import ChatHistory from "@/components/ChatHistory";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";


export default function UserInterface() {

  // Main function that defines the interface.
  //  - Every React component is just a function that returns HTML (JSX syntax).
  //  - We export it so it can be used in other parts of the app.
  // 	- useState creates state variables that React keeps track of.
  // [func, setFunc] – func stores variable, setFunc updates variable.

  const [query, setQuery] = useState("");
  const [categories, setCategories] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState(null);
  const [results, setResults] = useState([]);
  const [followUpQuery, setFollowUpQuery] = useState("");
  const [conversation, setConversation] = useState([]);

  // User actions: functions that get triggered when a user does something
  // handleQuerySubmit sets available categories after user enters query
  const handleQuerySubmit = async () => {
    setCategories(["Company Strategy", "Technology Stack", "Major Players"]);
  };

  // This stores category selected after the user selects one
  // Hides category options then fectches search results (mocked for now)
  const handleCategorySelect = async (category) => {
    setSelectedCategory(category);
    setCategories([]);
    setResults([
      { id: 1, title: "Apple's AI Strategy", summary: "Apple is investing in AI..." },
      { id: 2, title: "Apple's New Chip", summary: "The new M4 chip will..." }
    ]);
  };

  // handleFollowUp stores user's follow-up question and gives a response (mock for now)
  const handleFollowUp = async () => {
    setConversation([...conversation, { question: followUpQuery, response: "Here's a more detailed breakdown..." }]);
    setFollowUpQuery("");
  };

  // Now we render the UI (JSX)
  return (
    <div className="p-6 max-w-3xl mx-auto">
      <h1 className="text-2xl font-bold mb-4">Company Intelligence Agent</h1>
      
      {/* Inputting the query (this is a resuable input) */}
      <QueryInput query={query} setQuery={setQuery} onSubmit={handleQuerySubmit} />
      
      {/* Showing and selecting the category */}
      {categories.length > 0 && (
        <CategorySelection categories={categories} onSelect={handleCategorySelect} />
      )}

      {/* Showing the results.  results.map((res) => ) loops through the results and creates a ResultCard for each item. */}
      {results.length > 0 && (
        <div className="mt-6">
          <h2 className="text-lg font-semibold">Results</h2>
          {results.map((res) => (
            <ResultCard key={res.id} title={res.title} summary={res.summary} />
          ))}
        </div>
      )}
      
      {/* Asking a follow-up query */}
      {results.length > 0 && (
        <div className="mt-6">
          <h2 className="text-lg font-semibold">Ask more about the results</h2>
          <QueryInput query={followUpQuery} setQuery={setFollowUpQuery} onSubmit={handleFollowUp} />
        </div>
      )}

      {/* Chat history */}
      {conversation.length > 0 && <ChatHistory conversation={conversation} />}
    </div>
  );
}