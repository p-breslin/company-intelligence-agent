export default function ChatHistory({ conversation }) {
  return (
    <div className="mt-6">
      <h2 className="text-lg font-semibold mb-4">Conversation History</h2>
      <div className="space-y-4">
        {conversation.map((entry, index) => (
          <div key={index} className="p-4 border rounded">
            <p className="font-medium">You: {entry.question}</p>
            <p className="text-gray-600">Agent: {entry.response}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
