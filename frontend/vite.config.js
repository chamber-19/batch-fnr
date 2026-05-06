import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
// Tauri uses a fixed dev server port and reads files from `dist/`.
// 1420 is the convention used across every Chamber 19 Tauri app.
export default defineConfig({
    plugins: [react()],
    clearScreen: false,
    server: {
        port: 1420,
        strictPort: true,
    },
    envPrefix: ["VITE_", "TAURI_"],
    build: {
        target: "es2022",
        sourcemap: false,
    },
});
