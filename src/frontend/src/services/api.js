const API_URL = "http://127.0.0.1:8000";

export async function fetchResults(query, category = "") {
  try {
    const response = await fetch(`${API_URL}/search?q=${query}&category=${category}`);
    if (!response.ok) throw new Error("Failed to fetch results");
    return await response.json();
  } catch (error) {
    console.error("Error fetching results:", error);
    return { results: [] };
  }
}