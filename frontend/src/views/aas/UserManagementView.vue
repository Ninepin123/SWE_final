<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import BaseCard from '@/components/common/BaseCard.vue'
import BaseModal from '@/components/common/BaseModal.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import LoadingSkeleton from '@/components/common/LoadingSkeleton.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import Icon from '@/components/common/Icon.vue'
import { createUser, deleteUser, listUsers, ROLE_LABELS, updateUser } from '@/api/aas'
import { useMockApi } from '@/api/http'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'

const auth = useAuthStore()
const toast = useToastStore()
const loading = ref(true)
const users = ref([])
const keyword = ref('')
const roleFilter = ref('')
const statusFilter = ref('')
const showModal = ref(false)
const editingId = ref(null)
const error = ref('')

const form = reactive({
  account: '',
  password: '',
  name: '',
  email: '',
  role: 'STUDENT',
  unit_id: '',
  department: '',
  gpa: '',
  status: 'ACTIVE',
})

const roleOptions = computed(() =>
  Object.entries(ROLE_LABELS).filter(([role]) => useMockApi || role !== 'RECOMMENDER'),
)

const filteredUsers = computed(() => {
  const query = keyword.value.trim().toLowerCase()
  return users.value.filter((user) => {
    const matchedKeyword =
      !query ||
      [user.account, user.name, user.email, user.department, user.unit_id, user.unit].some((field) =>
        String(field ?? '').toLowerCase().includes(query),
      )
    const matchedRole = !roleFilter.value || user.role === roleFilter.value
    const matchedStatus = !statusFilter.value || user.status === statusFilter.value
    return matchedKeyword && matchedRole && matchedStatus
  })
})

function resetForm() {
  Object.assign(form, {
    account: '',
    password: '',
    name: '',
    email: '',
    role: 'STUDENT',
    unit_id: '',
    department: '',
    gpa: '',
    status: 'ACTIVE',
  })
  editingId.value = null
  error.value = ''
}

function openCreate() {
  resetForm()
  showModal.value = true
}

function openEdit(user) {
  Object.assign(form, {
    account: user.account,
    password: '',
    name: user.name,
    email: user.email ?? '',
    role: user.role,
    unit_id: user.unit_id ?? '',
    department: user.department ?? '',
    gpa: user.gpa ?? '',
    status: user.status,
  })
  editingId.value = user.user_id ?? user.id
  error.value = ''
  showModal.value = true
}

function validate() {
  error.value = ''
  if (!form.account || !form.name || !form.role) {
    error.value = '帳號、姓名與角色為必填。'
  } else if (form.email && !form.email.includes('@')) {
    error.value = 'Email 格式不正確。'
  } else if (!editingId.value && form.password.length < 8) {
    error.value = '新增帳號的初始密碼至少需要 8 個字元。'
  } else if (editingId.value && form.password && form.password.length < 8) {
    error.value = '新密碼至少需要 8 個字元。'
  }
  return !error.value
}

async function reload() {
  users.value = await listUsers()
}

async function save() {
  if (!validate()) return
  try {
    const payload = {
      name: form.name.trim(),
      email: form.email.trim() || null,
      role: form.role,
      unit_id: form.unit_id === '' ? null : Number(form.unit_id),
      department: form.department.trim() || null,
      gpa: form.gpa === '' ? null : Number(form.gpa),
    }
    if (editingId.value) {
      payload.status = form.status
      if (form.password) payload.password = form.password
      await updateUser(editingId.value, payload)
      toast.success('帳號已更新')
    } else {
      await createUser({
        ...payload,
        account: form.account.trim(),
        password: form.password,
      })
      toast.success('帳號已新增')
    }
    showModal.value = false
    await reload()
  } catch (saveError) {
    error.value = saveError.response?.data?.detail || saveError.message || '儲存失敗'
  }
}

async function remove(user) {
  const userId = user.user_id ?? user.id
  if (userId === (auth.user.user_id ?? auth.user.id)) {
    toast.error('不能刪除目前登入的管理員帳號')
    return
  }
  if (!window.confirm(`確定刪除 ${user.name}？`)) return
  try {
    await deleteUser(userId)
    toast.success('帳號已刪除')
    await reload()
  } catch (deleteError) {
    toast.error(deleteError.response?.data?.detail || deleteError.message || '刪除失敗')
  }
}

