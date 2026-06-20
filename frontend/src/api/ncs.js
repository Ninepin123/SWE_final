import http, { withApiData } from './http'

function toVariant(category) {
  const value = String(category ?? '').toUpperCase()
  if (value.includes('ERROR') || value.includes('DANGER') || value.includes('REJECT')) return 'danger'
  if (value.includes('WARN') || value.includes('REMIND')) return 'warning'
  if (value.includes('SUCCESS') || value.includes('APPROVE')) return 'success'
  return 'info'
}

function normalizeNotification(item = {}) {
  const notificationId = item.notificationId ?? item.notification_id ?? item.id ?? null
  const userId = item.userId ?? item.user_id ?? null
  const category = item.category ?? item.type ?? null
  const isRead = item.isRead ?? item.is_read ?? item.read ?? false

  return {
    id: notificationId,
    notificationId,
    userId,
    title: item.title ?? '',
    body: item.body ?? item.message ?? '',
    category,
    relatedType: item.relatedType ?? item.related_type ?? null,
    relatedId: item.relatedId ?? item.related_id ?? null,
    isRead,
    createdAt: item.createdAt ?? item.created_at ?? new Date().toISOString(),
    readAt: item.readAt ?? item.read_at ?? null,
    type: item.type ?? toVariant(category),
  }
}

function normalizeAnnouncement(item = {}) {
  const announcementId = item.announcementId ?? item.announcement_id ?? item.id ?? null

  return {
    id: announcementId,
    announcementId,
    title: item.title ?? '',
    body: item.body ?? '',
    createdBy: item.createdBy ?? item.created_by ?? null,
    targetRole: item.targetRole ?? item.target_role ?? null,
    isGlobal: item.isGlobal ?? item.is_global ?? true,
    status: item.status ?? 'PUBLISHED',
    publishedAt: item.publishedAt ?? item.published_at ?? null,
    expiresAt: item.expiresAt ?? item.expires_at ?? null,
    createdAt: item.createdAt ?? item.created_at ?? null,
    updatedAt: item.updatedAt ?? item.updated_at ?? null,
  }
}

function toAnnouncementPayload(payload = {}) {
  return {
    title: payload.title,
    body: payload.body,
    target_role: payload.targetRole || null,
    is_global: payload.isGlobal ?? true,
    status: payload.status ?? 'PUBLISHED',
    expires_at: payload.expiresAt || null,
    notify_users: payload.notifyUsers ?? true,
  }
}

function normalizeIssue(item = {}) {
  const issueId = item.issueId ?? item.issue_id ?? item.id ?? null

  return {
    id: issueId,
    issueId,
    issue_id: issueId,
    reporterId: item.reporterId ?? item.reporter_id ?? null,
    reporter_id: item.reporterId ?? item.reporter_id ?? null,
    issueType: item.issueType ?? item.issue_type ?? 'BUG',
    issue_type: item.issueType ?? item.issue_type ?? 'BUG',
    title: item.title ?? '',
    description: item.description ?? '',
    attachmentName: item.attachmentName ?? item.attachment_name ?? '',
    attachment_name: item.attachmentName ?? item.attachment_name ?? '',
    attachmentUrl: item.attachmentUrl ?? item.attachment_url ?? '',
    attachment_url: item.attachmentUrl ?? item.attachment_url ?? '',
    status: item.status ?? 'OPEN',
    createdAt: item.createdAt ?? item.created_at ?? null,
    created_at: item.createdAt ?? item.created_at ?? null,
    updatedAt: item.updatedAt ?? item.updated_at ?? null,
    updated_at: item.updatedAt ?? item.updated_at ?? null,
  }
}

function normalizeIssueReply(item = {}) {
  const replyId = item.replyId ?? item.reply_id ?? item.id ?? null

  return {
    id: replyId,
    replyId,
    reply_id: replyId,
    issueId: item.issueId ?? item.issue_id ?? null,
    issue_id: item.issueId ?? item.issue_id ?? null,
    replierId: item.replierId ?? item.replier_id ?? null,
    replier_id: item.replierId ?? item.replier_id ?? null,
    body: item.body ?? '',
    createdAt: item.createdAt ?? item.created_at ?? null,
    created_at: item.createdAt ?? item.created_at ?? null,
  }
}

function normalizeSystemAlert(item = {}) {
  const alertId = item.alertId ?? item.alert_id ?? item.id ?? null

  return {
    id: alertId,
    alertId,
    alert_id: alertId,
    severity: item.severity ?? 'INFO',
    title: item.title ?? '',
    body: item.body ?? '',
    source: item.source ?? '',
    status: item.status ?? 'OPEN',
    createdAt: item.createdAt ?? item.created_at ?? null,
    created_at: item.createdAt ?? item.created_at ?? null,
    resolvedAt: item.resolvedAt ?? item.resolved_at ?? null,
    resolved_at: item.resolvedAt ?? item.resolved_at ?? null,
  }
}

