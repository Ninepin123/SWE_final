<script setup>
import { onMounted, reactive, ref } from 'vue'
import BaseCard from '@/components/common/BaseCard.vue'
import { createSystemAlert, listSystemAlerts, updateSystemAlert } from '@/api/ncs'

const alerts = ref([])
const error = ref('')
const success = ref('')

const form = reactive({
  severity: 'INFO',
  title: '',
  body: '',
  source: 'manual',
})

async function loadAlerts() {
  alerts.value = await listSystemAlerts()
}

async function submitAlert() {
  error.value = ''
  success.value = ''

  if (!form.title.trim()) {
    error.value = '請輸入警示標題'
    return
  }

  try {
    await createSystemAlert(form)
    success.value = '系統警示已建立'
    form.title = ''
    form.body = ''
    await loadAlerts()
  } catch (err) {
    error.value = err?.response?.data?.detail || err?.message || '建立失敗'
  }
}

async function resolveAlert(alert) {
  await updateSystemAlert(alert.alert_id, { status: 'RESOLVED' })
  await loadAlerts()
}

onMounted(loadAlerts)
</script>

<template>
  <div class="page-grid">
    <BaseCard title="系統警示" eyebrow="NCS System Alert">
      <form class="form-grid" @submit.prevent="submitAlert">
        <label>
          等級
          <select v-model="form.severity">
            <option value="INFO">INFO</option>
            <option value="WARNING">WARNING</option>
            <option value="ERROR">ERROR</option>
            <option value="CRITICAL">CRITICAL</option>
          </select>
        </label>

        <label>
          標題
          <input v-model="form.title" type="text" />
        </label>

        <label>
          內容
          <textarea v-model="form.body" rows="4"></textarea>
        </label>

        <p v-if="error" class="form-error">{{ error }}</p>
        <p v-if="success" class="form-success">{{ success }}</p>

        <button class="primary-button" type="submit">建立警示</button>
      </form>
    </BaseCard>

    <BaseCard v-for="alert in alerts" :key="alert.alert_id" :title="alert.title" :eyebrow="alert.severity">
      <p>{{ alert.body }}</p>
      <p>狀態：{{ alert.status }}</p>
      <button
        v-if="alert.status !== 'RESOLVED'"
        class="primary-button"
        type="button"
        @click="resolveAlert(alert)"
      >
        標記已處理
      </button>
    </BaseCard>
  </div>
</template>