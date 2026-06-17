<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import BaseCard from '@/components/common/BaseCard.vue'
import BaseModal from '@/components/common/BaseModal.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import LoadingSkeleton from '@/components/common/LoadingSkeleton.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import Icon from '@/components/common/Icon.vue'
import {
  createScholarship,
  deleteScholarship,
  listScholarships,
  updateScholarship,
} from '@/api/sms'
import { useToastStore } from '@/stores/toast'

const toast = useToastStore()
const loading = ref(true)
const scholarships = ref([])
const keyword = ref('')
const showModal = ref(false)
const editingId = ref(null)
const error = ref('')

const form = reactive({
  title: '',
  category: '',
  sponsor: '',
  amount: 0,
  quota: 0,
  usedQuota: 0,
  deadline: '',
  status: 'OPEN',
  description: '',
  minGpa: 0,
  departmentsText: '不限科系',
  criteriaNote: '',
  tagsText: '',
  docsText: '',
  requireRecommendation: true,
})

const filteredScholarships = computed(() => {
  const query = keyword.value.trim().toLowerCase()
  if (!query) return scholarships.value
  return scholarships.value.filter((item) =>
    [item.title, item.category, item.sponsor, item.description]
      .filter(Boolean)
      .some((field) => field.toLowerCase().includes(query)),
  )
})

function toArray(text) {
  return String(text || '')
    .split(/[,\n、]/)
    .map((item) => item.trim())
    .filter(Boolean)
}

function resetForm() {
  Object.assign(form, {
    title: '',
    category: '',
    sponsor: '',
    amount: 0,
    quota: 0,
    usedQuota: 0,
    deadline: '',
    status: 'OPEN',
    description: '',
    minGpa: 0,
    departmentsText: '不限科系',
    criteriaNote: '',
    tagsText: '',
    docsText: '',
    requireRecommendation: true,
  })
  editingId.value = null
  error.value = ''
}

function openCreate() {
  resetForm()
  showModal.value = true
}

function openEdit(item) {
  Object.assign(form, {
    title: item.title,
    category: item.category,
    sponsor: item.sponsor,
    amount: item.amount,
    quota: item.quota,
    usedQuota: item.usedQuota,
    deadline: item.deadline,
    status: item.status,
    description: item.description,
    minGpa: item.criteria?.minGpa ?? 0,
    departmentsText: item.criteria?.departments?.join('、') ?? '',
    criteriaNote: item.criteria?.note ?? '',
    tagsText: item.tags?.join('、') ?? '',
    docsText: item.requiredDocs?.join('、') ?? '',
    requireRecommendation: item.requireRecommendation,
  })
  editingId.value = item.id
  error.value = ''
  showModal.value = true
}

function validate() {
  error.value = ''
  if (!form.title || !form.category || !form.sponsor || !form.deadline) {
    error.value = '名稱、分類、贊助單位與截止日為必填。'
  } else if (Number(form.amount) <= 0 || Number(form.quota) <= 0) {
    error.value = '金額與名額需大於 0。'
  }
  return !error.value
}

function payload() {
  return {
    title: form.title,
    category: form.category,
    sponsor: form.sponsor,
    amount: Number(form.amount),
    quota: Number(form.quota),
    usedQuota: Number(form.usedQuota || 0),
    deadline: form.deadline,
    status: form.status,
    description: form.description,
    criteria: {
      minGpa: Number(form.minGpa || 0),
      departments: toArray(form.departmentsText),
      note: form.criteriaNote,
    },
    tags: toArray(form.tagsText),
    requiredDocs: toArray(form.docsText),
    requireRecommendation: form.requireRecommendation,
  }
}

async function reload() {
  scholarships.value = await listScholarships()
}

async function save() {
  if (!validate()) return
  try {
    if (editingId.value) {
      await updateScholarship(editingId.value, payload())
      toast.success('獎學金已更新')
    } else {
      await createScholarship(payload())
      toast.success('獎學金已新增')
    }
    showModal.value = false
    await reload()
  } catch (saveError) {
    error.value = saveError.message || '儲存失敗'
  }
}

async function remove(item) {
  if (!window.confirm(`確定刪除 ${item.title}？`)) return
  try {
    await deleteScholarship(item.id)
    toast.success('獎學金已刪除')
    await reload()
  } catch (deleteError) {
    toast.error(deleteError.message || '刪除失敗')
  }
}

function formatMoney(value) {
  return new Intl.NumberFormat('zh-TW', {
    style: 'currency',
    currency: 'TWD',
    maximumFractionDigits: 0,
  }).format(value)
}

onMounted(async () => {
  await reload()
  loading.value = false
})
</script>

