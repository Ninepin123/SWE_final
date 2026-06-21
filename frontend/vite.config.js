// Vite 設定（組長維護，修改前請在群組告知）
import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      // 一律用 @ 引用 src，避免相對路徑地獄：import xxx from '@/api/aas'
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    // 預設 5173；若環境變數 PORT 有設（例如預覽工具指派的埠）則沿用，方便外部工具管理。
    port: process.env.PORT ? Number(process.env.PORT) : 5173,
    proxy: {
      // 開發時把 /api 轉發到後端 FastAPI（http://localhost:8000），
      // 前端程式一律呼叫相對路徑 /api/...，不要寫死後端網址。
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
