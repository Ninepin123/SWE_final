<script setup>
import { onMounted, reactive, ref } from 'vue'
import BaseCard from '@/components/common/BaseCard.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import { createIssueReport, listMyIssues } from '@/api/ncs'

const issues = ref([])
const error = ref('')
const success = ref('')
const loading = ref(false)

const form = reactive({
  issue_type: 'BUG',
  title: '',
  description: '',
  attachment_name: '',
  attachment_url: '',
})

async function loadIssues() {
  issues.value = await listMyIssues()
}

async function submitIssue() {
  error.value = ''
  success.value = ''

  if (!form.title.trim() || !form.description.trim()) {
    error.value = '請輸入標題與描述'
    return
  }

  loading.value = true
  try {
    await createIssueReport(form)
    success.value = '問題已送出'
    form.title = ''
    form.description = ''
    form.attachment_name = ''
    form.attachment_url = ''
    await loadIssues()
  } catch (err) {
    error.value = err?.response?.data?.detail || err?.message || '送出失敗'
  } finally {
    loading.value = false
  }
}

onMounted(loadIssues)
</script>

<template>
  <div class="page-grid">
    <BaseCard title="問題回報" eyebrow="NCS Issue Report">
      <form class="form-grid" @submit.prevent="submitIssue">
        <label>
          問題類型
          <select v-model="form.issue_type">
            <option value="BUG">系統錯誤</option>
            <option value="QUESTION">操作問題</option>
            <option value="SUGGESTION">改善建議</option>
          </select>
        </label>

        <label>
          標題
          <input v-model="form.title" type="text" />
        </label>

        <label>
          描述
          <textarea v-model="form.description" rows="5"></textarea>
        </label>

        <label>
          附件名稱
          <input v-model="form.attachment_name" type="text" placeholder="例如 screenshot.png" />
        </label>

        <label>
          附件連結
          <input v-model="form.attachment_url" type="text" />
        </label>

        <p v-if="error" class="form-error">{{ error }}</p>
        <p v-if="success" class="form-success">{{ success }}</p>

        <button class="primary-button" type="submit" :disabled="loading">
          {{ loading ? '送出中...' : '送出問題回報' }}
        </button>
      </form>
    </BaseCard>

    <EmptyState v-if="issues.length === 0" title="尚無問題回報" />

    <BaseCard v-for="issue in issues" :key="issue.issue_id" :title="issue.title" :eyebrow="issue.status">
      <p>{{ issue.description }}</p>
    </BaseCard>
  </div>
</template>