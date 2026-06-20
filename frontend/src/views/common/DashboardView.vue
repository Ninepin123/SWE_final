<script setup>
import { computed, onMounted, ref } from 'vue'
import BaseCard from '@/components/common/BaseCard.vue'
import LoadingSkeleton from '@/components/common/LoadingSkeleton.vue'
import { useAuthStore } from '@/stores/auth'
import { listUsers } from '@/api/aas'
import { getUnreadNotificationCount } from '@/api/ncs'
import { getAwardList, listReviewApplications } from '@/api/ras'
import { listAvailableScholarships, listMyApplications } from '@/api/sas'
import { listScholarships } from '@/api/sms'
import { getTeacherRecommendationDashboard } from '@/api/trs'

const auth = useAuthStore()
const loading = ref(true)
const summary = ref({})
const loadError = ref('')

const stats = computed(() => {
  if (auth.role === 'STUDENT') {
    return [
      { label: '我的申請', value: summary.value.applications ?? 0, tone: 'info', icon: '📄', hint: '已建立的申請紀錄' },
      { label: '審查中', value: summary.value.underReview ?? 0, tone: 'blue', icon: '🔎', hint: '正在等待審核' },
      { label: '需補件', value: summary.value.needsSupplement ?? 0, tone: 'warning', icon: '⚠️', hint: '請優先處理' },
      {
        label: '可申請',
        value: summary.value.availableScholarships ?? 0,
        tone: 'success',
        icon: '🎓',
        hint:
          (summary.value.availableDrafts ?? 0) > 0
            ? `符合資格可申請（含 ${summary.value.availableDrafts} 件草稿待完成）`
            : '符合資格可申請',
      },
      { label: '未讀通知', value: summary.value.unread ?? 0, tone: 'info', icon: '🔔', hint: '最新訊息' },
    ]
  }

  if (auth.role === 'REVIEWER') {
    return [
      { label: '待處理', value: summary.value.pending ?? 0, tone: 'warning', icon: '📥', hint: '等待審查案件' },
      { label: '已通過', value: summary.value.approved ?? 0, tone: 'success', icon: '✅', hint: '已核定案件' },
      { label: '未通過', value: summary.value.rejected ?? 0, tone: 'danger', icon: '⛔', hint: '已退回案件' },
      { label: '未讀通知', value: summary.value.unread ?? 0, tone: 'info', icon: '🔔', hint: '最新訊息' },
    ]
  }

  if (auth.role === 'ADMIN') {
    return [
      { label: '帳號數', value: summary.value.users ?? 0, tone: 'info', icon: '👥', hint: '平台使用者' },
      { label: '獎學金', value: summary.value.scholarships ?? 0, tone: 'success', icon: '🏛️', hint: '總項目數' },
      { label: '開放中', value: summary.value.openScholarships ?? 0, tone: 'blue', icon: '📣', hint: '目前開放申請' },
    ]
  }

  if (auth.role === 'SPONSOR') {
    return [
      { label: '獎學金', value: summary.value.scholarships ?? 0, tone: 'success', icon: '🏛️', hint: '所屬單位項目' },
      { label: '開放中', value: summary.value.openScholarships ?? 0, tone: 'blue', icon: '📣', hint: '目前公開中' },
      { label: '未讀通知', value: summary.value.unread ?? 0, tone: 'warning', icon: '🔔', hint: '待確認訊息' },
    ]
  }

  return [
    { label: '待填推薦信', value: summary.value.pendingRecommendations ?? 0, tone: 'warning', icon: '✍️', hint: '需要處理' },
    { label: '已送出推薦', value: summary.value.submittedRecommendations ?? 0, tone: 'success', icon: '✅', hint: '完成推薦' },
    { label: '未讀通知', value: summary.value.unread ?? 0, tone: 'info', icon: '🔔', hint: '最新訊息' },
  ]
})

const guidance = computed(() => {
  const text = {
    STUDENT: '目前有申請需要補件時，請優先確認期限；也可以直接瀏覽仍在開放中的獎學金。',
    REVIEWER: '審查工作台會彙整待處理案件、推薦信狀態與完整審核紀錄。',
    ADMIN: '管理員可維護帳號、獎學金資料與系統稽核紀錄，確保平台資料正確。',
    TEACHER: '教師可在推薦信邀請中查看學生請求，並追蹤已送出的推薦紀錄。',
    SPONSOR: '獎助單位人員可管理所屬單位的獎學金資料與開放狀態。',
  }

  return text[auth.role] ?? '請依照角色使用系統功能。'
})

