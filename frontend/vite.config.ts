import { fileURLToPath, URL } from "node:url";

import vue from "@vitejs/plugin-vue";
import { defineConfig, mergeConfig } from "vite";
import { defineConfig as defineVitestConfig } from "vitest/config";

const viteConfig = defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./src", import.meta.url)),
    },
  },
  server: {
    port: 5173,
    // Proxies API calls to the backend in dev so the browser only ever
    // talks to one origin; the backend's own CORS config covers the case
    // where this proxy isn't in front (e.g. `vite preview`).
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
});

const vitestConfig = defineVitestConfig({
  test: {
    environment: "jsdom",
    include: ["tests/unit/**/*.test.ts"],
    globals: false,
  },
});

export default mergeConfig(viteConfig, vitestConfig);
