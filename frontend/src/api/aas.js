// AAS 帳號與權限管理 — API 呼叫
// 對應後端 backend/app/modules/aas/router.py，路徑前綴 /api/aas
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

export function listUsers() {
  return http.get('/aas/users')
}

export function createUser(payload) {
  return http.post('/aas/users', payload)
}
