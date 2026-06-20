<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import BaseCard from '@/components/common/BaseCard.vue'
import BaseModal from '@/components/common/BaseModal.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import LoadingSkeleton from '@/components/common/LoadingSkeleton.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import {
  getRecommendationStudentProfile,
  getTeacherRecommendationDashboard,
  listTeacherRecommendations,
  saveRecommendationDraft,
  submitRecommendation,
} from '@/api/trs'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'

const auth = useAuthStore()
const toast = useToastStore()
const loading = ref(true)
const requests = ref([])
const selectedId = ref(null)
const content = ref('')
const error = ref('')
const loadError = ref('')
const saving = ref(false)
const dashboard = ref({
  totalCount: 0,
  pendingCount: 0,
  draftCount: 0,
  submittedCount: 0,
  dueSoonCount: 0,
  overdueCount: 0,
})
const studentProfile = ref(null)
const studentProfileLoading = ref(false)
const studentProfileError = ref('')
const studentProfileOpen = ref(false)
const filters = reactive({
  keyword: '',
  status: '',
  sortBy: 'deadline',
  order: 'asc',
})

const selected = computed(() => requests.value.find((item) => item.id === selectedId.value))
const currentUserId = computed(() => auth.user?.user_id ?? auth.user?.id ?? null)
const isSubmitted = computed(() => selected.value?.status === 'SUBMITTED')
const dashboardStats = computed(() => [
  { label: '全部案件', value: dashboard.value.totalCount, description: '目前負責的推薦案件總數' },
  { label: '待處理', value: dashboard.value.pendingCount, description: '尚未開始撰寫推薦信' },
  { label: '草稿中', value: dashboard.value.draftCount, description: '已儲存但尚未提交' },
  { label: '已提交', value: dashboard.value.submittedCount, description: '已正式送出推薦信' },
  { label: '即將截止', value: dashboard.value.dueSoonCount, description: '48 小時內到期' },
  { label: '已逾期', value: dashboard.value.overdueCount, description: '超過截止仍未提交' },
])

function formatDate(value) {
  if (!value) return '-'
  return new Intl.DateTimeFormat('zh-TW', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  }).format(new Date(value))
}

async function reload() {
  loadError.value = ''
  const previousId = selectedId.value
  requests.value = await listTeacherRecommendations({
    keyword: filters.keyword,
    status: filters.status,
    sortBy: filters.sortBy,
    order: filters.order,
  }, currentUserId.value)
  if (!requests.value.length) {
    selectedId.value = null
    content.value = ''
    return
  }

  const active =
    requests.value.find((item) => item.id === previousId) ??
    requests.value[0]
  selectedId.value = active.id
  content.value = active.content || ''
}

async function reloadDashboard() {
  dashboard.value = await getTeacherRecommendationDashboard(currentUserId.value)
}

function resolveErrorMessage(err, fallback) {
  return err?.response?.data?.detail || err?.message || fallback
}

async function safeReload() {
  try {
    await Promise.all([reload(), reloadDashboard()])
  } catch (err) {
    const message = resolveErrorMessage(err, '載入推薦案件失敗，請稍後再試。')
    loadError.value = message
    toast.error(message)
  }
}

async function search() {
  loading.value = true
  try {
    await safeReload()
  } finally {
    loading.value = false
  }
}

async function resetFilters() {
  filters.keyword = ''
  filters.status = ''
  filters.sortBy = 'deadline'
  filters.order = 'asc'
  await search()
}

function toggleSortOrder() {
  filters.order = filters.order === 'asc' ? 'desc' : 'asc'
}

function choose(request) {
  selectedId.value = request.id
  content.value = request.content || ''
  error.value = ''
}

