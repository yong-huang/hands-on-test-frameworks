import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// pw-store 前端构建：产物进 dist/，由 labs/32_pw_sut/server.mjs 托管
export default defineConfig({
    plugins: [react()],
    base: '/',
    build: { outDir: 'dist', emptyOutDir: true },
});
