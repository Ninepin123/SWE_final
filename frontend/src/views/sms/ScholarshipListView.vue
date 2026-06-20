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
const categoryFilter = ref('')
const eligibilityFilter = ref('')
const scholarships = ref([])

const filteredScholarships = computed(() => {
  const query = keyword.value.trim().toLowerCase()
  return scholarships.value.filter((item) =>
    (!query ||
      [item.title, item.category, item.sponsor, item.description]
        .filter(Boolean)
        .some((field) => String(field).toLowerCase().includes(query))) &&
    (!categoryFilter.value || item.category === categoryFilter.value) &&
    (!eligibilityFilter.value ||
      (eligibilityFilter.value === 'ELIGIBLE' ? item.canApply : !item.canApply)),
  )
})

const categoryLabels = {
  SCHOOL: '校內',
  GOVERNMENT: '政府',
  PRIVATE: '民間',
  LOW_INCOME: '清寒',
  MERIT: '成績優良',
  OTHER: '其他',
}

function formatMoney(value) {
  return new Intl.NumberFormat('zh-TW', {
    style: 'currency',
    currency: 'TWD',
    maximumFractionDigits: 0,
  }).format(value)
}

function isUnavailable(item) {
  return item.canApply === false || item.status !== 'OPEN' || item.seatsLeft <= 0
}

function formatDate(value) {
  if (!value) return '未設定'
  return new Intl.DateTimeFormat('zh-TW', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  }).format(new Date(value))
}

onMounted(async () => {
  scholarships.value = await listAvailableScholarships(auth.user?.user_id ?? auth.user?.id)
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
        <label>
          <span>分類</span>
          <select v-model="categoryFilter">
            <option value="">全部分類</option>
            <option v-for="(label, value) in categoryLabels" :key="value" :value="value">
              {{ label }}
            </option>
          </select>
        </label>
        <label>
          <span>資格</span>
          <select v-model="eligibilityFilter">
            <option value="">全部</option>
            <option value="ELIGIBLE">符合資格</option>
            <option value="INELIGIBLE">不符合資格</option>
          </select>
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
            <p class="eyebrow">{{ categoryLabels[item.category] || item.category }} · {{ item.sponsor }}</p>
            <h2>{{ item.title }}</h2>
          </div>
          <StatusBadge :value="item.status" />
        </div>

        <p class="muted-text">{{ item.description }}</p>

        <div class="scholarship-card__facts">
          <span>{{ formatMoney(item.amount) }}</span>
          <span>剩餘 {{ item.seatsLeft }} / {{ item.quota }} 名</span>
          <span v-if="item.startDate">{{ formatDate(item.startDate) }} ~ {{ formatDate(item.deadline) }}</span>
          <span v-else>截止 {{ formatDate(item.deadline) }}</span>
        </div>

        <div v-if="item.ineligibilityReasons?.length" class="tag-list">
          <span v-for="reason in item.ineligibilityReasons" :key="reason">{{ reason }}</span>
        </div>

        <dl class="criteria-list">
          <div>
            <dt>GPA 門檻</dt>
            <dd>{{ item.minGpa ?? '不限' }}</dd>
          </div>
          <div v-if="item.criteria.departments?.length && item.criteria.departments[0] !== '不限科系'">
            <dt>適用科系</dt>
            <dd>{{ item.departmentLimit || '不限科系' }}</dd>
          </div>
          <div v-if="item.criteria.grades?.length">
            <dt>適用年級</dt>
            <dd>{{ item.criteria.grades.join('、') }}</dd>
          </div>
          <div v-if="item.criteria.identities?.length">
            <dt>身分別限制</dt>
            <dd>{{ item.criteria.identities.join('、') }}</dd>
          </div>
          <div v-if="item.criteria.familyStatuses?.length">
            <dt>家庭狀況限制</dt>
            <dd>{{ item.criteria.familyStatuses.join('、') }}</dd>
          </div>
          <div>
            <dt>聯絡資訊</dt>
            <dd>{{ item.contactEmail || '請洽提供單位' }}</dd>
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
