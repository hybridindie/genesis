import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

export default defineConfig({
  plugins: [react()],
  // The backend mounts its routers at /reports; the frontend calls /api/...
  server: { proxy: { "/api": { target: "http://localhost:8000", rewrite: (p) => p.replace(/^\/api/, "") } } },
  test: { environment: "jsdom" },
});
