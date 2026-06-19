// SAS 學生申請 — API 呼叫（負責人：填上姓名）
// 對應後端 backend/app/modules/sas/router.py，路徑前綴 /api/sas
import http, { useMockApi, withApiFallback } from './http'
import * as mock from '@/services/mockBackend'

// 範例（骨架測試用，開發開始後可移除）：
export function ping() {
  return http.get('/sas/ping')
}

export function getProfile(userId) {
  if (useMockApi) return mock.getProfile(userId)
  return http.get('/sas/profile').then((response) => response.data)
}

export function updateProfile(userId, data) {
  if (useMockApi) return mock.updateProfile(userId, data)
  return http.put('/sas/profile', data).then((response) => response.data)
}

export function listAvailableScholarships(studentId) {
  if (useMockApi) return mock.listAvailableScholarships(studentId)
  return http.get('/sas/scholarships/available').then((response) =>
    response.data.map((item) => ({
      id: item.scholarship_id,
      title: item.name,
      year: item.year,
      amount: item.amount,
      quota: item.quota,
      seatsLeft: item.remaining_quota,
      minGpa: item.min_gpa,
      departmentLimit: item.department_limit,
      category: item.category,
      description: item.description,
      deadline: item.deadline,
      status: item.status,
      sponsor: item.unit_name,
      contactEmail: item.contact_email,
      requiredDocs: item.required_documents,
      alreadyApplied: item.already_applied,
      canApply: item.can_apply,
      ineligibilityReasons: item.ineligibility_reasons,
    })),
  )
}

export function listMyApplications(studentId) {
  if (useMockApi) return mock.listApplicationsByStudent(studentId)
  return http.get('/sas/applications/me').then((response) => response.data)
}

export function getApplication(applicationId) {
  if (useMockApi) return mock.getApplication(applicationId)
  return http.get(`/sas/applications/${applicationId}`).then((response) => response.data)
}

export function createApplication(studentId, data) {
  if (useMockApi) return mock.createApplication(studentId, data)
  return http.post('/sas/applications', data).then((response) => response.data)
}

export function updateApplication(applicationId, data) {
  return http.put(`/sas/applications/${applicationId}`, data).then((response) => response.data)
}

export function submitApplication(applicationId) {
  return http.post(`/sas/applications/${applicationId}/submit`).then((response) => response.data)
}

export function sendRecommendationReminder(studentId, requestId) {
  return withApiFallback(
    () => http.post(`/sas/recommendations/${requestId}/reminder`),
    () => mock.sendRecommendationReminder(studentId, requestId),
  )
}
