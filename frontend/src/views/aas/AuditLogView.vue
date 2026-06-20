<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import BaseCard from '@/components/common/BaseCard.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import LoadingSkeleton from '@/components/common/LoadingSkeleton.vue'
import { listAuditLogs } from '@/api/aas'
import { useToastStore } from '@/stores/toast'

const toast = useToastStore()
const loading = ref(true)
const logs = ref([])

const filters = reactive({
  actor_id: '',
  action: '',
  target_type: '',
  created_from: '',
  created_to: '',
})

const actionLabels = {
  LOGIN_SUCCESS: '登入成功',
  LOGIN_FAILED: '登入失敗',
  LOGOUT: '登出',
  CREATE_USER: '新增帳號',
  UPDATE_USER: '修改帳號',
  DELETE_USER: '刪除帳號',
  CREATE_SCHOLARSHIP: '新增獎學金',
  UPDATE_SCHOLARSHIP: '修改獎學金',
  DELETE_SCHOLARSHIP: '刪除獎學金',
}

const actionOptions = computed(() =>
  [...new Set([...Object.keys(actionLabels), ...logs.value.map((log) => log.action).filter(Boolean)])].sort(),
)

function formatDateTime(value) {
  if (!value) return '—'
  return new Intl.DateTimeFormat('zh-TW', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  }).format(new Date(value))
}

function toLocalDateTimeParam(value, { endOfRange = false } = {}) {
  const text = String(value ?? '').trim()
  if (!text) return ''
  if (/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$/.test(text)) {
    return `${text}:${endOfRange ? '59.999' : '00'}`
  }
  return text
}

function hasValidDateRange() {
  if (!filters.created_from || !filters.created_to) return true
  const from = new Date(toLocalDateTimeParam(filters.created_from)).getTime()
  const to = new Date(toLocalDateTimeParam(filters.created_to, { endOfRange: true })).getTime()
  if (!Number.isFinite(from) || !Number.isFinite(to) || from <= to) return true
  toast.error('結束時間不可早於開始時間')
  return false
}

function buildParams() {
  const params = { limit: 200 }
  if (filters.actor_id.trim()) params.actor_id = filters.actor_id.trim()
  if (filters.action) params.action = filters.action
  if (filters.target_type.trim()) params.target_type = filters.target_type.trim()
  if (filters.created_from) params.created_from = toLocalDateTimeParam(filters.created_from)
  if (filters.created_to) params.created_to = toLocalDateTimeParam(filters.created_to, { endOfRange: true })
  return params
}

async function reload() {
  if (!hasValidDateRange()) return
  loading.value = true
  try {
    logs.value = await listAuditLogs(buildParams())
  } catch (error) {
    toast.error(error.response?.data?.detail || error.message || '稽核日誌載入失敗')
  } finally {
    loading.value = false
  }
}

function resetFilters() {
  Object.assign(filters, {
    actor_id: '',
    action: '',
    target_type: '',
    created_from: '',
    created_to: '',
  })
  reload()
}

onMounted(reload)
</script>

<template>
  <div class="page-grid">
    <BaseCard title="稽核日誌" eyebrow="Audit Log">
      <template #actions>
        <button class="secondary-button" type="button" @click="resetFilters">清除條件</button>
        <button class="primary-button" type="button" @click="reload">查詢</button>
      </template>

      <div class="form-grid">
        <label>
          <span>操作者 ID</span>
          <input v-model="filters.actor_id" type="text" placeholder="例如 u-admin 或 1" />
        </label>
        <label>
          <span>動作類型</span>
          <select v-model="filters.action">
            <option value="">全部動作</option>
            <option v-for="action in actionOptions" :key="action" :value="action">
              {{ actionLabels[action] || action }}
            </option>
          </select>
        </label>
        <label>
          <span>目標類型</span>
          <input v-model="filters.target_type" type="text" placeholder="例如 user" />
        </label>
        <label>
          <span>開始時間</span>
          <input v-model="filters.created_from" type="datetime-local" />
        </label>
        <label>
          <span>結束時間</span>
          <input v-model="filters.created_to" type="datetime-local" />
        </label>
      </div>
    </BaseCard>

    <LoadingSkeleton v-if="loading" :rows="6" />

    <EmptyState
      v-else-if="!logs.length"
      title="沒有符合條件的稽核紀錄"
      description="請調整查詢條件，或先執行登入及帳號管理操作。"
      icon="archive"
    />

    <BaseCard v-else>
      <div class="table-wrap">
        <table class="data-table">
          <thead>
            <tr>
              <th>時間</th>
              <th>操作者</th>
              <th>動作</th>
              <th>影響對象</th>
              <th>詳細說明</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="log in logs" :key="log.log_id ?? log.id">
              <td>{{ formatDateTime(log.created_at) }}</td>
              <td>
                <strong>{{ log.actor_name || '未知／未登入' }}</strong>
                <span v-if="log.actor_id">ID {{ log.actor_id }}</span>
              </td>
              <td>{{ actionLabels[log.action] || log.action }}</td>
              <td>
                {{ log.target_type || '—' }}
                <span v-if="log.target_id">#{{ log.target_id }}</span>
              </td>
              <td>{{ log.detail || '—' }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </BaseCard>
  </div>
</template>
