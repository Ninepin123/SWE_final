// SAS 學生申請 — API 呼叫（負責人：填上姓名）
// 對應後端 backend/app/modules/sas/router.py，路徑前綴 /api/sas
import http from './http'

export function ping() {
  return http.get('/sas/ping')
}

export function getProfile(userId) {
  return http.get('/sas/profile').then((response) => response.data)
}

export function updateProfile(userId, data) {
  return http.put('/sas/profile', data).then((response) => response.data)
}

export function listAvailableScholarships(studentId) {
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
      // 後端目前只提供科系限制字串，仍給齊 criteria 物件以符合前端契約，
      // 避免畫面存取 item.criteria.* 時因 undefined 而整頁渲染崩潰。
      criteria: {
        departments:
          item.department_limit && item.department_limit !== '不限科系'
            ? [item.department_limit]
            : [],
        grades: [],
        identities: [],
        familyStatuses: [],
      },
    })),
  )
}

export function listMyApplications(studentId) {
  return http.get('/sas/applications/me').then((response) => response.data)
}

export function getApplication(applicationId) {
  return http.get(`/sas/applications/${applicationId}`).then((response) => response.data)
}

export function listApplicationEvents(applicationId) {
  return http.get(`/sas/applications/${applicationId}/events`).then((response) =>
    response.data.map((event) => ({
      id: event.event_id,
      action: event.event_type,
      actorName: event.actor_name || '系統',
      actorRole: event.actor_role || 'SYSTEM',
      fromStatus: event.from_status,
      toStatus: event.to_status,
      comment: event.detail,
      createdAt: event.created_at,
    })),
  )
}

export function createApplication(studentId, data) {
  return http.post('/sas/applications', data).then((response) => response.data)
}

export function updateApplication(applicationId, data) {
  return http.put(`/sas/applications/${applicationId}`, data).then((response) => response.data)
}

export function submitApplication(applicationId) {
  return http.post(`/sas/applications/${applicationId}/submit`).then((response) => response.data)
}

export function listApplicationDocuments(applicationId) {
  return http
    .get(`/sas/applications/${applicationId}/documents`)
    .then((response) => response.data)
}

export function saveApplicationDocument(applicationId, data) {
  return http
    .post(`/sas/applications/${applicationId}/documents`, data)
    .then((response) => response.data)
}

export function deleteApplicationDocument(applicationId, documentId) {
  return http
    .delete(`/sas/applications/${applicationId}/documents/${documentId}`)
    .then((response) => response.data)
}

export function createSupplementRequest(applicationId, data) {
  return http
    .post(`/sas/applications/${applicationId}/supplement-requests`, data)
    .then((response) => response.data)
}

export function listSupplementRequests(applicationId) {
  return http
    .get(`/sas/applications/${applicationId}/supplement-requests`)
    .then((response) => response.data)
}

export function submitSupplement(applicationId, supplementId, data) {
  return http
    .post(
      `/sas/applications/${applicationId}/supplement-requests/${supplementId}/submit`,
      data,
    )
    .then((response) => response.data)
}