// -------------------------
// Notifications
// -------------------------

export function listNotifications(params = {}) {
  const query = {
    unread_only: params.unreadOnly ?? false,
    limit: params.limit ?? 50,
    offset: params.offset ?? 0,
  }

  return withApiData(() => http.get('/ncs/notifications', { params: query }))
    .then((items) => (Array.isArray(items) ? items.map(normalizeNotification) : []))
}

export function getUnreadNotificationCount() {
  return withApiData(() => http.get('/ncs/notifications/unread-count'))
    .then((payload) => payload?.unread_count ?? payload?.unreadCount ?? payload?.count ?? 0)
}

export function markNotificationRead(notificationId) {
  return withApiData(() => http.patch(`/ncs/notifications/${notificationId}/read`))
    .then((item) => (item ? normalizeNotification(item) : null))
}

export function markAllNotificationsRead() {
  return withApiData(() => http.patch('/ncs/notifications/read-all')).then((payload) => ({
    updatedCount: payload?.updated_count ?? payload?.updatedCount ?? 0,
  }))
}

export function createNotification(payload) {
  return withApiData(() => http.post('/ncs/notifications', payload))
    .then((item) => (item ? normalizeNotification(item) : null))
}

// -------------------------
// Announcements
// -------------------------

export function listAnnouncements() {
  return withApiData(() => http.get('/ncs/announcements'))
    .then((items) => (Array.isArray(items) ? items.map(normalizeAnnouncement) : []))
}

export function listAdminAnnouncements() {
  return withApiData(() => http.get('/ncs/announcements/admin'))
    .then((items) => (Array.isArray(items) ? items.map(normalizeAnnouncement) : []))
}

export function createAnnouncement(payload) {
  return withApiData(() => http.post('/ncs/announcements', toAnnouncementPayload(payload)))
    .then((item) => (item ? normalizeAnnouncement(item) : null))
}

export function updateAnnouncement(announcementId, payload) {
  return withApiData(() => http.put(`/ncs/announcements/${announcementId}`, toAnnouncementPayload(payload)))
    .then((item) => (item ? normalizeAnnouncement(item) : null))
}

export function deleteAnnouncement(announcementId) {
  return withApiData(() => http.delete(`/ncs/announcements/${announcementId}`))
}

// -------------------------
// Deadline reminders
// -------------------------

export function runDeadlineReminders() {
  return withApiData(() => http.post('/ncs/deadline-reminders/run')).then((payload) => ({
    checkedCount: payload?.checked_count ?? payload?.checkedCount ?? 0,
    createdCount: payload?.created_count ?? payload?.createdCount ?? 0,
    skippedDuplicateCount: payload?.skipped_duplicate_count ?? payload?.skippedDuplicateCount ?? 0,
  }))
}

// -------------------------
// Application messages
// -------------------------

export function listApplicationMessages(applicationId) {
  return withApiData(() => http.get(`/ncs/applications/${applicationId}/messages`))
}

export function createApplicationMessage(applicationId, body) {
  return withApiData(() => http.post(`/ncs/applications/${applicationId}/messages`, { body }))
}

export function createIssueReport(payload) {
  return withApiData(() => http.post('/ncs/issues', payload))
    .then((item) => (item ? normalizeIssue(item) : null))
}

export function listMyIssues() {
  return withApiData(() => http.get('/ncs/issues/me'))
    .then((items) => (Array.isArray(items) ? items.map(normalizeIssue) : []))
}

export function listAllIssues() {
  return withApiData(() => http.get('/ncs/issues'))
    .then((items) => (Array.isArray(items) ? items.map(normalizeIssue) : []))
}

export function updateIssueReport(issueId, payload) {
  return withApiData(() => http.patch(`/ncs/issues/${issueId}`, payload))
    .then((item) => (item ? normalizeIssue(item) : null))
}

export function createIssueReply(issueId, body) {
  return withApiData(() => http.post(`/ncs/issues/${issueId}/replies`, { body }))
    .then((item) => (item ? normalizeIssueReply(item) : null))
}

export function listIssueReplies(issueId) {
  return withApiData(() => http.get(`/ncs/issues/${issueId}/replies`))
    .then((items) => (Array.isArray(items) ? items.map(normalizeIssueReply) : []))
}

// -------------------------
// System alerts
// -------------------------

export function listSystemAlerts() {
  return withApiData(() => http.get('/ncs/system-alerts'))
    .then((items) => (Array.isArray(items) ? items.map(normalizeSystemAlert) : []))
}

export function updateSystemAlert(alertId, payload) {
  return withApiData(() => http.patch(`/ncs/system-alerts/${alertId}`, payload))
    .then((item) => (item ? normalizeSystemAlert(item) : null))
}
