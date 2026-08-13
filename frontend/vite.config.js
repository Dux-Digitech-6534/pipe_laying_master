import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import { resolve } from "node:path";

export default defineConfig({
  plugins: [vue()],
  define: {
    "process.env.NODE_ENV": JSON.stringify("production"),
  },
  build: {
    outDir: resolve(__dirname, "../cmr_pipe_laying_master/public/dist"),
    emptyOutDir: true,
    lib: {
      entry: resolve(__dirname, "src/main.js"),
      name: "CMRPipeLayingMaster",
      formats: ["iife"],
      fileName: () => "cmr-pipe-laying-master-v12.js",
    },
    rollupOptions: {
      output: {
        footer: "window.CMRPipeLayingMaster = CMRPipeLayingMaster;",
        assetFileNames: (assetInfo) => assetInfo.name === "style.css" ? "cmr-pipe-laying-master-v12.css" : "[name][extname]",
      },
    },
  },
});

