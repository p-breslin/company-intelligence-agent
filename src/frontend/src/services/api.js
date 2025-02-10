/**
 * API Utility Functions
 * ---------------------
 * Provides utility functions to interact with the backend API.
 * Includes:
 * - Fetching search results based on a user query and an optional category.
 *
 * Features:
 * - Uses the Fetch API to request data from a FastAPI backend.
 * - Implements error handling to manage failed requests.
 * - Returns results in JSON format for further processing.
 *
 * Constants:
 * - `API_URL`: The base URL of the backend server.
 *
 * Functions:
 * - `fetchResults(query, cat)`: Sends a request to retrieve search results.
 */

const API_URL = "http://127.0.0.1:8000"; // Backend server URL

export async function fetchResults(query, category = "") {
  try {
    // Construct the API request URL
    const response = await fetch(
      `${API_URL}/search?q=${query}&category=${category}`
    );

    // Check for a successful response (HTTP status 200-299)
    if (!response.ok) throw new Error("Failed to fetch results");

    // Parse JSON response
    const data = await response.json();
    console.log("API Response:", data);

    return data;
  } catch (error) {
    console.error("Error fetching results:", error);
    return {
      q: [],
      cateogory: [],
      results: [],
      llm_response: "Error retrieving information. Please try again.",
    };
  }
}
