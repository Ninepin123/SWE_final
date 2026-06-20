// RAS 審查與核發 — API 呼叫（負責人：填上姓名）
// 對應後端 backend/app/modules/ras/router.py，路徑前綴 /api/ras
import http, { withApiFallback } from './http'
import * as mock from '@/services/mockBackend'

// 範例（骨架測試用，開發開始後可移除）：
export function ping() {
  return http.get('/ras/ping')
}

function normalizeRecommendation(item = {}) {
  const status = item.status ?? 'REQUESTED'
  return {
    id: item.id ?? item.rec_id ?? null,
    recommenderName: item.recommenderName ?? item.teacher_name ?? '-',
    recommenderTitle: item.recommenderTitle ?? '',
    relationship: item.relationship ?? '',
    status,
    content: item.content_available === false ? null : (item.content ?? null),
    contentAvailable: item.contentAvailable ?? item.content_available ?? status === 'SUBMITTED',
  }
}

function normalizeReviewApplication(item = {}) {
  const scholarshipTitle = item.scholarship?.title ?? item.scholarship_name ?? '-'
  const scholarshipCategory = item.scholarship?.category ?? item.scholarship_category ?? ''
  const studentName = item.student?.name ?? item.student_name ?? '-'
  const department = item.profile?.department ?? item.department ?? ''
  const gpa = item.gpa ?? item.form?.academics?.gpa ?? null
  const recommendations = Array.isArray(item.recommendations)
    ? item.recommendations.map(normalizeRecommendation)
    : []

  const auditLogs = Array.isArray(item.auditLogs)
    ? item.auditLogs
    : item.reviewed_at
      ? [
          {
            id: `review-${item.application_id}`,
            actorName: item.reviewer_name ?? '審查人員',
            action: '審查紀錄',
            result: item.review_result ?? '-',
            comment: item.review_comment ?? '',
            createdAt: item.reviewed_at,
          },
        ]
      : []

  return {
    id: item.id ?? item.application_id,
    application_id: item.application_id,
    scholarship: {
      title: scholarshipTitle,
      category: scholarshipCategory,
    },
    student: {
      name: studentName,
    },
    profile: {
      department,
    },
    submittedAt: item.submittedAt ?? item.submitted_at ?? item.createdAt ?? item.created_at ?? null,
    status: item.status,
    form: {
      academics: {
        gpa,
        credits: item.form?.academics?.credits ?? '-',
      },
      finance: {
        familyStatus: item.form?.finance?.familyStatus ?? item.household_status ?? '-',
      },
      statement: item.form?.statement ?? item.statement ?? '-',
    },
    documents: Array.isArray(item.documents) ? item.documents : [],
    recommendations,
    auditLogs,
  }
}

export function listReviewApplications(params) {
  return withApiFallback(() => http.get('/ras/applications', { params }), () =>
    mock.listReviewApplications(params),
  ).then((items) => (Array.isArray(items) ? items.map(normalizeReviewApplication) : []))
}

export function submitReviewDecision(reviewerId, applicationId, decision) {
  return withApiFallback(
    () => http.post(`/ras/applications/${applicationId}/decision`, decision),
    () => mock.submitReviewDecision(reviewerId, applicationId, decision),
  )
}

export function requestSupplement(reviewerId, applicationId, comment, deadline) {
  return withApiFallback(
    () => http.post(`/ras/applications/${applicationId}/decision`, { result: 'NEED_SUPPLEMENT', comment, supplement_deadline: deadline }),
    () => mock.submitReviewDecision(reviewerId, applicationId, { result: 'NEED_SUPPLEMENT', comment, supplement_deadline: deadline }),
  )
}

export function logView(applicationId) {
  return withApiFallback(
    () => http.post(`/ras/applications/${applicationId}/view`),
    () => Promise.resolve({ detail: '已記錄查看操作' })
  )
}

export function getAwardList(params) {
  return withApiFallback(
    () => http.get('/ras/award-list', { params }),
    () => mock.getAwardList(params)
  )
}

export function getStatistics(params) {
  return withApiFallback(
    () => http.get('/ras/statistics', { params }),
    () => mock.getStatistics(params)
  )
}

export function exportStatisticsCsv(params) {
  return http.get('/ras/statistics/export', { params, responseType: 'blob' })
    .then(response => {
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', params?.year ? `statistics_${params.year}.csv` : 'statistics_all.csv')
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
    })
    .catch(async () => {
      // fallback mock download
      const csvContent = await mock.exportStatisticsCsvData(params)
      // 加入 BOM 讓 Excel 可以正確顯示中文
      const blob = new Blob([new Uint8Array([0xEF, 0xBB, 0xBF]), csvContent], { type: 'text/csv;charset=utf-8;' })
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', params?.year ? `mock_statistics_${params.year}.csv` : 'mock_statistics_all.csv')
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
    })
}
