// 共用 axios 實例（組長維護，修改前請在群組告知）
// 各子系統的 API 呼叫一律寫在 src/api/<子系統>.js，並 import 這個實例，
// 不要在元件裡直接呼叫 axios / fetch。
import axios from 'axios'

export const useMockApi = import.meta.env.VITE_USE_MOCK_API !== 'false'

const http = axios.create({
  baseURL: '/api', // 開發時由 vite.config.js 的 proxy 轉發到後端
  timeout: 15000,
})

// 自動附帶登入 token（AAS 完成登入功能後生效）
http.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 401 統一處理：導回登入頁
http.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('token')
      // TODO(AAS): 登入頁完成後改為 router.push('/login')
    }
    return Promise.reject(err)
  },
)

export async function withApiFallback(request, fallback) {
  if (useMockApi) {
    return fallback()
  }
  try {
    const response = await request()
    return response.data
  } catch (error) {
    if (import.meta.env.DEV) {
      console.warn('API 尚未完成，改用前端 mock 資料。', error)
      return fallback()
    }
    throw error
  }
}

export default http
