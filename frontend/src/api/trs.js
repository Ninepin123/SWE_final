// TRS 教師推薦 — API（對應 /api/trs）
import http from './http'

// 學生：邀請老師推薦
export function requestRecommendation(payload) {
  return http.post('/trs/recommendations', payload)
}
// 學生：查看自己各申請的推薦狀態（無內容）
export function listMyRecommendations() {
  return http.get('/trs/recommendations/student')
}
// 老師：查看被指派的推薦邀請（含內容）
export function listTeacherRecommendations() {
  return http.get('/trs/recommendations/teacher')
}
// 老師：存草稿 / 送出
export function saveRecommendation(recId, payload) {
  return http.put(`/trs/recommendations/${recId}`, payload)
}
