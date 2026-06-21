<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import AuditTimeline from '@/components/common/AuditTimeline.vue'
import BaseCard from '@/components/common/BaseCard.vue'
import BaseModal from '@/components/common/BaseModal.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import MessageBoard from '@/components/common/MessageBoard.vue'
import Icon from '@/components/common/Icon.vue'
import LoadingSkeleton from '@/components/common/LoadingSkeleton.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import {
  listReviewApplications,
  requestSupplement,
  submitReviewDecision,
  logView,
} from '@/api/ras'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'

const auth = useAuthStore()
const toast = useToastStore()
const loading = ref(true)
const applications = ref([])
const keyword = ref('')
const statusFilter = ref('')
const sortBy = ref('gpa_desc')
const selected = ref(null)
const error = ref('')
const activeDetailTab = ref('decision')
const savingDecision = ref(false)
const sendingSupplement = ref(false)
const decision = reactive({
  result: 'APPROVED',
  comment: '',
  deadline: ''
})
const detailTabs = [
  { value: 'decision', label: '審查', icon: 'review' },
  { value: 'application', label: '資料', icon: 'application' },
  { value: 'documents', label: '文件與推薦', icon: 'archive' },
  { value: 'activity', label: '紀錄留言', icon: 'clock' },
]

const filteredApplications = computed(() => {
  const query = keyword.value.trim().toLowerCase()
  return applications.value.filter((application) => {
    const matchedKeyword =
      !query ||
      [
        application.student?.name,
        application.profile?.department,
        application.scholarship?.title,
        application.scholarship?.category,
      ]
        .filter(Boolean)
        .some((field) => field.toLowerCase().includes(query))
    const matchedStatus = !statusFilter.value || application.status === statusFilter.value
    return matchedKeyword && matchedStatus
  })
})

function formatDate(value) {
  if (!value) return '-'
  return new Intl.DateTimeFormat('zh-TW', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(value))
}

async function reload() {
  applications.value = await listReviewApplications({ sort_by: sortBy.value })
}

async function openDetail(application) {
  selected.value = application
  decision.result = 'APPROVED'
  decision.comment = ''
  decision.deadline = ''
  activeDetailTab.value = 'decision'
  error.value = ''
  // Log the view action in the backend
  try {
    await logView(application.id)
  } catch (e) {
    console.error('Failed to log view:', e)
  }
}

async function saveDecision() {
  error.value = ''
  if (!decision.comment.trim()) {
    error.value = '請填寫審查意見。'
    return
  }
  const applicationId = selected.value.id
  savingDecision.value = true
  try {
    await submitReviewDecision(auth.user.id, applicationId, { ...decision })
    toast.success('審查結果已送出並留下紀錄')
    await reload()
    selected.value = null
  } catch (saveError) {
    error.value = saveError.response?.data?.detail || saveError.message || '審查結果送出失敗'
  } finally {
    savingDecision.value = false
  }
}

async function supplement() {
  error.value = ''
  if (!decision.comment.trim()) {
    error.value = '請填寫補件要求。'
    return
  }
  if (!decision.deadline) {
    error.value = '請設定補交期限。'
    return
  }
  const applicationId = selected.value.id
  sendingSupplement.value = true
  try {
    await requestSupplement(auth.user.id, applicationId, decision.comment, decision.deadline)
    toast.success('補件通知已送出並留下紀錄')
    await reload()
    selected.value = null
  } catch (supplementError) {
    error.value = supplementError.response?.data?.detail || supplementError.message || '補件通知送出失敗'
  } finally {
    sendingSupplement.value = false
  }
}

function previewDocument(doc) {
  // Simulate opening document
  toast.info(`正在開啟附件：${doc}`)
  setTimeout(() => {
    toast.success(`附件 ${doc} 已下載/開啟完成。`)
  }, 1000)
}

onMounted(async () => {
  await reload()
  loading.value = false
})
</script>

