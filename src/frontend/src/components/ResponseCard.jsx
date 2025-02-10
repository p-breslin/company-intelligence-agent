/**
 * ResponseCard Component
 * --------------------
 * Displays a single search result, including a title and a summary.
 *
 * Props:
 * - title (string): The title of the search result.
 * - summary (string): A brief summary or description of the search result.
 *
 * Usage:
 * <ResponseCard title="Example Title" summary="Summary of the result." />
 *
 * Styles:
 * - Uses Tailwind CSS for layout and styling.
 * - Adds a shadow for a card-like appearance.
 */

import React from "react";
import ReactMarkdown from "react-markdown";

export default function ResponseCard({ title, summary }) {
  return (
    <div className="border p-4 rounded shadow-md mb-4">
      {/* Display title of response */}
      <h3 className="font-bold text-lg">{title}</h3>

      {/* Display LLM response sumamry */}
      <ReactMarkdown className="text-gray-600">{summary}</ReactMarkdown>
    </div>
  );
}
