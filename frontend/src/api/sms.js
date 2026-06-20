// SMS 獎助學金資料管理 — API 呼叫（負責人：填上姓名）
// 對應後端 backend/app/modules/sms/router.py，路徑前綴 /api/sms
import http, { withApiData } from './http'

export function ping() {
  return http.get('/sms/ping')
}

export function listScholarships(params) {
  return withApiData(() => http.get('/sms/scholarships', { params }))
}

export function getScholarship(scholarshipId) {
  return withApiData(() => http.get(`/sms/scholarships/${scholarshipId}`))
}

export function createScholarship(data) {
  return withApiData(() => http.post('/sms/scholarships', data))
}

export function updateScholarship(scholarshipId, data) {
  return withApiData(() => http.put(`/sms/scholarships/${scholarshipId}`, data))
}

export function deleteScholarship(scholarshipId) {
  return withApiData(() => http.delete(`/sms/scholarships/${scholarshipId}`))
}

// 分類／標籤建議清單；新分類與標籤會在獎學金存檔時由後端自動登記。
export function getOptions(type) {
  return withApiData(() => http.get('/sms/options', { params: type ? { type } : undefined }))
}
