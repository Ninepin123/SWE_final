// 登入狀態 store（AAS 負責人維護）
// 其他子系統需要「目前登入者是誰、角色為何」時，一律從這裡取，
// 不要自己讀 localStorage。
import { defineStore } from 'pinia'
import { getMe, loginAs as loginAsApi, logout as logoutApi } from '@/api/aas'
import { ROLE_LABELS } from '@/services/mockBackend'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('token') || null,
    user: null,
    loading: false,
  }),
  getters: {
    isLoggedIn: (state) => !!state.token,
    role: (state) => state.user?.role,
    roleLabel: (state) => ROLE_LABELS[state.user?.role] ?? '未登入',
    canAccess: (state) => (roles = []) => {
      if (!roles.length) return true
      return roles.includes(state.user?.role)
    },
  },
  actions: {
    async fetchMe() {
      if (!this.token) return null
      this.loading = true
      try {
        this.user = await getMe()
        return this.user
      } finally {
        this.loading = false
      }
    },
    async loginAs(role) {
      this.loading = true
      try {
        this.user = await loginAsApi(role)
        this.token = localStorage.getItem('token')
        return this.user
      } finally {
        this.loading = false
      }
    },
    async logout() {
      await logoutApi()
      this.token = null
      this.user = null
    },
  },
})
