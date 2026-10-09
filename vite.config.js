import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  define: {
    "process.env.NODE_ENV": JSON.stringify("production"),
  },
  build: {
    lib: {
      entry: "src/mount.jsx",
      name: "__lssNudge",
      fileName: "nudge-panel",
      formats: ["iife"],
    },
    outDir: "dist",
    rollupOptions: {
      // Bundle React in — no external deps needed in the userscript
      external: [],
    },
  },
});
