// TRS 教師推薦 — API 呼叫（負責人：填上姓名）
// 對應後端 backend/app/modules/trs/router.py，路徑前綴 /api/trs
import http, { withApiData } from './http'

export function ping() {
  return http.get('/trs/ping')
}

function normalizeRecommendation(item = {}) {
  const application = item.application ?? null
  const scholarship = application?.scholarship ?? null
  const student = application?.student ?? null

  const recId = item.recId ?? item.rec_id ?? item.id ?? null
  const applicationId = item.applicationId ?? item.application_id ?? application?.id ?? null
  const studentId = item.studentId ?? item.student_id ?? item.student?.id ?? application?.studentId ?? null
  const teacherId = item.teacherId ?? item.teacher_id ?? item.recommenderUserId ?? null
  const studentName = item.studentName ?? item.student_name ?? student?.name ?? null
  const scholarshipName =
    item.scholarshipName ?? item.scholarship_name ?? scholarship?.title ?? scholarship?.name ?? null
  const deadline = item.deadline ?? item.due_at ?? scholarship?.deadline ?? null
  const submittedAt = item.submittedAt ?? item.submitted_at ?? null

  return {
    id: recId,
    recId,
    applicationId,
    studentId,
    teacherId,
    studentName,
    studentAccount: item.studentAccount ?? item.student_account ?? student?.account ?? null,
    scholarshipName,
    deadline,
    status: item.status ?? 'REQUESTED',
    content: item.content ?? '',
    submittedAt,
  }
}

function normalizeStudentRecommendationStatus(item = {}) {
  return {
    recId: item.recId ?? item.rec_id ?? item.id ?? null,
    applicationId: item.applicationId ?? item.application_id ?? null,
    teacherName: item.teacherName ?? item.teacher_name ?? null,
    scholarshipName: item.scholarshipName ?? item.scholarship_name ?? null,
    status: item.status ?? 'REQUESTED',
    submittedAt: item.submittedAt ?? item.submitted_at ?? null,
  }
}

function normalizeRecommendationStudentProfile(item = {}) {
  const student = item.student ?? {}
  const profile = item.profile ?? null
  const application = item.application ?? {}
  const scholarship = item.scholarship ?? {}
  const documents = Array.isArray(item.documents) ? item.documents : []

  return {
    recId: item.recId ?? item.rec_id ?? null,
    applicationId: item.applicationId ?? item.application_id ?? application.applicationId ?? application.application_id ?? null,
    status: item.status ?? 'REQUESTED',
    student: {
      userId: student.userId ?? student.user_id ?? null,
      name: student.name ?? '',
      account: student.account ?? '',
      email: student.email ?? null,
    },
    profile: profile
      ? {
          grade: profile.grade ?? null,
          identityType: profile.identityType ?? profile.identity_type ?? null,
          contactEmail: profile.contactEmail ?? profile.contact_email ?? null,
          contactPhone: profile.contactPhone ?? profile.contact_phone ?? null,
          address: profile.address ?? null,
          emergencyContactName:
            profile.emergencyContactName ?? profile.emergency_contact_name ?? null,
          emergencyContactPhone:
            profile.emergencyContactPhone ?? profile.emergency_contact_phone ?? null,
        }
      : null,
    application: {
      applicationId:
        application.applicationId ?? application.application_id ?? item.applicationId ?? item.application_id ?? null,
      status: application.status ?? null,
      submittedAt: application.submittedAt ?? application.submitted_at ?? null,
    },
    scholarship: {
      scholarshipId: scholarship.scholarshipId ?? scholarship.scholarship_id ?? null,
      name: scholarship.name ?? scholarship.title ?? '',
      deadline: scholarship.deadline ?? null,
    },
    documents: documents.map((document) => ({
      documentId: document.documentId ?? document.document_id ?? null,
      documentType: document.documentType ?? document.document_type ?? '',
      title: document.title ?? '',
      contentText: document.contentText ?? document.content_text ?? '',
    })),
  }
}

function normalizeRecommendationDashboard(item = {}) {
  return {
    totalCount: item.totalCount ?? item.total_count ?? 0,
    pendingCount: item.pendingCount ?? item.pending_count ?? 0,
    draftCount: item.draftCount ?? item.draft_count ?? 0,
    submittedCount: item.submittedCount ?? item.submitted_count ?? 0,
    dueSoonCount: item.dueSoonCount ?? item.due_soon_count ?? 0,
    overdueCount: item.overdueCount ?? item.overdue_count ?? 0,
  }
}

export function listTeacherRecommendations(paramsOrRecommenderUserId, recommenderUserId) {
  const isLegacyCall =
    typeof paramsOrRecommenderUserId === 'string' ||
    typeof paramsOrRecommenderUserId === 'number' ||
    paramsOrRecommenderUserId == null

  const params = isLegacyCall
    ? {}
    : {
        keyword: paramsOrRecommenderUserId.keyword ?? undefined,
        status: paramsOrRecommenderUserId.status ?? undefined,
        sort_by: paramsOrRecommenderUserId.sortBy ?? undefined,
        order: paramsOrRecommenderUserId.order ?? undefined,
      }
  return withApiData(() => http.get('/trs/recommendations/teacher', { params }))
    .then((items) => (Array.isArray(items) ? items.map(normalizeRecommendation) : []))
}

export function saveRecommendationDraft(recId, content, recommenderUserId) {
  return withApiData(() => http.put(`/trs/recommendations/${recId}`, { content, submit: false }))
    .then(normalizeRecommendation)
}

export function submitRecommendation(recId, content, recommenderUserId) {
  return withApiData(() => http.put(`/trs/recommendations/${recId}`, { content, submit: true }))
    .then(normalizeRecommendation)
}

export function listStudentRecommendationStatus() {
  return withApiData(() => http.get('/trs/recommendations/student'))
    .then((items) => (Array.isArray(items) ? items.map(normalizeStudentRecommendationStatus) : []))
}

export function getRecommendationStudentProfile(recId, recommenderUserId) {
  return withApiData(() => http.get(`/trs/recommendations/${recId}/student-profile`))
    .then(normalizeRecommendationStudentProfile)
}

export function getTeacherRecommendationDashboard(recommenderUserId) {
  return withApiData(() => http.get('/trs/recommendations/teacher/dashboard'))
    .then(normalizeRecommendationDashboard)
}

// backward compatibility for existing imports
export function listRecommendationRequests(recommenderUserId) {
  return listTeacherRecommendations(recommenderUserId)
}
