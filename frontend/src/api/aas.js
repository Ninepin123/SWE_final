// AAS 帳號與權限管理 — API 呼叫（負責人：填上姓名）
// 對應後端 backend/app/modules/aas/router.py，路徑前綴 /api/aas
import http, { useMockApi, withApiFallback } from './http'
import * as mock from '@/services/mockBackend'

export const ROLE_LABELS = {
  STUDENT: '學生',
  TEACHER: '教師',
  SPONSOR: '獎助單位人員',
  REVIEWER: '審查人員',
  ADMIN: '系統管理員',
  // Mock 資料尚未由整合者遷移前保留相容性。
  RECOMMENDER: '推薦人',
}

// 範例（骨架測試用，開發開始後可移除）：
export function ping() {
  return http.get('/aas/ping')
}

export function getMe() {
  if (useMockApi) return mock.fetchMe()
  return http.get('/aas/me').then((response) => response.data)
}

export function login(credentials) {
  return http.post('/aas/login', credentials).then((response) => response.data)
}

export function loginAs(role) {
  return mock.loginAs(role)
}

export function logout() {
  if (useMockApi) return mock.logout()
  return http.post('/aas/logout').then((response) => response.data)
}

export function listUsers(params) {
  return withApiFallback(() => http.get('/aas/users', { params }), () => mock.listUsers(params))
}

export function createUser(data) {
  return withApiFallback(() => http.post('/aas/users', data), () => mock.createUser(data))
}

export function updateUser(userId, data) {
  return withApiFallback(() => http.put(`/aas/users/${userId}`, data), () =>
    mock.updateUser(userId, data),
  )
}

export function deleteUser(userId) {
  return withApiFallback(() => http.delete(`/aas/users/${userId}`), () => mock.deleteUser(userId))
}
