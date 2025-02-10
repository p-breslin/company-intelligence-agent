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

export default function ChatHistory({ conversation }) {
  if (!conversation || conversation.length === 0) {
    return (
      <div className="mt-6">
        <h2 className="text-lg font-semibold mb-4">Conversation History</h2>
        <p className="text-gray-600">No conversation history available.</p>
      </div>
    );
  }

  return (
    <div className="mt-6">
      {/* Section heading */}
      <h2 className="text-lg font-semibold mb-4">Conversation History</h2>

      {/* Container for chat entries */}
      <div className="space-y-4">
        {conversation.map((entry, index) => (
          <div
            key={index}
            className="p-4 border rounded bg-gray-50"
            aria-label={`Conversation entry ${index + 1}`}
          >
            {/* Handle both query and follow-up questions */}
            {entry.query && (
              <p className="font-medium text-blue-800">
                <span className="font-bold">You:</span> {entry.query}
              </p>
            )}
            {entry.question && (
              <p className="font-medium text-blue-800">
                <span className="font-bold">You:</span> {entry.question}
              </p>
            )}

            {/* Agent's response */}
            {entry.response && (
              <p className="text-gray-600">
                <span className="font-bold">Agent:</span> {entry.response}
              </p>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
