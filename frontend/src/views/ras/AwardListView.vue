<script setup>
import { ref, computed, onMounted } from 'vue'
import BaseCard from '@/components/common/BaseCard.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import LoadingSkeleton from '@/components/common/LoadingSkeleton.vue'
import { getAwardList } from '@/api/ras'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const loading = ref(true)
const awards = ref([])

const filterYear = ref('')
const keyword = ref('')

async function reload() {
  loading.value = true
  try {
    const params = {}
    if (filterYear.value) {
      params.year = filterYear.value
    }
    awards.value = await getAwardList(params)
  } catch (error) {
    console.error('Failed to fetch award list:', error)
  } finally {
    loading.value = false
  }
}

const filteredAwards = computed(() => {
  const query = keyword.value.trim().toLowerCase()
  return awards.value.filter((award) => {
    if (!query) return true
    return [
      award.student_name,
      award.department,
      award.scholarship_name,
    ]
      .filter(Boolean)
      .some((field) => String(field).toLowerCase().includes(query))
  })
})

const totalAmount = computed(() => {
  return filteredAwards.value.reduce((sum, award) => sum + (award.amount || 0), 0)
})

function formatCurrency(amount) {
  return new Intl.NumberFormat('zh-TW', { style: 'currency', currency: 'TWD', minimumFractionDigits: 0 }).format(amount)
}

function formatDate(value) {
  if (!value) return '-'
  return new Intl.DateTimeFormat('zh-TW', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  }).format(new Date(value))
}

onMounted(() => {
  reload()
})
</script>

<template>
  <div class="page-grid">
    <BaseCard title="核發名單" eyebrow="Award List">
      <div class="toolbar">
        <label class="search-field">
          <span>搜尋</span>
          <input v-model="keyword" type="search" placeholder="學生姓名、系所、獎學金" />
        </label>
        <label>
          <span>申請年度</span>
          <input v-model="filterYear" type="number" placeholder="全部" @change="reload" />
        </label>
        <button class="secondary-button" @click="reload">重新整理</button>
      </div>
      
      <div class="statistics-bar" style="margin-top: 1rem; padding: 1rem; background: var(--surface-2); border-radius: var(--radius-sm);">
        <strong>總得獎人數：</strong> {{ filteredAwards.length }} 人
        <strong style="margin-left: 1.5rem;">總核發金額：</strong> {{ formatCurrency(totalAmount) }}
      </div>
    </BaseCard>

    <LoadingSkeleton v-if="loading" :rows="5" />
    <EmptyState
      v-else-if="!filteredAwards.length"
      title="目前沒有核發名單"
      description="目前查無任何已通過的審查案件。"
      icon="review"
    />

    <BaseCard v-else>
      <div class="table-wrap">
        <table class="data-table">
          <thead>
            <tr>
              <th>獎學金 (年度)</th>
              <th>學生姓名</th>
              <th>系所</th>
              <th>核定金額</th>
              <th>審核時間</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="award in filteredAwards" :key="award.application_id">
              <td>
                <strong>{{ award.scholarship_name }}</strong>
                <span>{{ award.year }}</span>
              </td>
              <td>
                <strong>{{ award.student_name }}</strong>
              </td>
              <td>{{ award.department }}</td>
              <td style="color: var(--primary);">{{ formatCurrency(award.amount) }}</td>
              <td>{{ formatDate(award.reviewed_at) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </BaseCard>
  </div>
</template>

<style scoped>
.statistics-bar {
  display: flex;
  align-items: center;
  font-size: 1.1rem;
}
.toolbar {
  display: flex;
  gap: 1rem;
  align-items: flex-end;
}
</style>
