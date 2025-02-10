export default function QueryInput({ query, setQuery, onSubmit }) {
  return (
    <div className="flex flex-col space-y-2">
      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Ask a question..."
        className="border p-2 rounded"
      />
      <button onClick={onSubmit} className="bg-blue-500 text-white px-4 py-2 rounded">
        Search
      </button>
    </div>
  );
}
