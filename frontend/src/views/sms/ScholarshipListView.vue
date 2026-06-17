<script setup>
import { computed, onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import BaseCard from '@/components/common/BaseCard.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import LoadingSkeleton from '@/components/common/LoadingSkeleton.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import { listAvailableScholarships } from '@/api/sas'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const loading = ref(true)
const keyword = ref('')
const scholarships = ref([])

const filteredScholarships = computed(() => {
  const query = keyword.value.trim().toLowerCase()
  if (!query) return scholarships.value
  return scholarships.value.filter((item) =>
    [item.title, item.category, item.sponsor, item.description, ...(item.tags ?? [])]
      .filter(Boolean)
      .some((field) => String(field).toLowerCase().includes(query)),
  )
})

function formatMoney(value) {
  return new Intl.NumberFormat('zh-TW', {
    style: 'currency',
    currency: 'TWD',
    maximumFractionDigits: 0,
  }).format(value)
}

function isUnavailable(item) {
  return item.status !== 'OPEN' || item.seatsLeft <= 0
}

onMounted(async () => {
  scholarships.value = await listAvailableScholarships(auth.user.id)
  loading.value = false
})
</script>

<template>
  <div class="page-grid">
    <BaseCard title="可申請獎學金" eyebrow="Scholarships">
      <div class="toolbar">
        <label class="search-field">
          <span>搜尋</span>
          <input v-model="keyword" type="search" placeholder="輸入名稱、分類、贊助單位" />
        </label>
      </div>
    </BaseCard>

    <LoadingSkeleton v-if="loading" :rows="4" />
    <EmptyState
      v-else-if="!filteredScholarships.length"
      title="目前沒有符合條件的獎學金"
      description="請調整搜尋條件，或稍後查看新的申請項目。"
      icon="scholarship"
    />

    <section v-else class="scholarship-grid">
      <BaseCard v-for="item in filteredScholarships" :key="item.id" class="scholarship-card">
        <div class="card-row card-row--between">
          <div>
            <p class="eyebrow">{{ item.category }} · {{ item.sponsor }}</p>
            <h2>{{ item.title }}</h2>
          </div>
          <StatusBadge :value="item.status" />
        </div>

        <p class="muted-text">{{ item.description }}</p>

        <div class="scholarship-card__facts">
          <span>{{ formatMoney(item.amount) }}</span>
          <span>剩餘 {{ item.seatsLeft }} / {{ item.quota }} 名</span>
          <span>截止 {{ item.deadline }}</span>
        </div>

        <div class="tag-list">
          <span v-for="tag in item.tags" :key="tag">{{ tag }}</span>
        </div>

        <dl class="criteria-list">
          <div>
            <dt>GPA 門檻</dt>
            <dd>{{ item.criteria.minGpa }}</dd>
          </div>
          <div>
            <dt>適用科系</dt>
            <dd>{{ item.criteria.departments.join('、') }}</dd>
          </div>
          <div>
            <dt>推薦信</dt>
            <dd>{{ item.requireRecommendation ? '需要' : '不需要' }}</dd>
          </div>
        </dl>

        <div class="card-actions">
          <RouterLink v-if="item.alreadyApplied" class="secondary-button" to="/applications">
            查看狀態
          </RouterLink>
          <button v-else-if="isUnavailable(item)" class="secondary-button" type="button" disabled>
            不可申請
          </button>
          <RouterLink v-else class="primary-button" :to="`/scholarships/${item.id}/apply`">
            開始申請
          </RouterLink>
        </div>
      </BaseCard>
    </section>
  </div>
</template>
