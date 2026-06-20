<script setup>
import { computed, onMounted, ref } from 'vue'
import BaseCard from '@/components/common/BaseCard.vue'
import { listSystemAlerts, updateSystemAlert } from '@/api/ncs'

const alerts = ref([])
const loading = ref(false)
const error = ref('')
const resolvingId = ref(null)

async function loadAlerts() {
  loading.value = true
  error.value = ''

  try {
    alerts.value = await listSystemAlerts()
  } catch (err) {
    error.value = err?.response?.data?.detail || err?.message || '系統警示載入失敗'
  } finally {
    loading.value = false
  }
}

async function resolveAlert(alert) {
  const alertId = alert.alert_id ?? alert.alertId ?? alert.id
  resolvingId.value = alertId
  error.value = ''

  try {
    await updateSystemAlert(alertId, { status: 'RESOLVED' })
    await loadAlerts()
  } catch (err) {
    error.value = err?.response?.data?.detail || err?.message || '警示狀態更新失敗'
  } finally {
    resolvingId.value = null
  }
}

const openAlerts = computed(() => alerts.value.filter((alert) => alert.status !== 'RESOLVED'))

const dashboardStats = computed(() => [
  {
    label: '未處理',
    value: openAlerts.value.length,
    hint: '等待管理員確認與追蹤',
    tone: 'danger',
  },
  {
    label: '嚴重警示',
    value: alerts.value.filter((alert) => alert.severity === 'CRITICAL').length,
    hint: '由監控模組自動升級',
    tone: 'critical',
  },
  {
    label: '已處理',
    value: alerts.value.filter((alert) => alert.status === 'RESOLVED').length,
    hint: '已完成確認的紀錄',
    tone: 'success',
  },
  {
    label: '警示總數',
    value: alerts.value.length,
    hint: '系統自動發布紀錄',
    tone: 'info',
  },
])

function severityLabel(severity) {
  return {
    INFO: '資訊',
    WARNING: '注意',
    ERROR: '錯誤',
    CRITICAL: '嚴重',
  }[severity] ?? severity
}

function statusLabel(status) {
  return status === 'RESOLVED' ? '已處理' : '未處理'
}

function statusTone(status) {
  return status === 'RESOLVED' ? 'success' : 'warning'
}

function sourceLabel(source) {
  const value = String(source ?? '').toLowerCase()

  if (!value) return '系統監控模組'
  if (value.includes('aas')) return 'AAS 監控模組'
  if (value.includes('ncs')) return 'NCS 通知模組'
  if (value.includes('system')) return '系統監控模組'

  return source
}

function formatDate(value) {
  if (!value) return '尚未紀錄'

  return new Intl.DateTimeFormat('zh-TW', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(value))
}

onMounted(loadAlerts)
</script>

<template>
  <div class="system-alert-page page-grid">
    <section class="system-alert-hero">
      <div>
        <p class="eyebrow">System Generated</p>
        <h2>系統自動發布警示</h2>
        <p>
          AAS、NCS 與排程服務的自動事件集中在此，依最新發布時間排序並保留處理紀錄。
        </p>
      </div>

      <button class="secondary-button" type="button" :disabled="loading" @click="loadAlerts">
        {{ loading ? '同步中' : '重新同步' }}
      </button>
    </section>

    <div class="system-alert-stats">
      <BaseCard
        v-for="stat in dashboardStats"
        :key="stat.label"
        class="system-alert-stat"
        :class="`system-alert-stat--${stat.tone}`"
      >
        <span>{{ stat.label }}</span>
        <strong>{{ stat.value }}</strong>
        <p>{{ stat.hint }}</p>
      </BaseCard>
    </div>

    <BaseCard class="system-alert-board" title="自動警示紀錄" eyebrow="NCS System Alert">
      <template #actions>
        <span class="system-alert-board__note">由系統監控與排程服務發布</span>
      </template>

      <p v-if="error" class="form-error">{{ error }}</p>

      <div v-if="loading" class="skeleton-list">
        <div class="skeleton-row">
          <span></span>
          <span></span>
          <span></span>
        </div>
      </div>

      <div v-else-if="!alerts.length" class="empty-state empty-state--inline">
        <span class="empty-state__mark">!</span>
        <p>目前沒有系統自動發布的警示。</p>
      </div>

      <div v-else class="system-alert-list">
        <article
          v-for="alert in alerts"
          :key="alert.alert_id"
          class="system-alert-row"
          :class="[
            `system-alert-row--${String(alert.severity).toLowerCase()}`,
            { 'system-alert-row--resolved': alert.status === 'RESOLVED' },
          ]"
        >
          <div class="system-alert-row__level">
            <span class="system-alert-row__dot"></span>
            <strong>{{ alert.severity }}</strong>
            <small>{{ severityLabel(alert.severity) }}</small>
          </div>

          <div class="system-alert-row__content">
            <div class="system-alert-row__top">
              <h3>{{ alert.title || '未命名系統警示' }}</h3>
              <span class="status-badge" :class="`status-badge--${statusTone(alert.status)}`">
                {{ statusLabel(alert.status) }}
              </span>
            </div>

            <p>{{ alert.body || '系統未提供補充內容。' }}</p>

            <dl class="system-alert-row__meta">
              <div>
                <dt>來源</dt>
                <dd>{{ sourceLabel(alert.source) }}</dd>
              </div>
              <div>
                <dt>發布時間</dt>
                <dd>{{ formatDate(alert.createdAt || alert.created_at) }}</dd>
              </div>
              <div>
                <dt>處理時間</dt>
                <dd>{{ formatDate(alert.resolvedAt || alert.resolved_at) }}</dd>
              </div>
            </dl>
          </div>

          <div class="system-alert-row__actions">
            <button
              v-if="alert.status !== 'RESOLVED'"
              class="primary-button"
              type="button"
              :disabled="resolvingId === (alert.alert_id ?? alert.alertId ?? alert.id)"
              @click="resolveAlert(alert)"
            >
              {{ resolvingId === (alert.alert_id ?? alert.alertId ?? alert.id) ? '處理中' : '標記已處理' }}
            </button>
          </div>
        </article>
      </div>
    </BaseCard>
  </div>
