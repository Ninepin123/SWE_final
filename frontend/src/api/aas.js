// AAS 帳號與權限管理 — API 呼叫（負責人：填上姓名）
// 對應後端 backend/app/modules/aas/router.py，路徑前綴 /api/aas
import http, { withApiFallback } from './http'
import * as mock from '@/services/mockBackend'

// 範例（骨架測試用，開發開始後可移除）：
export function ping() {
  return http.get('/aas/ping')
}

export function getMe() {
  return withApiFallback(() => http.get('/aas/me'), () => mock.fetchMe())
}

export function loginAs(role) {
  return mock.loginAs(role)
}

export function logout() {
  return mock.logout()
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
