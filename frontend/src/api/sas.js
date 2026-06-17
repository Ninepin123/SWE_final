// SAS 學生申請 — API（對應 /api/sas）
import http from './http'

export function apply(payload) {
  return http.post('/sas/applications', payload)
}
export function listMyApplications() {
  return http.get('/sas/applications/me')
}
export function getProfile() {
  return http.get('/sas/profile')
}
export function updateProfile(payload) {
  return http.put('/sas/profile', payload)
}
