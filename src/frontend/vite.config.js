import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

console.log(
  "Resolved @configs alias:",
  path.resolve(__dirname, "../../configs")
);

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@configs": path.resolve(__dirname, "../../configs"), // Maps @configs to actual configs/ directory
    },
  },
});
