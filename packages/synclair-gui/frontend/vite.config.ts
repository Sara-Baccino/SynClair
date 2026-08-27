import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// SynClair frontend dev server configuration.
// The backend (FastAPI) runs separately on port 8000 (see
// synclair-gui/backend README); CORS on the backend side already
// allows http://localhost:5173 by default (see app.py's
// CORS_ALLOWED_ORIGINS), so no dev proxy is strictly required here.
// A proxy is added anyway for convenience: it lets frontend code call
// relative paths like "/api/auth/login" without hardcoding the backend
// origin, which matters once we deploy behind a single domain.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ""), // <-- Rimuove /api prima di inoltrare a FastAPI
      },
      "/auth": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
      "/datasets": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
      "/structure": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
      "/demo": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
    },
  },
});