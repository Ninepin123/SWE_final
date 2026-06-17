// NCS 通知與溝通 — API 呼叫（負責人：填上姓名）
// 對應後端 backend/app/modules/ncs/router.py，路徑前綴 /api/ncs
import http, { withApiFallback } from './http'
import * as mock from '@/services/mockBackend'

// 範例（骨架測試用，開發開始後可移除）：
export function ping() {
  return http.get('/ncs/ping')
}

export function listNotifications(userId) {
  return withApiFallback(() => http.get('/ncs/notifications'), () => mock.listNotifications(userId))
}

export function markNotificationRead(userId, notificationId) {
  return withApiFallback(() => http.put(`/ncs/notifications/${notificationId}/read`), () =>
    mock.markNotificationRead(userId, notificationId),
  )
}
