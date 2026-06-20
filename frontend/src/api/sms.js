// SMS 獎助學金資料管理 — API 呼叫（負責人：填上姓名）
// 對應後端 backend/app/modules/sms/router.py，路徑前綴 /api/sms
import http, { withApiData } from './http'

function resolveScholarshipId(scholarship) {
  return scholarship?.id ?? scholarship?.scholarshipId ?? scholarship?.scholarship_id
}

function assertScholarshipId(scholarshipOrId) {
  const scholarshipId =
    typeof scholarshipOrId === 'object' ? resolveScholarshipId(scholarshipOrId) : scholarshipOrId
  if (scholarshipId === undefined || scholarshipId === null || scholarshipId === '') {
    throw new Error('缺少獎學金編號，無法送出操作。')
  }
  return scholarshipId
}

function normalizeCriteria(criteria) {
  const source = criteria ?? {}
  return {
    ...source,
    minGpa: source.minGpa ?? source.min_gpa ?? null,
    familyStatuses: source.familyStatuses ?? source.family_statuses ?? [],
  }
}

function normalizeScholarship(item) {
  if (!item) return item
  const id = resolveScholarshipId(item)
  const unitId = item.unitId ?? item.unit_id
  const usedQuota = item.usedQuota ?? item.used_quota ?? 0

  return {
    ...item,
    id,
    scholarshipId: id,
    scholarship_id: id,
    title: item.title ?? item.name,
    unitId,
    unit_id: unitId,
    usedQuota,
    used_quota: usedQuota,
    startDate: item.startDate ?? item.start_date ?? '',
    start_date: item.start_date ?? item.startDate ?? '',
    requiredDocs: item.requiredDocs ?? item.required_docs ?? [],
    required_docs: item.required_docs ?? item.requiredDocs ?? [],
    requireRecommendation: item.requireRecommendation ?? item.require_recommendation ?? false,
    require_recommendation: item.require_recommendation ?? item.requireRecommendation ?? false,
    contactName: item.contactName ?? item.contact_name ?? '',
    contactPhone: item.contactPhone ?? item.contact_phone ?? '',
    contactEmail: item.contactEmail ?? item.contact_email ?? '',
    contactAddress: item.contactAddress ?? item.contact_address ?? '',
    isOpen: item.isOpen ?? item.is_open ?? false,
    criteria: normalizeCriteria(item.criteria),
    tags: item.tags ?? [],
  }
}

function normalizeScholarships(items) {
  return Array.isArray(items) ? items.map(normalizeScholarship) : []
}

export function ping() {
  return http.get('/sms/ping')
}

export function listScholarships(params) {
  return withApiData(() => http.get('/sms/scholarships', { params })).then(normalizeScholarships)
}

export function getScholarship(scholarshipId) {
  return withApiData(() => http.get(`/sms/scholarships/${assertScholarshipId(scholarshipId)}`)).then(
    normalizeScholarship,
  )
}

export function createScholarship(data) {
  return withApiData(() => http.post('/sms/scholarships', data)).then(normalizeScholarship)
}

export function updateScholarship(scholarshipId, data) {
  return withApiData(() =>
    http.put(`/sms/scholarships/${assertScholarshipId(scholarshipId)}`, data),
  ).then(normalizeScholarship)
}

export function deleteScholarship(scholarshipId) {
  return withApiData(() => http.delete(`/sms/scholarships/${assertScholarshipId(scholarshipId)}`))
}

// 分類／標籤建議清單；新分類與標籤會在獎學金存檔時由後端自動登記。
export function getOptions(type) {
  return withApiData(() => http.get('/sms/options', { params: type ? { type } : undefined }))
}
