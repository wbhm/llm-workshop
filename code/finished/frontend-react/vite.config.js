import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// The proxy forwards /api/* from the Vite dev server (port 5173) to the
// FastAPI backend (port 8080). The browser only ever talks to one origin,
// so there is no CORS to deal with -- the same trick real deployments use
// with a reverse proxy.
//
// If the backend runs on another machine, change the target to its address,
// e.g. "http://192.168.1.50:8080".
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/api": {
        target: "http://localhost:8080",
        changeOrigin: true,
      },
    },
  },
});
