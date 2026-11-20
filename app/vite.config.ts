import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

export default defineConfig({
  // Relative asset paths, so the built app can be served from any directory.
  base: "./",
  plugins: [react()],
  test: {
    include: ["src/**/*.test.ts"],
  },
});
