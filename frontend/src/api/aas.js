// AAS 帳號與權限管理 — API 呼叫（負責人：填上姓名）
// 對應後端 backend/app/modules/aas/router.py，路徑前綴 /api/aas
import http from './http'

export const ROLE_LABELS = {
  STUDENT: '學生',
  TEACHER: '教師',
  SPONSOR: '獎助單位人員',
  REVIEWER: '審查人員',
  ADMIN: '系統管理員',
}

export const UNIT_TYPE_LABELS = {
  SCHOOL: '校內',
  GOVERNMENT: '政府',
  PRIVATE: '民間／企業',
  OTHER: '其他',
}

export function ping() {
  return http.get('/aas/ping')
}

export function getMe() {
  return http.get('/aas/me').then((response) => response.data)
}

export function login(credentials) {
  return http.post('/aas/login', credentials).then((response) => response.data)
}

export function logout() {
  return http.post('/aas/logout').then((response) => response.data)
}

export function listUnits(params) {
  return http.get('/aas/units', { params }).then((response) => response.data)
}

export function createUnit(data) {
  return http.post('/aas/units', data).then((response) => response.data)
}

export function updateUnit(unitId, data) {
  return http.put(`/aas/units/${unitId}`, data).then((response) => response.data)
}

export function deleteUnit(unitId) {
  return http.delete(`/aas/units/${unitId}`).then((response) => response.data)
}

export function listUsers(params) {
  return http.get('/aas/users', { params }).then((response) => response.data)
}

export function createUser(data) {
  return http.post('/aas/users', data).then((response) => response.data)
}

export function updateUser(userId, data) {
  return http.put(`/aas/users/${userId}`, data).then((response) => response.data)
}

export function deleteUser(userId) {
  return http.delete(`/aas/users/${userId}`).then((response) => response.data)
}

export function listAuditLogs(params) {
  return http.get('/aas/audit-logs', { params }).then((response) => response.data)
}
