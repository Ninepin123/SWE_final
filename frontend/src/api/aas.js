// AAS 帳號與權限管理 — API（對應 /api/aas）
import http from './http'

export function login(account, password) {
  return http.post('/aas/login', { account, password })
}
export function logout() {
  return http.post('/aas/logout')
}
export function getMe() {
  return http.get('/aas/me')
}
export function listTeachers() {
  return http.get('/aas/teachers')
}
export function listUsers() {
  return http.get('/aas/users')
}
export function createUser(payload) {
  return http.post('/aas/users', payload)
}
export function updateUser(id, payload) {
  return http.put(`/aas/users/${id}`, payload)
}
export function deleteUser(id) {
  return http.delete(`/aas/users/${id}`)
}
export function listAuditLogs() {
  return http.get('/aas/audit-logs')
}
