/**
 * Vite Configuration File
 * -----------------------
 * Sets up Vite for a React project.
 * Includes:
 * - React plugin integration.
 * - Custom alias resolution for cleaner imports.
 *
 * Features:
 * - Uses `@vitejs/plugin-react` for optimized React support.
 * - A custom alias (`@configs`) to simplify importing configuration files.
 * - Resolves paths dynamically for flexibility across different environments.
 *
 * Usage:
 * - Automatically loaded by Vite when starting the development server.
 */

import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

// Debugging log to check alias resolution
// console.log(
//   "Resolved @configs alias:",
//   path.resolve(__dirname, "../../configs")
// );

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@configs": path.resolve(__dirname, "../../configs"), // Maps @configs to actual configs/ directory
    },
  },
});
