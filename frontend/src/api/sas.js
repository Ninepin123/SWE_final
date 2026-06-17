// SAS 學生申請 — API 呼叫（負責人：填上姓名）
// 對應後端 backend/app/modules/sas/router.py，路徑前綴 /api/sas
import http, { withApiFallback } from './http'
import * as mock from '@/services/mockBackend'

// 範例（骨架測試用，開發開始後可移除）：
export function ping() {
  return http.get('/sas/ping')
}

export function getProfile(userId) {
  return withApiFallback(() => http.get('/sas/profile'), () => mock.getProfile(userId))
}

export function updateProfile(userId, data) {
  return withApiFallback(() => http.put('/sas/profile', data), () => mock.updateProfile(userId, data))
}

export function listAvailableScholarships(studentId) {
  return withApiFallback(() => http.get('/sas/scholarships/available'), () =>
    mock.listAvailableScholarships(studentId),
  )
}

export function listMyApplications(studentId) {
  return withApiFallback(() => http.get('/sas/applications'), () =>
    mock.listApplicationsByStudent(studentId),
  )
}

export function getApplication(applicationId) {
  return withApiFallback(() => http.get(`/sas/applications/${applicationId}`), () =>
    mock.getApplication(applicationId),
  )
}

export function createApplication(studentId, data) {
  return withApiFallback(() => http.post('/sas/applications', data), () =>
    mock.createApplication(studentId, data),
  )
}

export function sendRecommendationReminder(studentId, requestId) {
  return withApiFallback(
    () => http.post(`/sas/recommendations/${requestId}/reminder`),
    () => mock.sendRecommendationReminder(studentId, requestId),
  )
}
