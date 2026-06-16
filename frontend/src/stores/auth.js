// 登入狀態 store（AAS 負責人維護）
// 其他子系統需要「目前登入者是誰、角色為何」時，一律從這裡取，
// 不要自己讀 localStorage。
import { defineStore } from 'pinia'
import { login as apiLogin, logout as apiLogout, getMe } from '@/api/aas'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('token') || null,
    user: JSON.parse(localStorage.getItem('user') || 'null'),
  }),
  getters: {
    isLoggedIn: (state) => !!state.token,
    role: (state) => state.user?.role || null,
  },
  actions: {
    async login(account, password) {
      const { data } = await apiLogin(account, password)
      this.token = data.access_token
      this.user = data.user
      localStorage.setItem('token', data.access_token)
      localStorage.setItem('user', JSON.stringify(data.user))
      return data.user
    },
    async fetchMe() {
      const { data } = await getMe()
      this.user = data
      localStorage.setItem('user', JSON.stringify(data))
      return data
    },
    async logout() {
      try {
        await apiLogout()
      } catch (e) {
        // 無狀態 JWT，後端登出失敗也不影響前端清除
      }
      this.token = null
      this.user = null
      localStorage.removeItem('token')
      localStorage.removeItem('user')
    },
  },
})