async function openStudentProfile() {
  if (!selected.value) {
    return
  }

  studentProfileOpen.value = true
  studentProfileLoading.value = true
  studentProfileError.value = ''
  studentProfile.value = null

  try {
    studentProfile.value = await getRecommendationStudentProfile(selected.value.recId, currentUserId.value)
  } catch (err) {
    if (err?.response?.status === 403) {
      studentProfileError.value = '你沒有權限查看此學生資料。'
    } else if (err?.response?.status === 404) {
      studentProfileError.value = '找不到推薦案件或學生資料。'
    } else {
      studentProfileError.value = resolveErrorMessage(err, '學生資料載入失敗，請稍後再試。')
    }
  } finally {
    studentProfileLoading.value = false
  }
}

function closeStudentProfile() {
  studentProfileOpen.value = false
}

async function saveDraft() {
  if (!selected.value || isSubmitted.value) {
    return
  }

  error.value = ''
  if (!content.value.trim()) {
    error.value = '請先輸入推薦內容。'
    return
  }
  saving.value = true
  try {
    const updated = await saveRecommendationDraft(selected.value.recId, content.value, currentUserId.value)
    content.value = updated.content || content.value
    toast.success('草稿已儲存')
    await safeReload()
  } catch (err) {
    const message = resolveErrorMessage(err, '儲存草稿失敗，請稍後再試。')
    error.value = message
    toast.error(message)
  } finally {
    saving.value = false
  }
}

async function submit() {
  if (!selected.value || isSubmitted.value) {
    return
  }

  error.value = ''
  if (!content.value.trim()) {
    error.value = '請先輸入推薦內容。'
    return
  }
  if (!window.confirm('確認要正式提交推薦信嗎？提交後將無法再修改。')) {
    return
  }

  saving.value = true
  try {
    const updated = await submitRecommendation(selected.value.recId, content.value, currentUserId.value)
    content.value = updated.content || content.value
    toast.success('推薦信已送出')
    await safeReload()
  } catch (err) {
    const message = resolveErrorMessage(err, '送出推薦信失敗，請稍後再試。')
    error.value = message
    toast.error(message)
  } finally {
    saving.value = false
  }
}

