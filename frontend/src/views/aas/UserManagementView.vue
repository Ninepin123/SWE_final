<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import BaseCard from '@/components/common/BaseCard.vue'
import BaseModal from '@/components/common/BaseModal.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import LoadingSkeleton from '@/components/common/LoadingSkeleton.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import Icon from '@/components/common/Icon.vue'
import { createUser, deleteUser, listUsers, updateUser } from '@/api/aas'
import { ROLE_LABELS } from '@/api/aas'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'

const auth = useAuthStore()
const toast = useToastStore()
const loading = ref(true)
const users = ref([])
const keyword = ref('')
const roleFilter = ref('')
const showModal = ref(false)
const editingId = ref(null)
const error = ref('')

const form = reactive({
  account: '',
  name: '',
  email: '',
  role: 'STUDENT',
  unit: '',
  phone: '',
  status: 'ACTIVE',
})

const filteredUsers = computed(() => {
  const query = keyword.value.trim().toLowerCase()
  return users.value.filter((user) => {
    const matchedKeyword =
      !query ||
      [user.account, user.name, user.email, user.unit].some((field) =>
        String(field ?? '').toLowerCase().includes(query),
      )
    const matchedRole = !roleFilter.value || user.role === roleFilter.value
    return matchedKeyword && matchedRole
  })
})

function resetForm() {
  Object.assign(form, {
    account: '',
    name: '',
    email: '',
    role: 'STUDENT',
    unit: '',
    phone: '',
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
  Object.assign(form, user)
  editingId.value = user.id
  error.value = ''
  showModal.value = true
}

function validate() {
  error.value = ''
  if (!form.account || !form.name || !form.email || !form.role) {
    error.value = '帳號、姓名、Email 與角色為必填。'
  } else if (!form.email.includes('@')) {
    error.value = 'Email 格式不正確。'
  }
  return !error.value
}

async function reload() {
  users.value = await listUsers()
}

async function save() {
  if (!validate()) return
  try {
    if (editingId.value) {
      await updateUser(editingId.value, { ...form })
      toast.success('帳號已更新')
    } else {
      await createUser({ ...form })
      toast.success('帳號已新增')
    }
    showModal.value = false
    await reload()
  } catch (saveError) {
    error.value = saveError.message || '儲存失敗'
  }
}

async function remove(user) {
  if (user.id === auth.user.id) {
    toast.error('不能刪除目前登入的管理員帳號')
    return
  }
  if (!window.confirm(`確定刪除 ${user.name}？`)) return
  await deleteUser(user.id)
  toast.success('帳號已刪除')
  await reload()
}

onMounted(async () => {
  await reload()
  loading.value = false
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
            <option v-for="(label, role) in ROLE_LABELS" :key="role" :value="role">
              {{ label }}
            </option>
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
            <tr v-for="user in filteredUsers" :key="user.id">
              <td>
                <strong>{{ user.account }}</strong>
                <span>{{ user.email }}</span>
              </td>
              <td>{{ user.name }}</td>
              <td>{{ ROLE_LABELS[user.role] }}</td>
              <td>{{ user.unit }}</td>
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
          <input v-model="form.account" type="text" />
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
            <option v-for="(label, role) in ROLE_LABELS" :key="role" :value="role">
              {{ label }}
            </option>
          </select>
        </label>
      </div>
    </div>

    <div class="field-group">
      <p class="field-group__title">聯絡與狀態</p>
      <div class="form-grid">
        <label>
          <span>單位</span>
          <input v-model="form.unit" type="text" />
        </label>
        <label>
          <span>電話</span>
          <input v-model="form.phone" type="text" />
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