const tasks = computed(() => {
  if (auth.role === 'STUDENT') {
    return [
      { title: '確認是否有補件要求', text: `${summary.value.needsSupplement ?? 0} 件申請可能需要補件`, tone: 'warning' },
      {
        title: '查看可申請獎學金',
        text:
          (summary.value.availableDrafts ?? 0) > 0
            ? `${summary.value.availableScholarships ?? 0} 項可申請，其中 ${summary.value.availableDrafts} 件草稿待完成`
            : `${summary.value.availableScholarships ?? 0} 項目前可申請`,
        tone: 'success',
      },
      { title: '追蹤申請進度', text: `${summary.value.underReview ?? 0} 件申請審查中`, tone: 'info' },
    ]
  }
  if (auth.role === 'ADMIN') {
    return [
      { title: '處理待辦事項', text: '依照側邊欄進入主要工作區', tone: 'warning' },
      { title: '維護公告與資料', text: '在公告管理發布與處理公告，並檢查資料正確性', tone: 'success' },
    ]
  }

  return [
    { title: '處理待辦事項', text: '依照側邊欄進入主要工作區', tone: 'warning' },
    { title: '確認通知中心', text: `${summary.value.unread ?? 0} 則未讀通知`, tone: 'info' },
    { title: '維護資料完整性', text: '定期檢查資料與狀態是否正確', tone: 'success' },
  ]
})

// 截止日尚未過（沒設定截止日就視為仍可申請）。
function deadlineActive(item) {
  if (!item.deadline) return true
  return new Date(item.deadline) >= new Date()
}

// 「可申請」＝符合資格的全新項目 ＋ 已開草稿但還沒填完、且獎學金仍開放的項目。
// 與「可申請獎學金」列表頁同源同判定，避免兩個畫面數字對不上。
function countAvailableWithDrafts(scholarships, draftScholarshipIds) {
  let fresh = 0
  let drafts = 0
  for (const item of scholarships) {
    if (draftScholarshipIds.has(String(item.id))) {
      // 草稿尚未完成：只要獎學金仍開放、未截止就算「可申請」（點進去可繼續填）。
      if (item.status === 'OPEN' && deadlineActive(item)) drafts += 1
    } else if (item.canApply && item.status === 'OPEN' && item.seatsLeft > 0) {
      fresh += 1
    }
  }
  return { available: fresh + drafts, drafts }
}

async function loadUnreadCount() {
  return getUnreadNotificationCount()
}

async function loadStudentSummary() {
  const studentId = auth.user?.user_id ?? auth.user?.id
  const [scholarships, applications, unread] = await Promise.all([
    listAvailableScholarships(studentId),
    listMyApplications(studentId),
    loadUnreadCount(),
  ])
  const draftScholarshipIds = new Set(
    applications
      .filter((application) => application.status === 'DRAFT')
      .map((application) => String(application.scholarship_id ?? application.scholarshipId)),
  )
  const { available, drafts } = countAvailableWithDrafts(scholarships, draftScholarshipIds)

  return {
    applications: applications.length,
    underReview: applications.filter((application) => application.status === 'UNDER_REVIEW').length,
    needsSupplement: applications.filter((application) =>
      ['NEED_SUPPLEMENT', 'NEEDS_SUPPLEMENT'].includes(application.status),
    ).length,
    availableScholarships: available,
    availableDrafts: drafts,
    unread,
  }
}

async function loadReviewerSummary() {
  const [applications, awards, unread] = await Promise.all([
    listReviewApplications(),
    getAwardList(),
    loadUnreadCount(),
  ])

  return {
    pending: applications.filter((application) =>
      ['SUBMITTED', 'UNDER_REVIEW', 'NEED_SUPPLEMENT', 'NEEDS_SUPPLEMENT'].includes(application.status),
    ).length,
    approved: awards.length,
    rejected: applications.filter((application) => application.status === 'REJECTED').length,
    unread,
  }
}

