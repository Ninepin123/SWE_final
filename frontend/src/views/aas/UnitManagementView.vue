<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import BaseCard from '@/components/common/BaseCard.vue'
import BaseModal from '@/components/common/BaseModal.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import LoadingSkeleton from '@/components/common/LoadingSkeleton.vue'
import Icon from '@/components/common/Icon.vue'
import { createUnit, deleteUnit, listUnits, updateUnit, UNIT_TYPE_LABELS } from '@/api/aas'
import { useToastStore } from '@/stores/toast'

const toast = useToastStore()
const loading = ref(true)
const units = ref([])
const keyword = ref('')
const showModal = ref(false)
const editingId = ref(null)
const error = ref('')

const form = reactive({
  name: '',
  type: 'SCHOOL',
  contact_email: '',
})

const typeOptions = computed(() => Object.entries(UNIT_TYPE_LABELS))

const filteredUnits = computed(() => {
  const query = keyword.value.trim().toLowerCase()
  if (!query) return units.value
  return units.value.filter((unit) =>
    [unit.name, unit.contact_email, UNIT_TYPE_LABELS[unit.type]]
      .some((field) => String(field ?? '').toLowerCase().includes(query)),
  )
})

function resetForm() {
  Object.assign(form, { name: '', type: 'SCHOOL', contact_email: '' })
  editingId.value = null
  error.value = ''
}

function openCreate() {
  resetForm()
  showModal.value = true
}

function openEdit(unit) {
  Object.assign(form, {
    name: unit.name,
    type: unit.type,
    contact_email: unit.contact_email ?? '',
  })
  editingId.value = unit.unit_id
  error.value = ''
  showModal.value = true
}

function validate() {
  error.value = ''
  if (!form.name.trim()) {
    error.value = '單位名稱為必填。'
  } else if (form.contact_email && !form.contact_email.includes('@')) {
    error.value = 'Email 格式不正確。'
  }
  return !error.value
}

async function reload() {
  units.value = await listUnits()
}

async function save() {
  if (!validate()) return
  try {
    const payload = {
      name: form.name.trim(),
      type: form.type,
      contact_email: form.contact_email.trim() || null,
    }
    if (editingId.value) {
      await updateUnit(editingId.value, payload)
      toast.success('單位已更新')
    } else {
      await createUnit(payload)
      toast.success('單位已新增')
    }
    showModal.value = false
    await reload()
  } catch (saveError) {
    error.value = saveError.response?.data?.detail || saveError.message || '儲存失敗'
  }
}

async function remove(unit) {
  if (!window.confirm(`確定刪除單位「${unit.name}」？`)) return
  try {
    await deleteUnit(unit.unit_id)
    toast.success('單位已刪除')
    await reload()
  } catch (deleteError) {
    toast.error(deleteError.response?.data?.detail || deleteError.message || '刪除失敗')
  }
}

onMounted(async () => {
  try {
    await reload()
  } catch (loadError) {
    toast.error(loadError.response?.data?.detail || loadError.message || '單位資料載入失敗')
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="page-grid">
    <BaseCard title="單位管理" eyebrow="Admin">
      <template #actions>
        <button class="primary-button" type="button" @click="openCreate">新增單位</button>
      </template>

      <div class="toolbar">
        <label class="search-field">
          <span>搜尋</span>
          <input v-model="keyword" type="search" placeholder="單位名稱、Email" />
        </label>
      </div>
    </BaseCard>

    <LoadingSkeleton v-if="loading" :rows="5" />
    <EmptyState
      v-else-if="!filteredUnits.length"
      title="尚未建立任何單位"
      description="獎助單位與審查單位皆需先在此建立，帳號與獎學金才能綁定。"
      icon="building"
    />

    <BaseCard v-else>
      <div class="table-wrap">
        <table class="data-table">
          <thead>
            <tr>
              <th>單位</th>
              <th>類型</th>
              <th>聯絡 Email</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="unit in filteredUnits" :key="unit.unit_id">
              <td>
                <strong>{{ unit.name }}</strong>
                <span>#{{ unit.unit_id }}</span>
              </td>
              <td>{{ UNIT_TYPE_LABELS[unit.type] ?? unit.type }}</td>
              <td>{{ unit.contact_email || '—' }}</td>
              <td>
                <div class="table-actions">
                  <button class="ghost-button" type="button" @click="openEdit(unit)">
                    <Icon name="edit" /> 修改
                  </button>
                  <button class="ghost-button" type="button" @click="remove(unit)">
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
    :title="editingId ? '修改單位' : '新增單位'"
    @close="showModal = false"
  >
    <p v-if="error" class="form-error">{{ error }}</p>
    <div class="field-group">
      <p class="field-group__title">單位資訊</p>
      <div class="form-grid">
        <label class="form-grid__wide">
          <span>單位名稱</span>
          <input v-model="form.name" type="text" placeholder="例如：高雄大學學生事務處" />
        </label>
        <label>
          <span>類型</span>
          <select v-model="form.type">
            <option v-for="[value, label] in typeOptions" :key="value" :value="value">
              {{ label }}
            </option>
          </select>
        </label>
        <label>
          <span>聯絡 Email</span>
          <input v-model="form.contact_email" type="email" placeholder="例如：osa@nuk.edu.tw" />
        </label>
      </div>
    </div>

    <template #footer>
      <button class="secondary-button" type="button" @click="showModal = false">取消</button>
      <button class="primary-button" type="button" @click="save">儲存</button>
    </template>
  </BaseModal>
</template>
