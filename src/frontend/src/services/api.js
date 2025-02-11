/**
 * API Utility Functions
 * ---------------------
 * Provides utility functions to interact with the backend API.
 * Includes:
 * - Fetching search results based on a user query and an optional category.
 * - Functionality for follow-up questions for a given session.
 *
 * Features:
 * - Uses the Fetch API to request data from a FastAPI backend.
 */

const API_URL = "http://127.0.0.1:8000"; // Backend server URL

export async function fetchResults(query, category = "", sessionID = null) {
  try {
    // Construct the API request URL
    // Append session_id to the request URL when it’s available
    let url = `${API_URL}/engine?q=${encodeURIComponent(query)}`;
    if (category) url += `&category=${encodeURIComponent(category)}`;
    if (sessionID) url += `&session_id=${encodeURIComponent(sessionID)}`;
    const response = await fetch(url);

    console.log("Fetching:", url);

    // Check for a successful response (HTTP status 200-299)
    if (!response.ok) throw new Error("Failed to fetch results");

    // Parse JSON response
    const data = await response.json();
    console.log("API Response:", data);

    return data;
  } catch (error) {
    console.error("Error fetching results:", error);
    return {
      q: query,
      cateogory: category,
      results: [],
      llm_response: "Error retrieving information. Please try again.",
      session_id: sessionID || null,
    };
  }
}
