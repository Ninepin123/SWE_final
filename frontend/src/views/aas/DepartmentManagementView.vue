<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import BaseCard from '@/components/common/BaseCard.vue'
import BaseModal from '@/components/common/BaseModal.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import LoadingSkeleton from '@/components/common/LoadingSkeleton.vue'
import Icon from '@/components/common/Icon.vue'
import {
  createDepartment,
  deleteDepartment,
  listDepartments,
  updateDepartment,
  DEPARTMENT_CATEGORY_LABELS,
} from '@/api/aas'
import { useToastStore } from '@/stores/toast'

const toast = useToastStore()
const loading = ref(true)
const departments = ref([])
const keyword = ref('')
const showModal = ref(false)
const editingId = ref(null)
const error = ref('')

const form = reactive({
  name: '',
  college: '',
  category: 'ACADEMIC',
})

const categoryOptions = computed(() => Object.entries(DEPARTMENT_CATEGORY_LABELS))

const filteredDepartments = computed(() => {
  const query = keyword.value.trim().toLowerCase()
  if (!query) return departments.value
  return departments.value.filter((dept) =>
    [dept.name, dept.college, DEPARTMENT_CATEGORY_LABELS[dept.category]]
      .some((field) => String(field ?? '').toLowerCase().includes(query)),
  )
})

function resetForm() {
  Object.assign(form, { name: '', college: '', category: 'ACADEMIC' })
  editingId.value = null
  error.value = ''
}

function openCreate() {
  resetForm()
  showModal.value = true
}

function openEdit(dept) {
  Object.assign(form, {
    name: dept.name,
    college: dept.college ?? '',
    category: dept.category,
  })
  editingId.value = dept.department_id
  error.value = ''
  showModal.value = true
}

function validate() {
  error.value = ''
  if (!form.name.trim()) {
    error.value = '科系／部門名稱為必填。'
  }
  return !error.value
}

async function reload() {
  departments.value = await listDepartments()
}

async function save() {
  if (!validate()) return
  try {
    const payload = {
      name: form.name.trim(),
      college: form.college.trim() || null,
      category: form.category,
    }
    if (editingId.value) {
      await updateDepartment(editingId.value, payload)
      toast.success('科系／部門已更新')
    } else {
      await createDepartment(payload)
      toast.success('科系／部門已新增')
    }
    showModal.value = false
    await reload()
  } catch (saveError) {
    error.value = saveError.response?.data?.detail || saveError.message || '儲存失敗'
  }
}

async function remove(dept) {
  if (!window.confirm(`確定刪除「${dept.name}」？`)) return
  try {
    await deleteDepartment(dept.department_id)
    toast.success('科系／部門已刪除')
    await reload()
  } catch (deleteError) {
    toast.error(deleteError.response?.data?.detail || deleteError.message || '刪除失敗')
  }
}

onMounted(async () => {
  try {
    await reload()
  } catch (loadError) {
    toast.error(loadError.response?.data?.detail || loadError.message || '科系資料載入失敗')
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="page-grid">
    <BaseCard title="科系與部門管理" eyebrow="Admin">
      <template #actions>
        <button class="primary-button" type="button" @click="openCreate">新增科系／部門</button>
      </template>

      <div class="toolbar">
        <label class="search-field">
          <span>搜尋</span>
          <input v-model="keyword" type="search" placeholder="名稱、所屬學院" />
        </label>
      </div>
    </BaseCard>

    <LoadingSkeleton v-if="loading" :rows="5" />
    <EmptyState
      v-else-if="!filteredDepartments.length"
      title="尚未建立任何科系或部門"
      description="先在此建立科系與行政部門，帳號的科系欄位與獎學金的科系資格才能對應一致。"
      icon="graduation"
    />

    <BaseCard v-else>
      <div class="table-wrap">
        <table class="data-table">
          <thead>
            <tr>
              <th>名稱</th>
              <th>類別</th>
              <th>所屬學院</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="dept in filteredDepartments" :key="dept.department_id">
              <td>
                <strong>{{ dept.name }}</strong>
                <span>#{{ dept.department_id }}</span>
              </td>
              <td>{{ DEPARTMENT_CATEGORY_LABELS[dept.category] ?? dept.category }}</td>
              <td>{{ dept.college || '—' }}</td>
              <td>
                <div class="table-actions">
                  <button class="ghost-button" type="button" @click="openEdit(dept)">
                    <Icon name="edit" /> 修改
                  </button>
                  <button class="ghost-button" type="button" @click="remove(dept)">
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
    :title="editingId ? '修改科系／部門' : '新增科系／部門'"
    @close="showModal = false"
  >
    <p v-if="error" class="form-error">{{ error }}</p>
    <div class="field-group">
      <p class="field-group__title">科系／部門資訊</p>
      <div class="form-grid">
        <label class="form-grid__wide">
          <span>名稱</span>
          <input v-model="form.name" type="text" placeholder="例如：資訊工程學系" />
        </label>
        <label>
          <span>類別</span>
          <select v-model="form.category">
            <option v-for="[value, label] in categoryOptions" :key="value" :value="value">
              {{ label }}
            </option>
          </select>
        </label>
        <label>
          <span>所屬學院</span>
          <input v-model="form.college" type="text" placeholder="例如：資訊學院（部門可留空）" />
        </label>
      </div>
    </div>

    <template #footer>
      <button class="secondary-button" type="button" @click="showModal = false">取消</button>
      <button class="primary-button" type="button" @click="save">儲存</button>
    </template>
  </BaseModal>
</template>
