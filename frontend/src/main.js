// App 進入點（組長維護）
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import { useMockApi } from './api/http'
import './assets/styles.css'
import './assets/visual-refresh.css'

// 開發環境或使用 mock 後端時啟用 dev-mode：顯示測試角色切換等除錯 UI
// 正式環境（VITE_USE_MOCK_API=false 且 production build）會自動隱藏
if (import.meta.env.DEV || useMockApi) {
  document.documentElement.classList.add('dev-mode')
  document.body.classList.add('dev-mode')
}

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.mount('#app')
