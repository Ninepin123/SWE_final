// SMS 獎助學金資料管理 — API 呼叫（負責人：填上姓名）
// 對應後端 backend/app/modules/sms/router.py，路徑前綴 /api/sms
import http, { withApiFallback } from './http'
import * as mock from '@/services/mockBackend'

// 範例（骨架測試用，開發開始後可移除）：
export function ping() {
  return http.get('/sms/ping')
}

export function listScholarships(params) {
  return withApiFallback(() => http.get('/sms/scholarships', { params }), () =>
    mock.listScholarships(params),
  )
}

export function getScholarship(scholarshipId) {
  return withApiFallback(() => http.get(`/sms/scholarships/${scholarshipId}`), () =>
    mock.getScholarship(scholarshipId),
  )
}

export function createScholarship(data) {
  return withApiFallback(() => http.post('/sms/scholarships', data), () =>
    mock.createScholarship(data),
  )
}

export function updateScholarship(scholarshipId, data) {
  return withApiFallback(() => http.put(`/sms/scholarships/${scholarshipId}`, data), () =>
    mock.updateScholarship(scholarshipId, data),
  )
}

export function deleteScholarship(scholarshipId) {
  return withApiFallback(() => http.delete(`/sms/scholarships/${scholarshipId}`), () =>
    mock.deleteScholarship(scholarshipId),
  )
}

export function getOptions(type) {
  return withApiFallback(() => http.get('/sms/options', { params: type ? { type } : undefined }), () =>
    mock.getOptions(type ? { type } : {})
  )
}

export function createOption(data) {
  return withApiFallback(() => http.post('/sms/options', data), () =>
    mock.createOption(data)
  )
}

export function updateOption(id, data) {
  return withApiFallback(() => http.put(`/sms/options/${id}`, data), () =>
    mock.updateOption(id, data)
  )
}

export function deleteOption(id) {
  return withApiFallback(() => http.delete(`/sms/options/${id}`), () =>
    mock.deleteOption(id)
  )
}
