// SAS 學生申請 — API 呼叫（負責人：填上姓名）
// 對應後端 backend/app/modules/sas/router.py，路徑前綴 /api/sas
import http from './http'

const UNLIMITED_DEPARTMENTS = ['不限', '不限科系', 'ALL']

// 解析後端的科系限制字串：可能是 JSON 陣列（複選結果）或舊的分隔符純文字；
// 「不限科系」語意或空值都回傳空陣列（代表不限）。
function parseDepartmentLimit(value) {
  if (!value || UNLIMITED_DEPARTMENTS.includes(String(value).trim())) return []
  const text = String(value).trim()
  let items = null
  if (text.startsWith('[')) {
    try {
      const parsed = JSON.parse(text)
      if (Array.isArray(parsed)) items = parsed.map((d) => String(d).trim())
    } catch {
      items = null
    }
  }
  if (items === null) {
    items = text.split(/[,，、;/]/).map((d) => d.trim())
  }
  return items.filter((d) => d && !UNLIMITED_DEPARTMENTS.includes(d))
}

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
      departmentLimit: parseDepartmentLimit(item.department_limit).join('、'),
      category: item.category,
      description: item.description,
      deadline: item.deadline,
      status: item.status,
      sponsor: item.unit_name,
      contactEmail: item.contact_email,
      requiredDocs: item.required_documents,
      requireRecommendation: item.require_recommendation ?? item.requireRecommendation ?? false,
      alreadyApplied: item.already_applied,
      canApply: item.can_apply,
      ineligibilityReasons: item.ineligibility_reasons,
      // 後端目前只提供科系限制字串，仍給齊 criteria 物件以符合前端契約，
      // 避免畫面存取 item.criteria.* 時因 undefined 而整頁渲染崩潰。
      criteria: {
        departments: parseDepartmentLimit(item.department_limit),
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
