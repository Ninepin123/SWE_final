// SMS 獎助學金資料管理 — API（對應 /api/sms）
import http from './http'

export function listScholarships(params) {
  return http.get('/sms/scholarships', { params })
}
export function getScholarship(id) {
  return http.get(`/sms/scholarships/${id}`)
}
export function createScholarship(payload) {
  return http.post('/sms/scholarships', payload)
}
export function updateScholarship(id, payload) {
  return http.put(`/sms/scholarships/${id}`, payload)
}
export function deleteScholarship(id) {
  return http.delete(`/sms/scholarships/${id}`)
}
