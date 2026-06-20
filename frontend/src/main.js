// App 進入點（組長維護）
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import './assets/styles.css'
import './assets/visual-refresh.css'

for (const key of ['nuksams_mock_state_v4', 'nuksams_current_user_id']) {
  localStorage.removeItem(key)
}

if (localStorage.getItem('token')?.startsWith('mock-token-')) {
  localStorage.removeItem('token')
}

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.mount('#app')
