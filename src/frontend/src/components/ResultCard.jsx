export default function ResultCard({ title, summary }) {
  return (
    <div className="border p-4 rounded shadow-md mb-4">
      <h3 className="font-bold text-lg">{title}</h3>
      <p className="text-gray-600">{summary}</p>
    </div>
  );
}