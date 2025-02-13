/**
 * QueryInput Component
 * --------------------
 * Provides a controlled input field where users can type a query and submit it
 * using the "Search" button.
 *
 * Props:
 * - query (string): The current value of the input field.
 * - setQuery (function): Updates the input value as the user types.
 * - onSubmit (function): Triggered when the user clicks the search button.
 *
 * Usage:
 * <QueryInput query={query} setQuery={setQuery} onSubmit={handleSubmit} />
 */

export default function QueryInput({ query, setQuery, onSubmit }) {
  return (
    <div className="flex flex-col space-y-2">
      {/* Text input for user query */}
      <input
        type="text"
        value={query} // Controlled component: value comes from state
        onChange={(e) => setQuery(e.target.value)} // Updates state as user types
        placeholder="Ask a question..."
        className="border p-2 rounded"
      />
      {/* Search button triggers onSubmit function */}
      <button
        onClick={onSubmit}
        className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 transition"
      >
        Search
      </button>
    </div>
  );
}
