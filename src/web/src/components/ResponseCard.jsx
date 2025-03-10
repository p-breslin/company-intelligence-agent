/**
 * ResponseCard Component
 * --------------------
 * Displays a single search result, including a title and LLM response.
 *
 * Props:
 * - title (string): The title of the search result.
 * - summary (string): The summary given by the LLM.
 *
 * Usage:
 * <ResponseCard title="Title of article" summary="LLM response." />
 */

import React from "react";
import ReactMarkdown from "react-markdown";

export default function ResponseCard({ title, summary }) {
  return (
    <div className="border p-4 rounded shadow-md mb-4">
      {/* Display title of response */}
      <h3 className="font-bold text-lg">{title}</h3>

      {/* Display LLM response sumamry (formatted with markdown) */}
      <ReactMarkdown
        className="text-gray-600"
        components={{
          p: ({ children }) => <p className="mb-2">{children}</p>,
          ul: ({ children }) => <ul className="list-disc pl-5">{children}</ul>,
          ol: ({ children }) => (
            <ol className="list-decimal pl-5">{children}</ol>
          ),
          li: ({ children }) => <li className="ml-4">{children}</li>,
        }}
      >
        {summary}
      </ReactMarkdown>
    </div>
  );
}
