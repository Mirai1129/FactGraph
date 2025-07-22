// vite.config.js
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    proxy: {
      // 所有 /api 開頭的請求都會被轉發到後端
      '/api': {
        target: 'http://127.0.0.1:8080',
        changeOrigin: true,
        // 如果你的 FastAPI 路由前面沒加 /api，則加上 rewrite：
        // rewrite: path => path.replace(/^\/api/, '')
      }
    }
  }
})
