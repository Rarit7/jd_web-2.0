import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'
import { createSvgIconsPlugin } from 'vite-plugin-svg-icons'
import UnoCSS from 'unocss/vite'

const pathSrc = resolve(__dirname, 'src')

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd())
  
  return {
    plugins: [
      vue(),
      UnoCSS({
        hmrTopLevelAwait: false
      }),
      createSvgIconsPlugin({
        iconDirs: [resolve(pathSrc, 'assets/icons')],
        symbolId: 'icon-[dir]-[name]',
      }),
    ],
    resolve: {
      alias: {
        '@': pathSrc
      }
    },
    css: {
      preprocessorOptions: {
        scss: {
          additionalData: `@use "@/styles/variables.scss" as *;`
        }
      }
    },
    server: {
      port: 8930,
      host: '0.0.0.0',
      proxy: {
        '/api': {
          target: 'http://127.0.0.1:8981',
          changeOrigin: true,
          secure: false,
          configure: (proxy, options) => {
            proxy.on('proxyReq', (proxyReq, req, res) => {
              console.log('Proxying request:', req.method, req.url, '-> target:', options.target)
            })
            proxy.on('error', (err, req, res) => {
              console.log('Proxy error:', err)
            })
          }
        },
        '/static': {
          target: 'http://127.0.0.1:8981',
          changeOrigin: true,
          secure: false
        }
      }
    },
    build: {
      outDir: '../static/dist',
      emptyOutDir: true,
      sourcemap: false,
      chunkSizeWarningLimit: 1000,
      rollupOptions: {
        output: {
          manualChunks: {
            'element-plus': ['element-plus'],
            'vue-vendor': ['vue', 'vue-router', 'pinia'],
            'utils': ['axios', '@vueuse/core']
          }
        }
      }
    }
  }
})