// TRS 教師推薦 — API 呼叫（負責人：填上姓名）
// 對應後端 backend/app/modules/trs/router.py，路徑前綴 /api/trs
import http, { withApiFallback } from './http'
import * as mock from '@/services/mockBackend'

// 範例（骨架測試用，開發開始後可移除）：
export function ping() {
  return http.get('/trs/ping')
}

export function listRecommendationRequests(recommenderId) {
  return withApiFallback(() => http.get('/trs/requests'), () =>
    mock.listRecommendationRequests(recommenderId),
  )
}

export function submitRecommendation(recommenderId, requestId, content) {
  return withApiFallback(
    () => http.post(`/trs/requests/${requestId}/letter/submit`, { content }),
    () => mock.submitRecommendation(recommenderId, requestId, content),
  )
}
