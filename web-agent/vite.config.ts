import { copyFileSync } from 'node:fs'
import { resolve } from 'node:path'
import tailwindcss from '@tailwindcss/vite'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
    {
      name: 'copy-extension-manifest',
      closeBundle() {
        copyFileSync(resolve(__dirname, 'manifest.json'), resolve(__dirname, 'dist/manifest.json'))
      },
    },
  ],
  build: {
    rollupOptions: {
      input: {
        popup: resolve(__dirname, 'index.html'),
        background: resolve(__dirname, 'src/background.ts'),
        content: resolve(__dirname, 'src/content.ts'),
      },
      output: {
        entryFileNames: 'assets/[name].js',
      },
    },
  },
})
