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
  getOptions,
} from '@/api/sms'
import { listDepartments, listUnits, UNIT_TYPE_LABELS } from '@/api/aas'
import { useToastStore } from '@/stores/toast'
import { useAuthStore } from '@/stores/auth'

const toast = useToastStore()
const auth = useAuthStore()
const loading = ref(true)
const scholarships = ref([])
const keyword = ref('')
const showModal = ref(false)
const editingId = ref(null)
const optionsList = ref([])
const units = ref([])
const departmentList = ref([])

const UNLIMITED_DEPARTMENTS = ['不限', '不限科系', 'ALL']

// 適用科系只列出學術科系（category=ACADEMIC）；行政部門（如教務處）不得作為獎學金的適用科系。
// 下拉清單以目前科系列表為主；若獎學金已存有不在清單中的舊科系名稱，
// 仍補進選項保持勾選，避免儲存時被誤刪（但行政部門名稱不補回）。
const departmentOptions = computed(() => {
  const academic = departmentList.value.filter((dept) => dept.category === 'ACADEMIC')
  const adminNames = new Set(
    departmentList.value.filter((dept) => dept.category !== 'ACADEMIC').map((dept) => dept.name),
  )
  const known = academic.map((dept) => dept.name)
  const extras = form.departments
    .filter((name) => !known.includes(name) && !adminNames.has(name))
    .map((name) => ({ department_id: `extra-${name}`, name, college: null }))
  return [...academic, ...extras]
})

function toggleNoDepartmentLimit() {
  form.departments = []
}

const categories = computed(() => optionsList.value.filter(o => o.type === 'CATEGORY'))
const tagOptions = computed(() => optionsList.value.filter(o => o.type === 'TAG'))

// 管理員可指定任一單位；獎助單位人員只能選自己所屬的單位。
const selectableUnits = computed(() => {
  if (auth.user?.role === 'ADMIN') return units.value
  return units.value.filter((unit) => unit.unit_id === auth.user?.unit_id)
})

const form = reactive({
  title: '',
  category: '',
  unitId: '',
  amount: 0,
  quota: 0,
  usedQuota: 0,
  startDate: '',
  deadline: '',
  status: 'OPEN',
  description: '',
  minGpa: 0,
  departments: [],
  gradesText: '',
  identitiesText: '',
  familyStatusesText: '',
  criteriaNote: '',
  tagsText: '',
  docsText: '',
  requireRecommendation: true,
  contactName: '',
  contactPhone: '',
  contactEmail: '',
  contactAddress: '',
  website: '',
})

const filteredScholarships = computed(() => {
  // 單位資料隔離（NUKSAMS010/041）：獎助單位人員只管理自己單位張貼的獎學金；管理員不限。
  let base = scholarships.value
  if (auth.user?.role !== 'ADMIN') {
    base = base.filter((item) => item.unitId === auth.user?.unit_id)
  }
  const query = keyword.value.trim().toLowerCase()
  if (!query) return base
  return base.filter((item) =>
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
    unitId: auth.user?.role === 'ADMIN' ? '' : (auth.user?.unit_id ?? ''),
    amount: 0,
    quota: 0,
    usedQuota: 0,
    startDate: '',
    deadline: '',
    status: 'OPEN',
    description: '',
    minGpa: 0,
    departments: [],
    gradesText: '',
    identitiesText: '',
    familyStatusesText: '',
    criteriaNote: '',
    tagsText: '',
    docsText: '',
    requireRecommendation: true,
    contactName: '',
    contactPhone: '',
    contactEmail: '',
    contactAddress: '',
    website: '',
  })
  editingId.value = null
}

function openCreate() {
  resetForm()
  showModal.value = true
}

