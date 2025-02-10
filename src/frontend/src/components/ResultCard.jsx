/**
 * ResultCard Component
 * --------------------
 * Displays a single search result, including a title and a summary.
 *
 * Props:
 * - title (string): The title of the search result.
 * - summary (string): A brief summary or description of the search result.
 *
 * Usage:
 * <ResultCard title="Example Title" summary="Summary of the result." />
 *
 * Styles:
 * - Uses Tailwind CSS for layout and styling.
 * - Adds a shadow for a card-like appearance.
 */

export default function ResultCard({ title, summary }) {
  return (
    <div className="border p-4 rounded shadow-md mb-4">
      {/* Display result title */}
      <h3 className="font-bold text-lg">{title}</h3>

      {/* Display result summary */}
      <p className="text-gray-600">{summary}</p>
    </div>
  );
}
