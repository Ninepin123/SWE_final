<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import BaseCard from '@/components/common/BaseCard.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import LoadingSkeleton from '@/components/common/LoadingSkeleton.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import { listSupplementRequests, submitSupplement } from '@/api/sas'
import { useToastStore } from '@/stores/toast'

const route = useRoute()
const router = useRouter()
const toast = useToastStore()
const loading = ref(true)
const submitting = ref(false)
const requests = ref([])
const responseText = ref('')
const error = ref('')

const activeRequest = computed(() =>
  requests.value.find((request) => request.status === 'REQUESTED'),
)

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

async function submit() {
  error.value = ''
  if (!responseText.value.trim()) {
    error.value = '請填寫補件內容。'
    return
  }
  if (!window.confirm('補件送出後不能再次修改，確定送出嗎？')) return
  submitting.value = true
  try {
    await submitSupplement(
      Number(route.params.id),
      activeRequest.value.supplement_id,
      { response_text: responseText.value.trim() },
    )
    toast.success('補件已送出，申請重新進入審查')
    router.push('/applications')
  } catch (submitError) {
    error.value =
      submitError.response?.data?.detail || submitError.message || '補件送出失敗'
  } finally {
    submitting.value = false
  }
}

onMounted(async () => {
  try {
    requests.value = await listSupplementRequests(Number(route.params.id))
  } catch (loadError) {
    error.value = loadError.response?.data?.detail || loadError.message || '補件資料載入失敗'
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <LoadingSkeleton v-if="loading" :rows="4" />

  <div v-else class="page-grid">
    <BaseCard title="補件要求" eyebrow="Supplement">
      <p v-if="error" class="form-error">{{ error }}</p>

      <div v-if="activeRequest" class="review-list">
        <div>
          <dt>狀態</dt>
          <dd><StatusBadge value="NEED_SUPPLEMENT" /></dd>
        </div>
        <div>
          <dt>補件項目</dt>
          <dd>{{ activeRequest.required_items }}</dd>
        </div>
        <div>
          <dt>補件期限</dt>
          <dd>{{ formatDate(activeRequest.deadline) }}</dd>
        </div>
      </div>

      <EmptyState
        v-else
        title="目前沒有待處理的補件要求"
        description="補件可能已送出，或審查人員尚未建立補件要求。"
        icon="check"
      />
    </BaseCard>

    <BaseCard v-if="activeRequest" title="提交文字補件">
      <label class="stacked-field">
        <span>補件內容</span>
        <textarea
          v-model="responseText"
          rows="10"
          placeholder="請依補件項目補充說明、資料或證明內容"
        />
      </label>
      <div class="form-actions">
        <button class="primary-button" type="button" :disabled="submitting" @click="submit">
          {{ submitting ? '送出中' : '送出補件' }}
        </button>
      </div>
    </BaseCard>

    <BaseCard v-if="requests.length" title="補件歷程">
      <div class="table-wrap">
        <table class="data-table">
          <thead>
            <tr>
              <th>建立時間</th>
              <th>要求內容</th>
              <th>期限</th>
              <th>狀態</th>
              <th>送出內容</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="request in requests" :key="request.supplement_id">
              <td>{{ formatDate(request.created_at) }}</td>
              <td>{{ request.required_items }}</td>
              <td>{{ formatDate(request.deadline) }}</td>
              <td>{{ request.status === 'SUBMITTED' ? '已送出' : '待補件' }}</td>
              <td>{{ request.response_text || '—' }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </BaseCard>
  </div>
</template>
