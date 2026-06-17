<script setup>
import { computed, onMounted, ref } from 'vue'
import BaseCard from '@/components/common/BaseCard.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import LoadingSkeleton from '@/components/common/LoadingSkeleton.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import { listRecommendationRequests, submitRecommendation } from '@/api/trs'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'

const auth = useAuthStore()
const toast = useToastStore()
const loading = ref(true)
const requests = ref([])
const selectedId = ref('')
const content = ref('')
const error = ref('')

const selected = computed(() => requests.value.find((item) => item.id === selectedId.value))

function formatDate(value) {
  if (!value) return '-'
  return new Intl.DateTimeFormat('zh-TW', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  }).format(new Date(value))
}

async function reload() {
  requests.value = await listRecommendationRequests(auth.user.id)
  if (!selectedId.value && requests.value.length) {
    selectedId.value = requests.value[0].id
    content.value = requests.value[0].content || ''
  }
}

function choose(request) {
  selectedId.value = request.id
  content.value = request.content || ''
  error.value = ''
}

async function submit() {
  error.value = ''
  if (content.value.trim().length < 30) {
    error.value = '推薦內容至少需要 30 個字。'
    return
  }
  await submitRecommendation(auth.user.id, selected.value.id, content.value)
  toast.success('推薦信已送出')
  await reload()
}

onMounted(async () => {
  await reload()
  loading.value = false
})
</script>

<template>
  <LoadingSkeleton v-if="loading" :rows="4" />

  <EmptyState
    v-else-if="!requests.length"
    title="目前沒有推薦邀請"
    description="當學生填寫你的推薦人資料後，邀請會出現在這裡。"
    icon="recommend"
  />

  <div v-else class="split-layout">
    <BaseCard title="推薦邀請" eyebrow="Requests">
      <div class="request-list">
        <button
          v-for="request in requests"
          :key="request.id"
          type="button"
          class="request-item"
          :class="{ 'request-item--active': request.id === selectedId }"
          @click="choose(request)"
        >
          <span>{{ request.application?.student?.name }}</span>
          <strong>{{ request.application?.scholarship?.title }}</strong>
          <small>邀請日 {{ formatDate(request.invitedAt) }}</small>
          <StatusBadge :value="request.status" />
        </button>
      </div>
    </BaseCard>

    <BaseCard v-if="selected" title="填寫推薦內容" eyebrow="Recommendation Letter">
      <dl class="review-list">
        <div>
          <dt>學生</dt>
          <dd>{{ selected.application?.student?.name }} · {{ selected.application?.profile?.department }}</dd>
        </div>
        <div>
          <dt>獎學金</dt>
          <dd>{{ selected.application?.scholarship?.title }}</dd>
        </div>
        <div>
          <dt>申請狀態</dt>
          <dd><StatusBadge :value="selected.application?.status" /></dd>
        </div>
      </dl>

      <p v-if="error" class="form-error">{{ error }}</p>
      <label class="stacked-field">
        <span>推薦內容</span>
        <textarea
          v-model="content"
          :disabled="selected.status === 'SUBMITTED'"
          rows="10"
          placeholder="請描述學生的學習表現、專業能力、品格與推薦理由"
        />
      </label>

      <div class="form-actions">
        <button
          class="primary-button"
          type="button"
          :disabled="selected.status === 'SUBMITTED'"
          @click="submit"
        >
          {{ selected.status === 'SUBMITTED' ? '已送出' : '送出推薦信' }}
        </button>
      </div>
    </BaseCard>
  </div>
</template>