function openEdit(item) {
  Object.assign(form, {
    title: item.title,
    category: item.category,
    unitId: item.unitId ?? '',
    amount: item.amount,
    quota: item.quota,
    usedQuota: item.usedQuota,
    startDate: item.startDate || '',
    deadline: item.deadline || '',
    status: item.status,
    description: item.description,
    minGpa: item.criteria?.minGpa ?? 0,
    departments: (item.criteria?.departments ?? []).filter(
      (name) => name && !UNLIMITED_DEPARTMENTS.includes(name),
    ),
    gradesText: item.criteria?.grades?.join('、') ?? '',
    identitiesText: item.criteria?.identities?.join('、') ?? '',
    familyStatusesText: item.criteria?.familyStatuses?.join('、') ?? '',
    criteriaNote: item.criteria?.note ?? '',
    tagsText: item.tags?.join('、') ?? '',
    docsText: item.requiredDocs?.join('、') ?? '',
    requireRecommendation: item.requireRecommendation,
    contactName: item.contactName ?? '',
    contactPhone: item.contactPhone ?? '',
    contactEmail: item.contactEmail ?? '',
    contactAddress: item.contactAddress ?? '',
    website: item.website ?? '',
  })
  editingId.value = item.id
  showModal.value = true
}

function validate() {
  let message = ''
  if (!form.title || !form.category || form.unitId === '' || !form.deadline) {
    message = '名稱、分類、提供單位與截止日為必填。'
  } else if (Number(form.amount) < 0 || Number(form.quota) <= 0) {
    message = '金額需大於等於 0，名額需大於 0。'
  } else if (form.startDate && form.deadline && new Date(form.startDate) >= new Date(form.deadline)) {
    message = '開始日必須早於截止日。'
  } else if (form.contactEmail && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.contactEmail)) {
    message = 'Email 格式不正確。'
  }
  if (message) {
    toast.warning(message)
    return false
  }
  return true
}

function payload() {
  return {
    title: form.title,
    category: form.category,
    unitId: form.unitId === '' ? null : Number(form.unitId),
    amount: Number(form.amount),
    quota: Number(form.quota),
    usedQuota: Number(form.usedQuota || 0),
    startDate: form.startDate || null,
    deadline: form.deadline,
    status: form.status,
    description: form.description,
    criteria: {
      minGpa: Number(form.minGpa || 0),
      departments: [...form.departments],
      grades: toArray(form.gradesText),
      identities: toArray(form.identitiesText),
      familyStatuses: toArray(form.familyStatusesText),
      note: form.criteriaNote,
    },
    tags: toArray(form.tagsText),
    requiredDocs: toArray(form.docsText),
    requireRecommendation: form.requireRecommendation,
    contactName: form.contactName,
    contactPhone: form.contactPhone,
    contactEmail: form.contactEmail,
    contactAddress: form.contactAddress,
    website: form.website,
  }
}