<template>
  <div class="page-grid">
    <BaseCard title="審查工作台" eyebrow="Review">
      <div class="toolbar">
        <label class="search-field">
          <span>搜尋</span>
          <input v-model="keyword" type="search" placeholder="學生、科系、獎學金" />
        </label>
        <label>
          <span>狀態</span>
          <select v-model="statusFilter">
            <option value="">全部</option>
            <option value="UNDER_REVIEW">審查中</option>
            <option value="NEED_SUPPLEMENT">需補件</option>
            <option value="APPROVED">已通過</option>
            <option value="REJECTED">未通過</option>
          </select>
        </label>
        <label>
          <span>排序</span>
          <select v-model="sortBy" @change="reload">
            <option value="gpa_desc">GPA (由高到低)</option>
            <option value="gpa_asc">GPA (由低到高)</option>
            <option value="time_desc">送出時間 (新到舊)</option>
            <option value="time_asc">送出時間 (舊到新)</option>
          </select>
        </label>
      </div>
    </BaseCard>

    <LoadingSkeleton v-if="loading" :rows="5" />
    <EmptyState
      v-else-if="!filteredApplications.length"
      title="目前沒有符合條件的申請案"
      description="調整搜尋或狀態篩選後再試一次。"
      icon="review"
    />

    <BaseCard v-else>
      <div class="table-wrap">
        <table class="data-table">
          <thead>
            <tr>
              <th>申請案</th>
              <th>學生</th>
              <th>送出時間</th>
              <th>推薦信</th>
              <th>狀態</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="application in filteredApplications" :key="application.id">
              <td>
                <strong>{{ application.scholarship?.title }}</strong>
                <span>{{ application.scholarship?.category }}</span>
              </td>
              <td>
                <strong>{{ application.student?.name }}</strong>
                <span>{{ application.profile?.department }}</span>
              </td>
              <td>{{ formatDate(application.submittedAt) }}</td>
              <td>
                <StatusBadge
                  v-if="application.recommendations.length"
                  :value="application.recommendations[0].status"
                />
                <span v-else class="muted-text">不需要</span>
              </td>
              <td><StatusBadge :value="application.status" /></td>
              <td>
                <button class="secondary-button" type="button" @click="openDetail(application)">
                  審查
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </BaseCard>
  </div>

  <BaseModal
    :show="!!selected"
    :title="selected ? selected.scholarship?.title : ''"
    width="960px"
    @close="selected = null"
  >
    <div v-if="selected" class="review-detail-modal">
      <div class="review-summary">
        <div class="review-summary__main">
          <span class="review-summary__label">申請摘要</span>
          <h3>{{ selected.student?.name }}</h3>
          <p>{{ selected.profile?.department || '未填寫科系' }}</p>
        </div>
        <dl class="review-summary__facts">
          <div>
            <dt>目前狀態</dt>
            <dd><StatusBadge :value="selected.status" /></dd>
          </div>
          <div>
            <dt>GPA / 學分</dt>
            <dd>{{ selected.form.academics.gpa }} / {{ selected.form.academics.credits }}</dd>
          </div>
          <div>
            <dt>送出時間</dt>
            <dd>{{ formatDate(selected.submittedAt) }}</dd>
          </div>
        </dl>
      </div>

      <div class="review-detail-tabs" role="tablist" aria-label="審查詳情分頁">
        <button
          v-for="tab in detailTabs"
          :key="tab.value"
          :class="['review-detail-tab', { 'review-detail-tab--active': activeDetailTab === tab.value }]"
          type="button"
          role="tab"
          :aria-selected="activeDetailTab === tab.value"
          @click="activeDetailTab = tab.value"
        >
          <Icon :name="tab.icon" />
          <span>{{ tab.label }}</span>
        </button>
      </div>

      <div class="review-tab-stage">
        <section v-if="activeDetailTab === 'decision'" class="review-panel review-panel--decision">
          <div class="review-section-heading">
            <div>
              <span class="review-section-heading__kicker">審查決策</span>
              <h3>審查操作</h3>
            </div>
            <button class="ghost-button" type="button" @click="activeDetailTab = 'application'">
              查看資料
            </button>
          </div>
          <p v-if="error" class="form-error">{{ error }}</p>
          <div class="form-grid review-decision-grid">
            <label>
              <span>審查結果</span>
              <select v-model="decision.result">
                <option value="APPROVED">通過</option>
                <option value="REJECTED">未通過</option>
              </select>
            </label>
            <label>
              <span>補交期限 (僅要求補件時必填)</span>
              <input v-model="decision.deadline" type="datetime-local" />
            </label>
            <label class="form-grid__wide">
              <span>審查意見 / 補件說明</span>
              <textarea v-model="decision.comment" rows="6" />
            </label>
          </div>
          <div class="review-decision-actions">
            <button
              class="secondary-button"
              type="button"
              :disabled="sendingSupplement || savingDecision"
              @click="supplement"
            >
              <Icon name="alert" />
              {{ sendingSupplement ? '送出中...' : '要求補件' }}
            </button>
            <button
              class="primary-button"
              type="button"
              :disabled="savingDecision || sendingSupplement"
              @click="saveDecision"
            >
              <Icon name="check" />
              {{ savingDecision ? '送出中...' : '送出審查結果' }}
            </button>
          </div>
        </section>

        <section v-else-if="activeDetailTab === 'application'" class="review-panel review-panel--application">
          <div class="review-section-heading">
            <div>
              <span class="review-section-heading__kicker">學生資料</span>
              <h3>申請資料</h3>
            </div>
            <button class="ghost-button" type="button" @click="activeDetailTab = 'documents'">
              查看文件
            </button>
          </div>

          <dl class="review-field-grid">
            <div>
              <dt>學生</dt>
              <dd>{{ selected.student?.name }}</dd>
            </div>
            <div>
              <dt>科系</dt>
              <dd>{{ selected.profile?.department || '-' }}</dd>
            </div>
            <div>
              <dt>家庭狀況</dt>
              <dd>{{ selected.form.finance.familyStatus }}</dd>
            </div>
            <div>
              <dt>推薦信</dt>
              <dd>
                <span v-if="selected.recommendations.length">
                  {{ selected.recommendations.length }} 份
                </span>
                <span v-else>不需要</span>
              </dd>
            </div>
            <div class="review-field-grid__wide">
              <dt>申請聲明</dt>
              <dd>{{ selected.form.statement }}</dd>
            </div>
          </dl>
        </section>

        <section v-else-if="activeDetailTab === 'documents'" class="review-tab-grid">
          <div class="review-panel">
            <div class="review-subsection__header">
              <h3>上傳文件</h3>
              <span>{{ selected.documents?.length || 0 }} 件</span>
            </div>
            <ul v-if="selected.documents && selected.documents.length" class="document-list">
              <li v-for="(doc, index) in selected.documents" :key="index">
                <div class="document-header">
                  <button class="document-open-button" type="button" @click="previewDocument(doc.title)">
                    <Icon name="archive" />
                    <span>{{ doc.title }}</span>
                  </button>
                  <span v-if="doc.documentType" class="document-type">{{ doc.documentType }}</span>
                </div>
                <p v-if="doc.contentText" class="document-content">{{ doc.contentText }}</p>
                <p v-else class="document-content document-content--empty">未提供文字摘要。</p>
              </li>
            </ul>
            <p v-else class="muted-text">無上傳文件。</p>
          </div>

          <div class="review-panel">
            <div class="review-subsection__header">
              <h3>推薦信</h3>
              <span>{{ selected.recommendations.length ? '已建立邀請' : '無需求' }}</span>
            </div>
            <div v-if="selected.recommendations.length" class="recommendation-list">
              <article
                v-for="request in selected.recommendations"
                :key="request.id"
                class="mini-panel"
              >
                <div>
                  <strong>{{ request.recommenderName }}</strong>
                  <p>{{ request.recommenderTitle }} · {{ request.relationship }}</p>
                  <p v-if="request.contentAvailable && request.content">{{ request.content }}</p>
                  <p v-else class="muted-text">推薦信尚未提交，暫不可檢視內容。</p>
                </div>
                <StatusBadge :value="request.status" />
              </article>
            </div>
            <p v-else class="muted-text">此申請不需要推薦信。</p>
          </div>
        </section>

        <section v-else class="review-tab-grid">
          <div class="review-panel">
            <div class="review-section-heading">
              <div>
                <span class="review-section-heading__kicker">歷程紀錄</span>
                <h3>審查歷程</h3>
              </div>
            </div>
            <AuditTimeline :logs="selected.auditLogs" />
          </div>

          <div class="review-panel">
            <div class="review-section-heading">
              <div>
                <span class="review-section-heading__kicker">留言溝通</span>
                <h3>留言互動</h3>
              </div>
            </div>
            <MessageBoard :application-id="selected.application_id" />
          </div>
        </section>
      </div>
    </div>
  </BaseModal>
