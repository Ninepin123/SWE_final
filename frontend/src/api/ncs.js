// NCS 通知與溝通 — API（對應 /api/ncs）
import http from './http'

export function listNotifications() {
  return http.get('/ncs/notifications')
}
export function unreadCount() {
  return http.get('/ncs/notifications/unread_count')
}
export function markRead(id) {
  return http.post(`/ncs/notifications/${id}/read`)
}
export function listAnnouncements() {
  return http.get('/ncs/announcements')
}
export function createAnnouncement(payload) {
  return http.post('/ncs/announcements', payload)
}
