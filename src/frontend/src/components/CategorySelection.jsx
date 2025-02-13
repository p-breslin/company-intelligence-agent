/**
 * CategorySelection Component
 * ---------------------------
 * Displays a list of categories that users can select to refine their search.
 *
 * Props:
 * - categories (array of strings): List of available categories.
 * - onSelect (function): Triggered when a category is selected.
 *
 * Usage:
 * <CategorySelection categories={categories} onSelect={handleCategorySelect} />
 */

export default function CategorySelection({ categories, onSelect }) {
  return (
    <div className="mt-4">
      {/* Instructional text for category selection */}
      <p className="font-medium mb-2">Refine your query:</p>

      {/* Container for category buttons */}
      <div className="flex gap-2">
        {categories.map((category) => (
          <button
            key={category} // Unique key for each category
            onClick={() => onSelect(category)} // Calls onSelect function with the chosen category
            className="bg-gray-200 px-4 py-2 rounded hover:bg-gray-300 transition"
          >
            {category} {/* Display category name */}
          </button>
        ))}
      </div>
    </div>
  );
}