</template>

<style scoped>
.review-detail-modal {
  display: grid;
  gap: 18px;
}

.review-summary {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(430px, 0.82fr);
  gap: 18px;
  align-items: stretch;
  padding: 18px;
  border: 1px solid rgba(211, 195, 165, 0.76);
  border-radius: 14px;
  background: linear-gradient(135deg, var(--primary-tint), #fffefa 62%);
}

.review-summary__main {
  min-width: 0;
}

.review-summary__label {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  color: var(--muted);
  font-size: 12px;
  font-weight: 750;
}

.review-summary__label::before {
  content: "";
  width: 6px;
  height: 6px;
  flex: 0 0 auto;
  border-radius: 1px;
  background: var(--seal);
}

.review-summary__main h3 {
  margin: 8px 0 6px;
  font-size: 22px;
}

.review-summary__main p {
  margin: 0;
  color: var(--muted);
}

.review-summary__facts {
  display: grid;
  grid-template-columns: repeat(3, minmax(120px, 1fr));
  gap: 10px;
  margin: 0;
}

.review-summary__facts div,
.review-field-grid div {
  min-width: 0;
  padding: 12px;
  border: 1px solid rgba(211, 195, 165, 0.7);
  border-radius: 12px;
  background: rgba(255, 253, 248, 0.78);
}

.review-summary__facts dt,
.review-field-grid dt {
  margin-bottom: 6px;
  color: var(--muted);
  font-size: 12px;
  font-weight: 700;
}

.review-summary__facts dd,
.review-field-grid dd {
  min-width: 0;
  margin: 0;
  color: var(--text);
  font-weight: 650;
  overflow-wrap: anywhere;
}

.review-workspace--detail {
  grid-template-columns: minmax(0, 1fr) minmax(360px, 440px);
  gap: 18px;
}

.review-detail-tabs {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 8px;
  padding: 6px;
  border: 1px solid rgba(211, 195, 165, 0.72);
  border-radius: 14px;
  background: rgba(244, 239, 229, 0.64);
}

.review-detail-tab {
  display: inline-flex;
  min-width: 0;
  min-height: 42px;
  align-items: center;
  justify-content: center;
  gap: 7px;
  padding: 9px 10px;
  border: 1px solid transparent;
  border-radius: 10px;
  background: transparent;
  color: var(--muted);
  font: inherit;
  font-weight: 750;
  cursor: pointer;
}

.review-detail-tab .icon {
  width: 16px;
  height: 16px;
  flex: 0 0 auto;
}

.review-detail-tab span {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.review-detail-tab--active {
  border-color: rgba(47, 107, 79, 0.28);
  background: #fffefa;
  color: var(--primary-strong);
  box-shadow: var(--shadow-xs);
}

.review-tab-stage {
  display: grid;
  min-width: 0;
}

.review-tab-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(320px, 0.82fr);
  gap: 16px;
  min-width: 0;
}

.review-panel {
  display: grid;
  gap: 16px;
  min-width: 0;
  padding: 18px;
  border: 1px solid rgba(211, 195, 165, 0.72);
  border-radius: 14px;
  background: rgba(255, 253, 248, 0.9);
}

.review-side-column {
  display: grid;
  align-content: start;
  gap: 18px;
  min-width: 0;
}

.review-section-heading {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.review-section-heading h3 {
  margin: 2px 0 0;
  font-size: 18px;
}

.review-section-heading__kicker {
  color: var(--muted);
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0;
  text-transform: uppercase;
}

.review-field-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
  margin: 0;
}

.review-field-grid__wide {
  grid-column: 1 / -1;
}

.review-field-grid__wide dd {
  line-height: 1.7;
  font-weight: 500;
}

.review-decision-grid {
  grid-template-columns: minmax(0, 0.8fr) minmax(0, 1fr);
}

.review-subsection {
  display: grid;
  gap: 10px;
  min-width: 0;
}

.review-subsection__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.review-subsection__header h3,
.review-subsection__header h4 {
  margin: 0;
  font-size: 15px;
}

.review-subsection__header span {
  color: var(--muted);
  font-size: 12px;
  font-weight: 700;
}

.document-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: grid;
  gap: 10px;
}

