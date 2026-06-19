// AAS 帳號與權限管理 — API 呼叫（負責人：填上姓名）
// 對應後端 backend/app/modules/aas/router.py，路徑前綴 /api/aas
import http, { useMockApi } from './http'
import * as mock from '@/services/mockBackend'

export const ROLE_LABELS = {
  STUDENT: '學生',
  TEACHER: '教師',
  SPONSOR: '獎助單位人員',
  REVIEWER: '審查人員',
  ADMIN: '系統管理員',
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
  if (useMockApi) return mock.listUsers(params)
  return http.get('/aas/users', { params }).then((response) => response.data)
}

export function createUser(data) {
  if (useMockApi) return mock.createUser(data)
  return http.post('/aas/users', data).then((response) => response.data)
}

export function updateUser(userId, data) {
  if (useMockApi) return mock.updateUser(userId, data)
  return http.put(`/aas/users/${userId}`, data).then((response) => response.data)
}

export function deleteUser(userId) {
  if (useMockApi) return mock.deleteUser(userId)
  return http.delete(`/aas/users/${userId}`).then((response) => response.data)
}

export function listAuditLogs(params) {
  if (useMockApi) return Promise.resolve([])
  return http.get('/aas/audit-logs', { params }).then((response) => response.data)
}
