<script setup>
import { ref, onMounted } from 'vue'
import BaseCard from '@/components/common/BaseCard.vue'
import LoadingSkeleton from '@/components/common/LoadingSkeleton.vue'
import Icon from '@/components/common/Icon.vue'
import { getStatistics, exportStatisticsCsv } from '@/api/ras'
import { useToastStore } from '@/stores/toast'

const toast = useToastStore()
const loading = ref(true)
const stats = ref(null)

const filterYear = ref('')

async function reload() {
  loading.value = true
  try {
    const params = {}
    if (filterYear.value) {
      params.year = filterYear.value
    }
    stats.value = await getStatistics(params)
  } catch (error) {
    console.error('Failed to fetch statistics:', error)
    toast.error('無法取得統計資料')
  } finally {
    loading.value = false
  }
}

async function handleExport() {
  const params = {}
  if (filterYear.value) {
    params.year = filterYear.value
  }
  toast.info('準備匯出 CSV 報表...')
  await exportStatisticsCsv(params)
}

function formatCurrency(amount) {
  return new Intl.NumberFormat('zh-TW', { style: 'currency', currency: 'TWD', minimumFractionDigits: 0 }).format(amount)
}

onMounted(() => {
  reload()
})
</script>

<template>
  <div class="page-grid">
    <BaseCard title="年度統計與報表" eyebrow="Statistics & Reports">
      <div class="toolbar">
        <label>
          <span>統計年度</span>
          <input v-model="filterYear" type="number" placeholder="全部年度" @change="reload" />
        </label>
        <button class="secondary-button" @click="reload">重新整理</button>
        <div style="flex-grow: 1;"></div>
        <button class="primary-button" @click="handleExport">
          <Icon name="download" /> 匯出 CSV 報表
        </button>
      </div>
    </BaseCard>

    <LoadingSkeleton v-if="loading" :rows="6" />

    <template v-else-if="stats">
      <!-- 總覽數據卡片 -->
      <div class="overview-grid">
        <BaseCard class="stat-card">
          <div class="stat-label">總得獎人數</div>
          <div class="stat-value">{{ stats.total_winners }} <span class="stat-unit">人</span></div>
        </BaseCard>
        <BaseCard class="stat-card">
          <div class="stat-label">總核發金額</div>
          <div class="stat-value highlight">{{ formatCurrency(stats.total_amount) }}</div>
        </BaseCard>
      </div>

      <!-- 各單位通過比例表格 -->
      <BaseCard title="各單位審查統計">
        <div class="table-wrap">
          <table class="data-table">
            <thead>
              <tr>
                <th>提供單位</th>
                <th>申請總數</th>
                <th>通過人數</th>
                <th>通過比例</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="!stats.unit_stats.length">
                <td colspan="4" class="text-center muted-text">尚無任何單位統計資料</td>
              </tr>
              <tr v-for="unit in stats.unit_stats" :key="unit.unit_name">
                <td><strong>{{ unit.unit_name }}</strong></td>
                <td>{{ unit.total_applications }}</td>
                <td><span style="color: var(--primary); font-weight: 600;">{{ unit.approved_count }}</span></td>
                <td>
                  <div class="progress-bar-container">
                    <div class="progress-bar" :style="{ width: unit.pass_rate + '%' }"></div>
                    <span class="progress-text">{{ unit.pass_rate }}%</span>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </BaseCard>
    </template>
  </div>
</template>

<style scoped>
.toolbar {
  display: flex;
  gap: 1rem;
  align-items: flex-end;
  margin-top: 1rem;
}
.overview-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
}
.stat-card {
  text-align: center;
  padding: 2rem !important;
}
.stat-label {
  font-size: 1.1rem;
  color: var(--text-2);
  margin-bottom: 0.5rem;
}
.stat-value {
  font-size: 2.5rem;
  font-weight: 700;
  color: var(--text-1);
}
.stat-value.highlight {
  color: var(--primary);
}
.stat-unit {
  font-size: 1.2rem;
  font-weight: normal;
  color: var(--text-2);
}
.progress-bar-container {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
.progress-bar {
  height: 8px;
  background-color: var(--primary);
  border-radius: 4px;
  min-width: 5px;
}
.progress-text {
  font-size: 0.9rem;
  color: var(--text-2);
  min-width: 45px;
}
.text-center {
  text-align: center;
}
</style>