.document-list li {
  display: grid;
  gap: 8px;
  min-width: 0;
  padding: 12px;
  border: 1px solid rgba(211, 195, 165, 0.72);
  border-radius: 12px;
  background: #fffefa;
}

.document-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 10px;
  min-width: 0;
}

.document-open-button {
  display: inline-flex;
  min-width: 0;
  align-items: flex-start;
  gap: 8px;
  padding: 0;
  border: 0;
  background: transparent;
  color: var(--primary);
  font: inherit;
  font-weight: 750;
  text-align: left;
  cursor: pointer;
}

.document-open-button .icon {
  flex: 0 0 auto;
  width: 17px;
  height: 17px;
  margin-top: 2px;
}

.document-open-button span {
  min-width: 0;
  overflow-wrap: anywhere;
}

.document-type {
  flex: 0 0 auto;
  padding: 3px 8px;
  border-radius: var(--radius-pill);
  background: var(--primary-tint);
  color: var(--primary-strong);
  font-size: 12px;
  font-weight: 700;
}

.document-content {
  margin: 0;
  white-space: pre-wrap;
  color: var(--text-2, inherit);
  font-size: 0.93rem;
  line-height: 1.65;
  overflow-wrap: anywhere;
}

.document-content--empty {
  color: var(--muted);
}

.review-decision-actions {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1.2fr);
  gap: 10px;
}

.review-decision-actions .primary-button,
.review-decision-actions .secondary-button {
  width: 100%;
}

@media (max-width: 1080px) {
  .review-summary,
  .review-workspace--detail,
  .review-tab-grid,
  .review-summary__facts {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 760px) {
  .review-panel,
  .review-summary {
    padding: 14px;
  }

  .review-field-grid,
  .review-decision-grid,
  .review-decision-actions {
    grid-template-columns: 1fr;
  }

  .review-detail-tabs {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .document-header {
    flex-direction: column;
  }
}
</style>