onMounted(async () => {
  try {
    await safeReload()
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <LoadingSkeleton v-if="loading" :rows="4" />

  <div v-else class="page-grid">
    <section class="stat-grid">
      <BaseCard v-for="stat in dashboardStats" :key="stat.label" class="stat-card">
        <span>{{ stat.label }}</span>
        <strong>{{ stat.value }}</strong>
        <small class="muted-text">{{ stat.description }}</small>
      </BaseCard>
    </section>

    <BaseCard title="搜尋與篩選" eyebrow="Filters">
      <div class="form-grid">
        <label class="form-grid__wide">
          <span>搜尋</span>
          <input
            v-model="filters.keyword"
            type="search"
            placeholder="搜尋學生姓名、學號或獎學金"
          />
        </label>
        <label>
          <span>狀態</span>
          <select v-model="filters.status">
            <option value="">全部</option>
            <option value="REQUESTED">待處理</option>
            <option value="PENDING">待處理</option>
            <option value="DRAFT">草稿中</option>
            <option value="SUBMITTED">已提交</option>
          </select>
        </label>
        <label>
          <span>排序欄位</span>
          <select v-model="filters.sortBy">
            <option value="deadline">截止日期</option>
            <option value="submitted_at">提交時間</option>
            <option value="student_name">學生姓名</option>
            <option value="scholarship_name">獎學金名稱</option>
          </select>
        </label>
        <label>
          <span>排序方向</span>
          <div class="sort-indicator" role="group" aria-label="排序方向">
            <button
              type="button"
              class="sort-indicator__button"
              :class="{
                'sort-indicator__button--asc': filters.order === 'asc',
                'sort-indicator__button--desc': filters.order === 'desc',
              }"
              @click="toggleSortOrder"
            >
              <span class="sort-indicator__arrow" aria-hidden="true">{{ filters.order === 'asc' ? '▲' : '▼' }}</span>
              <span>{{ filters.order === 'asc' ? '遞增' : '遞減' }}</span>
            </button>
          </div>
        </label>
      </div>
      <div class="form-actions">
        <button class="primary-button" type="button" @click="search">搜尋</button>
        <button class="secondary-button" type="button" @click="resetFilters">清除條件</button>
      </div>
    </BaseCard>

    <EmptyState
      v-if="!requests.length"
      :title="loadError ? '載入失敗' : '目前沒有符合條件的推薦案件'"
      :description="loadError || '請調整搜尋、篩選條件，或等待學生送出推薦邀請。'"
      icon="recommend"
    />

    <div v-else class="split-layout">
    <BaseCard title="推薦邀請" eyebrow="Requests">
      <div class="request-list">
        <button
          v-for="request in requests"
          :key="request.id"
          type="button"
          class="request-item"
          :class="{ 'request-item--active': request.id === selectedId }"
          @click="choose(request)"
        >
          <span>{{ request.studentName || '-' }}</span>
          <small>{{ request.studentAccount || '—' }}</small>
          <strong>{{ request.scholarshipName || '-' }}</strong>
          <small>截止日 {{ formatDate(request.deadline) }}</small>
          <small>{{ request.content?.trim() ? '已有草稿' : '尚未撰寫' }}</small>
          <StatusBadge :value="request.status" />
        </button>
      </div>
    </BaseCard>

    <BaseCard v-if="selected" title="填寫推薦內容" eyebrow="Recommendation Letter">
      <template #actions>
        <button class="secondary-button" type="button" @click="openStudentProfile">
          查看學生資料
        </button>
      </template>

      <dl class="review-list">
        <div>
          <dt>學生</dt>
          <dd>{{ selected.studentName || '-' }}</dd>
        </div>
        <div>
          <dt>獎學金</dt>
          <dd>{{ selected.scholarshipName || '-' }}</dd>
        </div>
        <div>
          <dt>截止日期</dt>
          <dd>{{ formatDate(selected.deadline) }}</dd>
        </div>
        <div>
          <dt>推薦狀態</dt>
          <dd><StatusBadge :value="selected.status" /></dd>
        </div>
      </dl>

      <p v-if="error" class="form-error">{{ error }}</p>
      <label class="stacked-field">
        <span>推薦內容</span>
        <textarea
          v-model="content"
          :readonly="isSubmitted"
          :disabled="isSubmitted || saving"
          rows="10"
          placeholder="請描述學生的學習表現、專業能力、品格與推薦理由"
        />
      </label>

      <div class="form-actions">
        <button
          v-if="!isSubmitted"
          class="secondary-button"
          type="button"
          :disabled="saving"
          @click="saveDraft"
        >
          {{ saving ? '處理中...' : '儲存草稿' }}
        </button>
        <button
          class="primary-button"
          type="button"
          :disabled="isSubmitted || saving"
          @click="submit"
        >
          {{ isSubmitted ? '已送出' : saving ? '處理中...' : '提交推薦信' }}
        </button>
      </div>
    </BaseCard>
    </div>
  </div>

  <BaseModal
    :show="studentProfileOpen"
    title="學生申請資料"
    width="920px"
    @close="closeStudentProfile"
  >
    <LoadingSkeleton v-if="studentProfileLoading" :rows="5" />

    <EmptyState
      v-else-if="studentProfileError"
      title="無法載入學生資料"
      :description="studentProfileError"
      icon="recommend"
    />

    <div v-else-if="studentProfile" class="detail-grid">
      <section>
        <h3>學生基本資料</h3>
        <dl class="review-list">
          <div>
            <dt>姓名</dt>
            <dd>{{ studentProfile.student.name || '—' }}</dd>
          </div>
          <div>
            <dt>帳號 / 學號</dt>
            <dd>{{ studentProfile.student.account || '—' }}</dd>
          </div>
          <div>
            <dt>Email</dt>
            <dd>{{ studentProfile.student.email || '—' }}</dd>
          </div>
        </dl>

        <h3>個人檔案</h3>
        <dl v-if="studentProfile.profile" class="review-list">
          <div>
            <dt>年級</dt>
            <dd>{{ studentProfile.profile.grade || '—' }}</dd>
          </div>
          <div>
            <dt>身分別</dt>
            <dd>{{ studentProfile.profile.identityType || '—' }}</dd>
          </div>
          <div>
            <dt>聯絡 Email</dt>
            <dd>{{ studentProfile.profile.contactEmail || '—' }}</dd>
          </div>
          <div>
            <dt>聯絡電話</dt>
            <dd>{{ studentProfile.profile.contactPhone || '—' }}</dd>
          </div>
          <div>
            <dt>地址</dt>
            <dd>{{ studentProfile.profile.address || '—' }}</dd>
          </div>
          <div>
            <dt>緊急聯絡人</dt>
            <dd>{{ studentProfile.profile.emergencyContactName || '—' }}</dd>
          </div>
          <div>
            <dt>緊急聯絡電話</dt>
            <dd>{{ studentProfile.profile.emergencyContactPhone || '—' }}</dd>
          </div>
        </dl>
        <p v-else class="muted-text">尚無學生個人資料。</p>
      </section>

      <section>
        <h3>申請案資料</h3>
        <dl class="review-list">
          <div>
            <dt>申請案編號</dt>
            <dd>{{ studentProfile.application.applicationId || '—' }}</dd>
          </div>
          <div>
            <dt>申請狀態</dt>
            <dd>
              <StatusBadge v-if="studentProfile.application.status" :value="studentProfile.application.status" />
              <span v-else>—</span>
            </dd>
          </div>
          <div>
            <dt>送出時間</dt>
            <dd>{{ formatDate(studentProfile.application.submittedAt) }}</dd>
          </div>
        </dl>

        <h3>獎學金資料</h3>
        <dl class="review-list">
          <div>
            <dt>獎學金名稱</dt>
            <dd>{{ studentProfile.scholarship.name || '—' }}</dd>
          </div>
          <div>
            <dt>截止日期</dt>
            <dd>{{ formatDate(studentProfile.scholarship.deadline) }}</dd>
          </div>
        </dl>

        <h3>申請文件</h3>
        <div v-if="studentProfile.documents.length" class="recommendation-list">
          <article
            v-for="document in studentProfile.documents"
            :key="document.documentId"
            class="mini-panel"
          >
            <strong>{{ document.title || '未命名文件' }}</strong>
            <p class="muted-text">{{ document.documentType || 'OTHER' }}</p>
            <p style="white-space: pre-wrap">{{ document.contentText || '—' }}</p>
          </article>
        </div>
        <p v-else class="muted-text">尚無申請文件。</p>
      </section>
    </div>
  </BaseModal>
</template>

<style scoped>
.sort-indicator {
  display: block;
}

.sort-indicator__button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.375rem;
  width: 100%;
  min-height: 2.5rem;
  border: 1px solid #8ea899;
  border-radius: 0.75rem;
  background: #eef4ed;
  color: #1f2a21;
  font-weight: 700;
  cursor: pointer;
  transition: transform 140ms ease, box-shadow 140ms ease, border-color 140ms ease, background 140ms ease, color 140ms ease;
}

.sort-indicator__button:hover {
  transform: translateY(-1px);
  border-color: #5f7f6e;
  background: #e5efe4;
}

.sort-indicator__button--asc,
.sort-indicator__button--desc {
  color: white;
  border-color: #2f5e45;
  background: linear-gradient(135deg, #3a7154, #2f5e45);
  box-shadow: 0 8px 20px rgba(47, 94, 69, 0.24);
}

.sort-indicator__arrow {
  font-size: 0.9rem;
  line-height: 1;
}
</style>
