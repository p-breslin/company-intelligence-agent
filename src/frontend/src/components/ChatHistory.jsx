/**
 * ChatHistory Component
 * ---------------------
 * Displays the history of user queries and the AI agent's responses.
 *
 * Props:
 * - conversation (array of objects): List of previous interactions.
 *   - Each object should have:
 *      - question (string): The user's query.
 *      - response (string): The AI agent's response.
 *
 * Usage:
 * <ChatHistory conversation={conversation} />
 *
 * Styles:
 * - Uses Tailwind CSS for layout and styling.
 * - Applies spacing and borders for better readability.
 */

import React from "react";
import ReactMarkdown from "react-markdown";

export default function ChatHistory({ conversation }) {
  // Prevents rendering an empty component when no data is available
  if (!conversation || conversation.length === 0) {
    return (
      <div className="mt-6">
        <h2 className="text-lg font-semibold mb-4">Conversation History</h2>
        <p className="text-gray-600">No conversation history available.</p>
      </div>
    );
  }

  // Group messages properly by session
  let previousSessionId = null;

  return (
    <div className="mt-6">
      {/* Section heading */}
      <h2 className="text-lg font-semibold mb-4">Conversation History</h2>

      {/* Container for chat entries */}
      <div className="space-y-6">
        {[...conversation].reverse().map((entry, index) => {
          const isNewSession = previousSessionId !== entry.session_id;
          previousSessionId = entry.session_id;

          return (
            <div key={index} className="p-4 border rounded bg-gray-50">
              {/* Display session header for new sessions */}
              {isNewSession && (
                <h3 className="text-xl font-bold text-gray-900 mb-2">
                  New Session
                </h3>
              )}

              {/* Query */}
              <p className="font-medium text-blue-800">
                <span className="font-bold">Query:</span> {entry.query}
              </p>

              {/* LLM Response */}
              {entry.response && (
                <div className="text-gray-600 mt-2">
                  <span className="font-medium text-red-800 underline">
                    Agent's Response:
                  </span>
                  <ReactMarkdown
                    className="mt-1"
                    components={{
                      p: ({ children }) => <p className="mb-2">{children}</p>,
                      ul: ({ children }) => (
                        <ul className="list-disc pl-5">{children}</ul>
                      ),
                      ol: ({ children }) => (
                        <ol className="list-decimal pl-5">{children}</ol>
                      ),
                      li: ({ children }) => (
                        <li className="ml-4">{children}</li>
                      ),
                    }}
                  >
                    {entry.response}
                  </ReactMarkdown>
                </div>
              )}

              {/* Nested Follow-Ups */}
              {entry.followUps && entry.followUps.length > 0 && (
                <div className="mt-3 pl-5 border-l-2 border-gray-300">
                  <h4 className="text-md font-bold text-green-800 underline">
                    Follow-ups:
                  </h4>
                  {entry.followUps.map((followUp, i) => (
                    <div key={i} className="mt-2">
                      <p className="font-medium text-blue-800">
                        {followUp.query}
                      </p>
                      <ReactMarkdown className="text-gray-600">
                        {followUp.response}
                      </ReactMarkdown>
                    </div>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
