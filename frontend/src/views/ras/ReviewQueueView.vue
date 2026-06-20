<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import AuditTimeline from '@/components/common/AuditTimeline.vue'
import BaseCard from '@/components/common/BaseCard.vue'
import BaseModal from '@/components/common/BaseModal.vue'
import EmptyState from '@/components/common/EmptyState.vue'
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
const decision = reactive({
  result: 'APPROVED',
  comment: '',
  deadline: ''
})

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
  const updated = await submitReviewDecision(auth.user.id, selected.value.id, { ...decision })
  toast.success('審查結果已送出並留下紀錄')
  await reload()
  selected.value = updated
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
  const updated = await requestSupplement(auth.user.id, selected.value.id, decision.comment, decision.deadline)
  toast.success('補件通知已送出並留下紀錄')
  await reload()
  selected.value = updated
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
            <option value="NEEDS_SUPPLEMENT">需補件</option>
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
    width="1040px"
    @close="selected = null"
  >
    <div v-if="selected" class="review-workspace">
      <section>
        <h3>申請資料</h3>
        <dl class="review-list">
          <div>
            <dt>學生</dt>
            <dd>{{ selected.student?.name }} · {{ selected.profile?.department }}</dd>
          </div>
          <div>
            <dt>狀態</dt>
            <dd><StatusBadge :value="selected.status" /></dd>
          </div>
          <div>
            <dt>GPA / 學分</dt>
            <dd>{{ selected.form.academics.gpa }} / {{ selected.form.academics.credits }}</dd>
          </div>
          <div>
            <dt>家庭狀況</dt>
            <dd>{{ selected.form.finance.familyStatus }}</dd>
          </div>
          <div>
            <dt>文件</dt>
            <dd v-if="selected.documents && selected.documents.length">
              <ul class="document-list">
                <li v-for="doc in selected.documents" :key="doc">
                  <a href="#" @click.prevent="previewDocument(doc)">
                    <Icon name="attachment" /> {{ doc }}
                  </a>
                </li>
              </ul>
            </dd>
            <dd v-else class="muted-text">無上傳文件</dd>
          </div>
          <div>
            <dt>申請聲明</dt>
            <dd>{{ selected.form.statement }}</dd>
          </div>
        </dl>

        <h3>推薦信</h3>
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
      </section>

      <section>
        <h3>審查操作</h3>
        <p v-if="error" class="form-error">{{ error }}</p>
        <div class="form-grid form-grid--single">
          <label>
            <span>審查結果</span>
            <select v-model="decision.result">
              <option value="APPROVED">通過</option>
              <option value="REJECTED">未通過</option>
            </select>
          </label>
          <label>
            <span>審查意見 / 補件說明</span>
            <textarea v-model="decision.comment" rows="5" />
          </label>
          <label>
            <span>補交期限 (僅要求補件時必填)</span>
            <input v-model="decision.deadline" type="datetime-local" />
          </label>
        </div>
        <div class="form-actions form-actions--left">
          <button class="secondary-button" type="button" @click="supplement">要求補件</button>
          <button class="primary-button" type="button" @click="saveDecision">送出審查結果</button>
        </div>

        <h3>Audit Timeline</h3>
        <AuditTimeline :logs="selected.auditLogs" />
      </section>
    </div>
  </BaseModal>
</template>

<style scoped>
.document-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}
.document-list a {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  color: var(--primary);
  text-decoration: none;
  padding: 0.5rem;
  background: var(--surface-2);
  border-radius: var(--radius-sm);
  transition: background 0.2s;
}
.document-list a:hover {
  background: var(--surface-3);
}
</style>
