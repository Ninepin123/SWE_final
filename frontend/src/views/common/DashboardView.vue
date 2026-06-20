<script setup>
import { computed, onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import BaseCard from '@/components/common/BaseCard.vue'
import LoadingSkeleton from '@/components/common/LoadingSkeleton.vue'
import { useAuthStore } from '@/stores/auth'
import { getDashboardSummary } from '@/services/mockBackend'
import { getUnreadNotificationCount } from '@/api/ncs'

const auth = useAuthStore()
const loading = ref(true)
const summary = ref({})

const quickLinks = computed(() => {
  const links = {
    STUDENT: [
      { label: '查看可申請獎學金', to: '/scholarships', primary: true },
      { label: '追蹤我的申請', to: '/applications' },
      { label: '更新個人資料', to: '/profile' },
      { label: '查看公告', to: '/announcements' },
      { label: '查看通知', to: '/notifications' },
      { label: '公告中心', to: '/announcements' }
    ],
    REVIEWER: [
      { label: '進入審查工作台', to: '/reviews', primary: true },
      { label: '查看公告', to: '/announcements' },
      { label: '查看通知', to: '/notifications' },
      { label: '公告中心', to: '/announcements' }
    ],
    ADMIN: [
      { label: '管理帳號', to: '/admin/users', primary: true },
      { label: '管理獎學金', to: '/admin/scholarships' },
      { label: '公告管理', to: '/admin/announcements' },
      { label: '查看公告', to: '/announcements' },
      { label: '查看通知', to: '/notifications' },
      { label: '公告中心', to: '/announcements' },
      {
        label: '公告管理',
        to: '/admin/announcements',
        roles: ['ADMIN'],
      }
    ],
    TEACHER: [
      { label: '處理推薦信邀請', to: '/recommendations', primary: true },
      { label: '查看公告', to: '/announcements' },
      { label: '查看通知', to: '/notifications' },
      { label: '公告中心', to: '/announcements' }
    ],
    SPONSOR: [
      { label: '管理獎學金', to: '/admin/scholarships', primary: true },
      { label: '查看公告', to: '/announcements' },
      { label: '查看通知', to: '/notifications' },
      { label: '公告中心', to: '/announcements' }
    ],
  }

  return links[auth.role] ?? []
})

const stats = computed(() => {
  if (auth.role === 'STUDENT') {
    return [
      { label: '我的申請', value: summary.value.applications ?? 0, tone: 'info', icon: '📄', hint: '已建立的申請紀錄' },
      { label: '審查中', value: summary.value.underReview ?? 0, tone: 'blue', icon: '🔎', hint: '正在等待審核' },
      { label: '需補件', value: summary.value.needsSupplement ?? 0, tone: 'warning', icon: '⚠️', hint: '請優先處理' },
      { label: '可申請', value: summary.value.availableScholarships ?? 0, tone: 'success', icon: '🎓', hint: '目前開放項目' },
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
      { label: '未讀通知', value: summary.value.unread ?? 0, tone: 'warning', icon: '🔔', hint: '待確認訊息' },
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
      { title: '查看可申請獎學金', text: `${summary.value.availableScholarships ?? 0} 項目前可申請`, tone: 'success' },
      { title: '追蹤申請進度', text: `${summary.value.underReview ?? 0} 件申請審查中`, tone: 'info' },
    ]
  }
  return [
    { title: '處理待辦事項', text: '依照側邊欄進入主要工作區', tone: 'warning' },
    { title: '確認通知中心', text: `${summary.value.unread ?? 0} 則未讀通知`, tone: 'info' },
    { title: '維護資料完整性', text: '定期檢查資料與狀態是否正確', tone: 'success' },
  ]
})

async function loadDashboard() {
  loading.value = true

  try {
    const dashboardSummary = await getDashboardSummary(auth.user)
    let unread = dashboardSummary?.unread ?? 0

    try {
      unread = await getUnreadNotificationCount()
    } catch (error) {
      console.warn('取得未讀通知數失敗，改用 dashboard summary 的 unread 值', error)
    }

    summary.value = {
      ...(dashboardSummary ?? {}),
      unread,
    }
  } catch (error) {
    console.error('載入系統總覽失敗', error)
    summary.value = {
      unread: 0,
    }
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
      <div class="dashboard-hero__actions">
        <RouterLink
          v-for="link in quickLinks"
          :key="link.to"
          :class="link.primary ? 'primary-button' : 'secondary-button'"
          :to="link.to"
        >
          {{ link.label }}
        </RouterLink>
      </div>
    </section>

    <LoadingSkeleton v-if="loading" :rows="4" />

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

    <section class="dashboard-two-column">
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
