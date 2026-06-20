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
      { label: '查看可申請獎學金', to: '/scholarships' },
      { label: '追蹤我的申請', to: '/applications' },
      { label: '更新個人資料', to: '/profile' },
      { label: '查看公告', to: '/announcements' },
      { label: '查看通知', to: '/notifications' },
      { label: '公告中心', to: '/announcements' }
    ],
    REVIEWER: [
      { label: '進入審查工作台', to: '/reviews' },
      { label: '查看公告', to: '/announcements' },
      { label: '查看通知', to: '/notifications' },
      { label: '公告中心', to: '/announcements' }
    ],
    ADMIN: [
      { label: '管理帳號', to: '/admin/users' },
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
      { label: '處理推薦信邀請', to: '/recommendations' },
      { label: '查看公告', to: '/announcements' },
      { label: '查看通知', to: '/notifications' },
      { label: '公告中心', to: '/announcements' }
    ],
    SPONSOR: [
      { label: '管理獎學金', to: '/admin/scholarships' },
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
      { label: '我的申請', value: summary.value.applications ?? 0 },
      { label: '審查中', value: summary.value.underReview ?? 0 },
      { label: '需補件', value: summary.value.needsSupplement ?? 0 },
      { label: '可申請', value: summary.value.availableScholarships ?? 0 },
      { label: '未讀通知', value: summary.value.unread ?? 0 },
    ]
  }

  if (auth.role === 'REVIEWER') {
    return [
      { label: '待處理', value: summary.value.pending ?? 0 },
      { label: '已通過', value: summary.value.approved ?? 0 },
      { label: '未通過', value: summary.value.rejected ?? 0 },
      { label: '未讀通知', value: summary.value.unread ?? 0 },
    ]
  }

  if (auth.role === 'ADMIN') {
    return [
      { label: '帳號數', value: summary.value.users ?? 0 },
      { label: '獎學金', value: summary.value.scholarships ?? 0 },
      { label: '開放中', value: summary.value.openScholarships ?? 0 },
      { label: '未讀通知', value: summary.value.unread ?? 0 },
    ]
  }

  if (auth.role === 'SPONSOR') {
    return [
      { label: '獎學金', value: summary.value.scholarships ?? 0 },
      { label: '開放中', value: summary.value.openScholarships ?? 0 },
      { label: '未讀通知', value: summary.value.unread ?? 0 },
    ]
  }

  return [
    { label: '待填推薦信', value: summary.value.pendingRecommendations ?? 0 },
    { label: '已送出推薦', value: summary.value.submittedRecommendations ?? 0 },
    { label: '未讀通知', value: summary.value.unread ?? 0 },
  ]
})

const guidance = computed(() => {
  const text = {
    STUDENT:
      '從可申請獎學金開始，系統會阻擋重複申請，並在送出後建立推薦信邀請與通知。',
    REVIEWER: '審查工作台會顯示申請文件、推薦信狀態與完整 audit timeline。',
    ADMIN: '管理員只負責帳號與獎學金 CRUD，不提供申請審查入口。',
    TEACHER: '教師只能看到指派給自己的推薦邀請，學生只能看狀態，不會看到內容。',
    SPONSOR: '獎助單位人員可管理所屬單位的獎學金資料，且不能修改其他單位的內容。',
  }

  return text[auth.role] ?? '請依照角色使用系統功能。'
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
  <div class="page-grid">
    <BaseCard class="hero-card" :title="`${auth.user?.name ?? '使用者'}，你好`" :eyebrow="auth.roleLabel">
      <p>{{ guidance }}</p>

      <div class="hero-card__actions">
        <RouterLink
          v-for="link in quickLinks"
          :key="link.to"
          class="primary-button"
          :to="link.to"
        >
          {{ link.label }}
        </RouterLink>
      </div>
    </BaseCard>

    <LoadingSkeleton v-if="loading" :rows="4" />

    <section v-else class="stat-grid">
      <BaseCard v-for="stat in stats" :key="stat.label" class="stat-card">
        <span>{{ stat.label }}</span>
        <strong>{{ stat.value }}</strong>
      </BaseCard>
    </section>

    <BaseCard title="今日重點" eyebrow="Workflow">
      <div class="workflow-list">
        <div class="workflow-item">
          <strong>權限清楚分流</strong>
          <p>側邊欄與路由 guard 都依角色控制，無權限頁面無法進入。</p>
        </div>

        <div class="workflow-item">
          <strong>狀態可追蹤</strong>
          <p>申請、推薦信、補件與審查結果都會同步出現在通知與紀錄中。</p>
        </div>

        <div class="workflow-item">
          <strong>公告與通知整合</strong>
          <p>系統公告可由管理員發布，使用者可於公告中心與通知中心查看重要訊息。</p>
        </div>

        <div class="workflow-item">
          <strong>後端 API 可接軌</strong>
          <p>目前部分總覽資料仍使用 mock store，NCS 通知數已可透過 `/api/ncs/notifications/unread-count` 接軌真實 API。</p>
        </div>
      </div>
    </BaseCard>
  </div>
</template>
```
