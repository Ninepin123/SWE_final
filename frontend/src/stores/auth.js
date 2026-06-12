// 登入狀態 store（AAS 負責人維護）
// 其他子系統需要「目前登入者是誰、角色為何」時，一律從這裡取，
// 不要自己讀 localStorage。
import { defineStore } from 'pinia'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('token') || null,
    user: null, // TODO(AAS): { id, name, role: 'STUDENT'|'TEACHER'|'SPONSOR'|'REVIEWER'|'ADMIN', unitId }
  }),
  getters: {
    isLoggedIn: (state) => !!state.token,
  },
  actions: {
    // TODO(AAS): login(account, password)、logout()、fetchMe()
  },
})