<template>
  <div class="page-grid">
    <BaseCard title="獎學金管理" eyebrow="Admin">
      <template #actions>
        <button class="primary-button" type="button" @click="openCreate">新增獎學金</button>
      </template>
      <div class="toolbar">
        <label class="search-field">
          <span>搜尋</span>
          <input v-model="keyword" type="search" placeholder="名稱、分類、贊助單位" />
        </label>
      </div>
    </BaseCard>

    <LoadingSkeleton v-if="loading" :rows="5" />
    <EmptyState
      v-else-if="!filteredScholarships.length"
      title="沒有符合條件的獎學金"
      description="請調整搜尋條件或新增獎學金。"
      icon="manage"
    />

    <BaseCard v-else>
      <div class="table-wrap">
        <table class="data-table">
          <thead>
            <tr>
              <th>獎學金</th>
              <th>金額</th>
              <th>名額</th>
              <th>截止日</th>
              <th>狀態</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in filteredScholarships" :key="item.id">
              <td>
                <strong>{{ item.title }}</strong>
                <span>{{ item.category }} · {{ item.sponsor }}</span>
              </td>
              <td>{{ formatMoney(item.amount) }}</td>
              <td>{{ item.usedQuota }} / {{ item.quota }}</td>
              <td>{{ item.deadline }}</td>
              <td><StatusBadge :value="item.status" /></td>
              <td>
                <div class="table-actions">
                  <button class="ghost-button" type="button" @click="openEdit(item)">
                    <Icon name="edit" /> 修改
                  </button>
                  <button class="ghost-button" type="button" @click="remove(item)">
                    <Icon name="trash" /> 刪除
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </BaseCard>
  </div>

  <BaseModal
    :show="showModal"
    :title="editingId ? '修改獎學金' : '新增獎學金'"
    width="880px"
    @close="showModal = false"
  >
    <p v-if="error" class="form-error">{{ error }}</p>

    <div class="field-group">
      <p class="field-group__title">基本資料</p>
      <div class="form-grid">
        <label class="form-grid__wide">
          <span>名稱</span>
          <input v-model="form.title" type="text" />
        </label>
        <label>
          <span>分類</span>
          <input v-model="form.category" type="text" />
        </label>
        <label>
          <span>贊助單位</span>
          <input v-model="form.sponsor" type="text" />
        </label>
        <label class="form-grid__wide">
          <span>說明</span>
          <textarea v-model="form.description" rows="3" />
        </label>
      </div>
    </div>

    <div class="field-group">
      <p class="field-group__title">金額與名額</p>
      <div class="form-grid">
        <label>
          <span>金額</span>
          <input v-model="form.amount" min="0" type="number" />
        </label>
        <label>
          <span>總名額</span>
          <input v-model="form.quota" min="0" type="number" />
        </label>
        <label>
          <span>已使用名額</span>
          <input v-model="form.usedQuota" min="0" type="number" />
        </label>
        <label>
          <span>截止日</span>
          <input v-model="form.deadline" type="date" />
        </label>
        <label>
          <span>狀態</span>
          <select v-model="form.status">
            <option value="OPEN">開放申請</option>
            <option value="CLOSED">已截止</option>
            <option value="DRAFT">草稿</option>
          </select>
        </label>
      </div>
    </div>

    <div class="field-group">
      <p class="field-group__title">申請條件</p>
      <div class="form-grid">
        <label>
          <span>GPA 門檻</span>
          <input v-model="form.minGpa" min="0" max="4.3" step="0.01" type="number" />
        </label>
        <label>
          <span>需要推薦信</span>
          <select v-model="form.requireRecommendation">
            <option :value="true">需要</option>
            <option :value="false">不需要</option>
          </select>
        </label>
        <label class="form-grid__wide">
          <span>適用科系</span>
          <input v-model="form.departmentsText" type="text" placeholder="可用頓號或換行分隔" />
        </label>
        <label class="form-grid__wide">
          <span>申請條件備註</span>
          <input v-model="form.criteriaNote" type="text" />
        </label>
        <label class="form-grid__wide">
          <span>標籤</span>
          <input v-model="form.tagsText" type="text" placeholder="成績優良、校內" />
        </label>
        <label class="form-grid__wide">
          <span>必要文件</span>
          <input v-model="form.docsText" type="text" placeholder="成績單、自傳與讀書計畫" />
        </label>
      </div>
    </div>

    <template #footer>
      <button class="secondary-button" type="button" @click="showModal = false">取消</button>
      <button class="primary-button" type="button" @click="save">儲存</button>
    </template>
  </BaseModal>
</template>