async function loadAdminSummary() {
  const [users, scholarships] = await Promise.all([
    listUsers(),
    listScholarships(),
  ])

  return {
    users: users.length,
    scholarships: scholarships.length,
    openScholarships: scholarships.filter((item) => item.status === 'OPEN' && deadlineActive(item)).length,
  }
}

async function loadSponsorSummary() {
  const [scholarships, unread] = await Promise.all([
    listScholarships(),
    loadUnreadCount(),
  ])
  const unitId = auth.user?.unit_id
  const ownedScholarships = unitId
    ? scholarships.filter((item) => String(item.unit_id) === String(unitId))
    : scholarships

  return {
    scholarships: ownedScholarships.length,
    openScholarships: ownedScholarships.filter((item) => item.status === 'OPEN' && deadlineActive(item)).length,
    unread,
  }
}

async function loadTeacherSummary() {
  const [dashboard, unread] = await Promise.all([
    getTeacherRecommendationDashboard(),
    loadUnreadCount(),
  ])

  return {
    pendingRecommendations: dashboard.pendingCount + dashboard.draftCount,
    submittedRecommendations: dashboard.submittedCount,
    unread,
  }
}

function resolveErrorMessage(error) {
  return error?.response?.data?.detail || error?.message || '系統總覽載入失敗'
}

async function loadDashboard() {
  loading.value = true
  loadError.value = ''

  try {
    if (auth.role === 'STUDENT') {
      summary.value = await loadStudentSummary()
    } else if (auth.role === 'REVIEWER') {
      summary.value = await loadReviewerSummary()
    } else if (auth.role === 'ADMIN') {
      summary.value = await loadAdminSummary()
    } else if (auth.role === 'SPONSOR') {
      summary.value = await loadSponsorSummary()
    } else if (auth.role === 'TEACHER') {
      summary.value = await loadTeacherSummary()
    } else {
      summary.value = {}
    }
  } catch (error) {
    console.error('載入系統總覽失敗', error)
    loadError.value = resolveErrorMessage(error)
    summary.value = {}
  } finally {
    loading.value = false
  }
}

onMounted(loadDashboard)
</script>

<template>
  <div class="dashboard-page page-grid">
    <section class="dashboard-hero">
      <div>
        <p class="eyebrow">{{ auth.roleLabel }} Workspace</p>
        <h2>{{ auth.user?.name }}，你好</h2>
        <p>{{ guidance }}</p>
      </div>
    </section>

    <LoadingSkeleton v-if="loading" :rows="4" />

    <BaseCard v-else-if="loadError" title="無法載入系統總覽" eyebrow="Dashboard">
      <p class="form-error">{{ loadError }}</p>
    </BaseCard>

    <section v-else class="stat-grid stat-grid--modern">
      <BaseCard
        v-for="stat in stats"
        :key="stat.label"
        class="stat-card stat-card--modern"
        :class="`stat-card--${stat.tone}`"
      >
        <div class="stat-card__top">
          <span class="stat-card__icon">{{ stat.icon }}</span>
          <span class="stat-card__label">{{ stat.label }}</span>
        </div>
        <strong>{{ stat.value }}</strong>
        <p>{{ stat.hint }}</p>
      </BaseCard>
    </section>

    <section v-if="!loading && !loadError" class="dashboard-two-column">
      <BaseCard title="我的待辦" eyebrow="Action Items">
        <div class="task-list">
          <div v-for="task in tasks" :key="task.title" class="task-item" :class="`task-item--${task.tone}`">
            <span aria-hidden="true"></span>
            <div>
              <strong>{{ task.title }}</strong>
              <p>{{ task.text }}</p>
            </div>
          </div>
        </div>
      </BaseCard>

      <BaseCard title="系統流程" eyebrow="Workflow">
        <div class="workflow-list workflow-list--compact">
          <div class="workflow-item">
            <strong>角色分流</strong>
            <p>側邊欄與路由 guard 會依使用者角色顯示功能。</p>
          </div>
          <div class="workflow-item">
            <strong>狀態追蹤</strong>
            <p>申請、推薦信、補件與審查結果都會同步紀錄。</p>
          </div>
          <div class="workflow-item">
            <strong>通知提醒</strong>
            <p>重要進度會集中在通知中心，避免漏掉期限。</p>
          </div>
        </div>
      </BaseCard>
    </section>
  </div>
</template>