async function reload() {
  scholarships.value = await listScholarships()
  try {
    const [opts, unitList, deptList] = await Promise.all([
      getOptions(),
      listUnits(),
      listDepartments(),
    ])
    optionsList.value = opts
    units.value = unitList
    departmentList.value = deptList
  } catch (err) {
    console.error('Failed to fetch options/units/departments', err)
  }
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
    toast.error(saveError.message || '儲存失敗')
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
    <div class="field-group">
      <p class="field-group__title">基本資料</p>
      <div class="form-grid">
        <label class="form-grid__wide">
          <span>名稱</span>
          <input v-model="form.title" type="text" />
        </label>
        <label>
          <span>分類</span>
          <input v-model="form.category" type="text" list="category-suggestions" placeholder="選擇或輸入新分類" />
          <datalist id="category-suggestions">
            <option v-for="cat in categories" :key="cat.id" :value="cat.name"></option>
          </datalist>
        </label>
        <label>
          <span>提供單位</span>
          <select v-model="form.unitId">
            <option disabled value="">請選擇單位</option>
            <option v-for="unit in selectableUnits" :key="unit.unit_id" :value="unit.unit_id">
              {{ unit.name }}（{{ UNIT_TYPE_LABELS[unit.type] ?? unit.type }}）
            </option>
          </select>
        </label>
        <label class="form-grid__wide">
          <span>說明</span>
          <textarea v-model="form.description" rows="3" />
        </label>
      </div>
    </div>

    <div class="field-group">
      <p class="field-group__title">聯絡資訊</p>
      <div class="form-grid">
        <label>
          <span>聯絡人</span>
          <input v-model="form.contactName" type="text" placeholder="例如：王小明" />
        </label>
        <label>
          <span>聯絡電話</span>
          <input v-model="form.contactPhone" type="tel" placeholder="例如：02-12345678" />
        </label>
        <label class="form-grid__wide">
          <span>Email</span>
          <input v-model="form.contactEmail" type="email" placeholder="例如：example@domain.com" />
        </label>
        <label class="form-grid__wide">
          <span>通訊地址</span>
          <input v-model="form.contactAddress" type="text" placeholder="聯絡地址" />
        </label>
        <label class="form-grid__wide">
          <span>網站連結</span>
          <input v-model="form.website" type="url" placeholder="https://" />
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
          <input v-model="form.usedQuota" type="number" disabled />
        </label>
        <label>
          <span>開始日</span>
          <input v-model="form.startDate" type="date" />
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
        <div class="form-grid__wide dept-field">
          <span class="dept-field__label">適用科系</span>
          <label class="dept-all">
            <input
              type="checkbox"
              :checked="form.departments.length === 0"
              @change="toggleNoDepartmentLimit"
            />
            <span>不限科系（所有科系皆可申請）</span>
          </label>
          <div v-if="departmentOptions.length" class="dept-picker">
            <label
              v-for="dept in departmentOptions"
              :key="dept.department_id"
              class="dept-option"
            >
              <input type="checkbox" :value="dept.name" v-model="form.departments" />
              <span>
                {{ dept.name }}
                <small v-if="dept.college">（{{ dept.college }}）</small>
              </span>
            </label>
          </div>
          <p v-else class="dept-empty">
            尚未建立任何科系，請先到「科系與部門管理」新增；未選擇即代表不限科系。
          </p>
          <p v-if="form.departments.length" class="dept-summary">
            已選 {{ form.departments.length }} 個科系：{{ form.departments.join('、') }}
          </p>
        </div>
        <label>
          <span>適用年級</span>
          <input v-model="form.gradesText" type="text" placeholder="例如：二年級、三年級" />
        </label>
        <label>
          <span>身分別限制</span>
          <input v-model="form.identitiesText" type="text" placeholder="例如：原住民、身心障礙" />
        </label>
        <label class="form-grid__wide">
          <span>家庭狀況限制</span>
          <input v-model="form.familyStatusesText" type="text" placeholder="例如：低收入戶、中低收入戶" />
        </label>
        <label class="form-grid__wide">
          <span>申請條件備註</span>
          <input v-model="form.criteriaNote" type="text" />
        </label>
        <label class="form-grid__wide">
          <span>標籤</span>
          <input v-model="form.tagsText" type="text" list="tag-suggestions" placeholder="成績優良、校內" />
          <datalist id="tag-suggestions">
            <option v-for="tag in tagOptions" :key="tag.id" :value="tag.name"></option>
          </datalist>
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

<style scoped>
.dept-field {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.dept-field__label {
  font-size: 0.85rem;
  color: var(--ink-soft, #6b6256);
}

.dept-all {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 600;
}

.dept-all input,
.dept-option input {
  width: auto;
  margin: 0;
}

.dept-picker {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 0.35rem 0.75rem;
  max-height: 220px;
  overflow-y: auto;
  padding: 0.65rem 0.75rem;
  border: 1px solid var(--line, #ddd5c7);
  border-radius: 8px;
  background: var(--paper, #fbf8f1);
}

.dept-option {
  display: flex;
  align-items: center;
  gap: 0.45rem;
  font-weight: 400;
  cursor: pointer;
}

.dept-option small {
  color: var(--ink-soft, #8a8170);
}

.dept-empty {
  margin: 0;
  font-size: 0.85rem;
  color: var(--ink-soft, #8a8170);
}

.dept-summary {
  margin: 0;
  font-size: 0.82rem;
  color: var(--jade, #2f6b52);
}
</style>
