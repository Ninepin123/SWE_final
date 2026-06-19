<script setup>
import { onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import BaseCard from '@/components/common/BaseCard.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import LoadingSkeleton from '@/components/common/LoadingSkeleton.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import { listMyApplications } from '@/api/sas'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'

const auth = useAuthStore()
const toast = useToastStore()
const loading = ref(true)
const applications = ref([])

function formatDate(value) {
  if (!value) return '—'
  return new Intl.DateTimeFormat('zh-TW', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(value))
}

onMounted(async () => {
  try {
    applications.value = await listMyApplications(auth.user?.user_id ?? auth.user?.id)
  } catch (error) {
    toast.error(error.response?.data?.detail || error.message || '申請紀錄載入失敗')
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <LoadingSkeleton v-if="loading" :rows="4" />

  <EmptyState
    v-else-if="!applications.length"
    title="尚未建立任何申請"
    description="從可申請獎學金開始，可以先儲存草稿，再於期限內正式送出。"
    icon="application"
  />

  <div v-else class="page-grid">
    <BaseCard title="我的申請紀錄" eyebrow="Applications">
      <div class="table-wrap">
        <table class="data-table">
          <thead>
            <tr>
              <th>獎學金</th>
              <th>建立時間</th>
              <th>送出時間</th>
              <th>狀態</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="application in applications" :key="application.application_id ?? application.id">
              <td>
                <strong>{{ application.scholarship_name ?? application.scholarship?.title }}</strong>
              </td>
              <td>{{ formatDate(application.created_at ?? application.submittedAt) }}</td>
              <td>{{ formatDate(application.submitted_at ?? application.submittedAt) }}</td>
              <td><StatusBadge :value="application.status" /></td>
              <td>
                <RouterLink
                  v-if="application.status === 'DRAFT'"
                  class="primary-button"
                  :to="`/scholarships/${application.scholarship_id}/apply`"
                >
                  繼續填寫
                </RouterLink>
                <span v-else class="muted-text">已送出，無法修改</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </BaseCard>
  </div>
</template>
