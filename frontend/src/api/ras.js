// RAS 審查與核發 — API 呼叫（負責人：填上姓名）
// 對應後端 backend/app/modules/ras/router.py，路徑前綴 /api/ras
import http, { withApiFallback } from './http'
import * as mock from '@/services/mockBackend'

// 範例（骨架測試用，開發開始後可移除）：
export function ping() {
  return http.get('/ras/ping')
}

export function listReviewApplications(params) {
  return withApiFallback(() => http.get('/ras/applications', { params }), () =>
    mock.listReviewApplications(params),
  )
}

export function submitReviewDecision(reviewerId, applicationId, decision) {
  return withApiFallback(
    () => http.post(`/ras/applications/${applicationId}/decision`, decision),
    () => mock.submitReviewDecision(reviewerId, applicationId, decision),
  )
}

export function requestSupplement(reviewerId, applicationId, comment) {
  return withApiFallback(
    () => http.post(`/ras/applications/${applicationId}/supplement-request`, { comment }),
    () => mock.requestSupplement(reviewerId, applicationId, comment),
  )
}