onMounted(async () => {
  try {
    await reload()
  } catch (loadError) {
    toast.error(loadError.response?.data?.detail || loadError.message || '帳號資料載入失敗')
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="page-grid">
    <BaseCard title="帳號管理" eyebrow="Admin">
      <template #actions>
        <button class="primary-button" type="button" @click="openCreate">新增帳號</button>
      </template>

      <div class="toolbar">
        <label class="search-field">
          <span>搜尋</span>
          <input v-model="keyword" type="search" placeholder="帳號、姓名、Email、單位" />
        </label>
        <label>
          <span>角色</span>
          <select v-model="roleFilter">
            <option value="">全部角色</option>
            <option v-for="[role, label] in roleOptions" :key="role" :value="role">
              {{ label }}
            </option>
          </select>
        </label>
        <label>
          <span>狀態</span>
          <select v-model="statusFilter">
            <option value="">全部狀態</option>
            <option value="ACTIVE">啟用</option>
            <option value="DISABLED">停用</option>
          </select>
        </label>
      </div>
    </BaseCard>

    <LoadingSkeleton v-if="loading" :rows="5" />
    <EmptyState
      v-else-if="!filteredUsers.length"
      title="沒有符合條件的帳號"
      description="請調整搜尋條件或新增帳號。"
      icon="admin"
    />

    <BaseCard v-else>
      <div class="table-wrap">
        <table class="data-table">
          <thead>
            <tr>
              <th>帳號</th>
              <th>姓名</th>
              <th>角色</th>
              <th>單位</th>
              <th>狀態</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="user in filteredUsers" :key="user.user_id ?? user.id">
              <td>
                <strong>{{ user.account }}</strong>
                <span>{{ user.email }}</span>
              </td>
              <td>{{ user.name }}</td>
              <td>{{ ROLE_LABELS[user.role] }}</td>
              <td>
                {{ user.department || user.unit || (user.unit_id ? `單位 #${user.unit_id}` : '—') }}
              </td>
              <td><StatusBadge :value="user.status" /></td>
              <td>
                <div class="table-actions">
                  <button class="ghost-button" type="button" @click="openEdit(user)">
                    <Icon name="edit" /> 修改
                  </button>
                  <button class="ghost-button" type="button" @click="remove(user)">
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
    :title="editingId ? '修改帳號' : '新增帳號'"
    @close="showModal = false"
  >
    <p v-if="error" class="form-error">{{ error }}</p>
    <div class="field-group">
      <p class="field-group__title">帳號資訊</p>
      <div class="form-grid">
        <label>
          <span>帳號</span>
          <input v-model="form.account" :disabled="!!editingId" type="text" />
        </label>
        <label>
          <span>{{ editingId ? '新密碼（留空不修改）' : '初始密碼' }}</span>
          <input v-model="form.password" type="password" autocomplete="new-password" />
        </label>
        <label>
          <span>姓名</span>
          <input v-model="form.name" type="text" />
        </label>
        <label>
          <span>Email</span>
          <input v-model="form.email" type="email" />
        </label>
        <label>
          <span>角色</span>
          <select v-model="form.role">
            <option v-for="[role, label] in roleOptions" :key="role" :value="role">
              {{ label }}
            </option>
          </select>
        </label>
      </div>
    </div>

    <div class="field-group">
      <p class="field-group__title">單位與狀態</p>
      <div class="form-grid">
        <label>
          <span>單位 ID</span>
          <input v-model="form.unit_id" min="1" type="number" />
        </label>
        <label>
          <span>科系／部門</span>
          <input v-model="form.department" type="text" />
        </label>
        <label>
          <span>GPA（學生）</span>
          <input v-model="form.gpa" max="4.3" min="0" step="0.01" type="number" />
        </label>
        <label>
          <span>狀態</span>
          <select v-model="form.status">
            <option value="ACTIVE">啟用</option>
            <option value="DISABLED">停用</option>
          </select>
        </label>
      </div>
    </div>

    <template #footer>
      <button class="secondary-button" type="button" @click="showModal = false">取消</button>
      <button class="primary-button" type="button" @click="save">儲存</button>
    </template>
  </BaseModal>
</template>
