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
  return (
    <div className="mt-6">
      {/* Section heading */}
      <h2 className="text-lg font-semibold mb-4">Conversation History</h2>

      {/* Container for chat entries */}
      <div className="space-y-4">
        {conversation.map((entry, index) => (
          <div key={index} className="p-4 border rounded">
            {/* User query */}
            <p className="font-medium">You: {entry.question}</p>

            {/* Agent's response */}
            <p className="text-gray-600">Agent: {entry.response}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