</template>

<style scoped>
.system-alert-page {
  width: 100%;
}

.system-alert-hero {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  padding: 26px 28px;
  border: 1px solid rgba(47, 107, 79, 0.16);
  border-radius: 18px;
  background:
    linear-gradient(135deg, rgba(255, 253, 248, 0.96), rgba(231, 241, 235, 0.86));
  box-shadow: var(--shadow-sm);
}

.system-alert-hero h2 {
  margin-top: 6px;
  font-size: 28px;
}

.system-alert-hero p:not(.eyebrow) {
  max-width: 780px;
  margin-top: 8px;
  color: var(--text-secondary);
  line-height: 1.7;
}

.system-alert-stats {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
}

.system-alert-stat {
  position: relative;
  overflow: hidden;
  min-height: 142px;
}

.system-alert-stat::before {
  content: "";
  position: absolute;
  inset: 0 auto 0 0;
  width: 5px;
  background: var(--info);
}

.system-alert-stat--danger::before,
.system-alert-stat--critical::before {
  background: var(--danger);
}

.system-alert-stat--success::before {
  background: var(--success);
}

.system-alert-stat span {
  color: var(--muted);
  font-size: 13px;
  font-weight: 700;
}

.system-alert-stat strong {
  display: block;
  margin-top: 14px;
  font-family: var(--font-serif);
  font-size: 42px;
  font-weight: 600;
  line-height: 1;
}

.system-alert-stat p {
  margin-top: 10px;
  color: var(--text-secondary);
  line-height: 1.6;
}

.system-alert-board {
  min-height: 420px;
}

.system-alert-board__note {
  color: var(--muted);
  font-size: 13px;
  font-weight: 700;
}

.system-alert-list {
  display: grid;
  gap: 12px;
}

.system-alert-row {
  display: grid;
  grid-template-columns: 140px minmax(0, 1fr) minmax(140px, auto);
  gap: 18px;
  align-items: stretch;
  padding: 18px;
  border: 1px solid var(--line);
  border-left: 5px solid var(--info);
  border-radius: var(--radius-lg);
  background: linear-gradient(180deg, #fffdf8, #fbf6ec);
}

.system-alert-row--warning {
  border-left-color: var(--warning);
}

.system-alert-row--error,
.system-alert-row--critical {
  border-left-color: var(--danger);
}

.system-alert-row--resolved {
  opacity: 0.82;
}

.system-alert-row__level {
  display: grid;
  align-content: start;
  gap: 5px;
  padding-top: 2px;
}

.system-alert-row__dot {
  width: 12px;
  height: 12px;
  border-radius: var(--radius-pill);
  background: var(--info);
}

.system-alert-row--warning .system-alert-row__dot {
  background: var(--warning);
}

.system-alert-row--error .system-alert-row__dot,
.system-alert-row--critical .system-alert-row__dot {
  background: var(--danger);
}

.system-alert-row__level strong {
  font-family: var(--font-mono);
  font-size: 13px;
  letter-spacing: 0.08em;
}

.system-alert-row__level small {
  color: var(--muted);
  font-weight: 700;
}

.system-alert-row__content {
  min-width: 0;
}

.system-alert-row__top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.system-alert-row__top h3 {
  font-size: 17px;
}

.system-alert-row__content > p {
  margin-top: 10px;
  color: var(--text-secondary);
  line-height: 1.7;
}

.system-alert-row__meta {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
  margin: 16px 0 0;
}

.system-alert-row__meta div {
  min-width: 0;
  padding: 10px 12px;
  border: 1px solid rgba(211, 195, 165, 0.7);
  border-radius: var(--radius-md);
  background: var(--surface-muted);
}

.system-alert-row__meta dt {
  font-size: 12px;
}

.system-alert-row__meta dd {
  margin-top: 4px;
  color: var(--text);
  font-weight: 700;
}

.system-alert-row__actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
}

@media (max-width: 1180px) {
  .system-alert-stats {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .system-alert-row {
    grid-template-columns: 120px minmax(0, 1fr);
  }

  .system-alert-row__actions {
    grid-column: 2;
    justify-content: flex-start;
  }
}

@media (max-width: 760px) {
  .system-alert-hero {
    align-items: stretch;
    flex-direction: column;
  }

  .system-alert-stats,
  .system-alert-row,
  .system-alert-row__meta {
    grid-template-columns: 1fr;
  }

  .system-alert-row__actions {
    grid-column: auto;
  }
}
</style>
