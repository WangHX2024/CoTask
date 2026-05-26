import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  return {
    plugins: [
      vue(),
    ],
    resolve: {
      alias: {
        '@': fileURLToPath(new URL('./src', import.meta.url)),
      },
    },
    server: {
      host: '0.0.0.0',
      port: 5173,
      // Polling is required under WSL2 / Docker volume mounts because
      // inotify filesystem events are not reliably delivered in those
      // environments. The CHOKIDAR_USEPOLLING env var is set in
      // docker-compose.dev.yml; it also acts as the guard here so that
      // local (non-Docker) dev keeps using native FS events.
      watch: {
        usePolling: !!process.env.CHOKIDAR_USEPOLLING,
        interval: 300,
      },
      proxy: {
        '/api': {
          target: env.VITE_DEV_API_TARGET || 'http://localhost:8000',
          changeOrigin: true,
        },
        '/ws': {
          target: env.VITE_DEV_WS_TARGET || 'ws://localhost:8000',
          ws: true,
          changeOrigin: true,
        },
        '/docs': {
          target: env.VITE_DEV_API_TARGET || 'http://localhost:8000',
          changeOrigin: true,
        },
      },
      allowedHosts: ['localhost', '127.0.0.1', '0.0.0.0', 'cotask.haoxiong.wang'],
    },
    define: {
      __VITE_API_BASE__: JSON.stringify(env.VITE_API_BASE || '/api'),
      __VITE_WS_BASE__: JSON.stringify(env.VITE_WS_BASE || '/ws'),
    },
    build: {
      target: 'es2020',
      sourcemap: false,
      chunkSizeWarningLimit: 1500,
    },
  }
})
