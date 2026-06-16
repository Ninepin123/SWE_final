// SMS 獎助學金資料管理 — API 呼叫
// 對應後端 backend/app/modules/sms/router.py，路徑前綴 /api/sms
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
