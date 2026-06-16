// RAS 審查與核發 — API 呼叫
// 對應後端 backend/app/modules/ras/router.py，路徑前綴 /api/ras
import http from './http'

export function listReviewApplications(params) {
  return http.get('/ras/applications', { params })
}

export function decide(applicationId, payload) {
  return http.post(`/ras/applications/${applicationId}/decision`, payload)
}
