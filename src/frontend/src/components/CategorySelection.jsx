export default function CategorySelection({ categories, onSelect }) {
  return (
    <div className="mt-4">
      <p className="font-medium mb-2">Refine your query:</p>
      <div className="flex gap-2">
        {categories.map((category) => (
          <button
            key={category}
            onClick={() => onSelect(category)}
            className="bg-gray-200 px-4 py-2 rounded hover:bg-gray-300"
          >
            {category}
          </button>
        ))}
      </div>
    </div>
  );
}