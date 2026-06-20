<script setup>
import { onMounted, reactive, ref } from 'vue'
import BaseCard from '@/components/common/BaseCard.vue'
import LoadingSkeleton from '@/components/common/LoadingSkeleton.vue'
import { getProfile, updateProfile } from '@/api/sas'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'

const auth = useAuthStore()
const toast = useToastStore()
const loading = ref(true)
const saving = ref(false)
const error = ref('')

const form = reactive({
  account: '',
  name: '',
  department: '',
  grade: '',
  gpa: '',
  identity_type: '',
  email: '',
  contact_phone: '',
  address: '',
  emergency_contact_name: '',
  emergency_contact_phone: '',
})

function normalizeProfile(profile) {
  return {
    account: profile.account ?? profile.studentId ?? '',
    name: profile.name ?? '',
    department: profile.department ?? '',
    grade: profile.grade ?? '',
    gpa: profile.gpa ?? '',
    identity_type: profile.identity_type ?? profile.identityType ?? '',
    email: profile.email ?? '',
    contact_phone: profile.contact_phone ?? profile.phone ?? '',
    address: profile.address ?? '',
    emergency_contact_name:
      profile.emergency_contact_name ?? profile.emergencyContactName ?? profile.emergencyContact ?? '',
    emergency_contact_phone: profile.emergency_contact_phone ?? profile.emergencyContactPhone ?? '',
  }
}

function validate() {
  error.value = ''
  if (form.email && !form.email.includes('@')) {
    error.value = 'Email 格式不正確。'
  } else if (!form.contact_phone.trim()) {
    error.value = '請填寫聯絡電話。'
  }
  return !error.value
}

async function save() {
  if (!validate()) return
  saving.value = true
  try {
    const updated = await updateProfile(auth.user?.user_id ?? auth.user?.id, {
      email: form.email.trim() || null,
      contact_phone: form.contact_phone.trim() || null,
      address: form.address.trim() || null,
      emergency_contact_name: form.emergency_contact_name.trim() || null,
      emergency_contact_phone: form.emergency_contact_phone.trim() || null,
    })
    Object.assign(form, normalizeProfile(updated))
    toast.success('個人資料已更新')
  } catch (saveError) {
    error.value =
      saveError.response?.data?.detail?.[0]?.msg ||
      saveError.response?.data?.detail ||
      saveError.message ||
      '個人資料更新失敗'
  } finally {
    saving.value = false
  }
}

onMounted(async () => {
  try {
    const profile = await getProfile(auth.user?.user_id ?? auth.user?.id)
    Object.assign(form, normalizeProfile(profile))
  } catch (loadError) {
    error.value = loadError.response?.data?.detail || loadError.message || '個人資料載入失敗'
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <LoadingSkeleton v-if="loading" :rows="5" />

  <div v-else class="profile-page page-grid">
    <BaseCard class="profile-card" title="我的個人資料" eyebrow="Profile">
      <p class="muted-text">
        學號、姓名、科系、年級、GPA 與身份類別為核心資料，需由管理單位更正。
      </p>
      <p v-if="error" class="form-error">{{ error }}</p>

      <div class="field-group">
        <p class="field-group__title">核心資料</p>
        <p class="field-group__hint">以下欄位僅供查看，學生無法自行修改。</p>
        <div class="form-grid">
          <label>
            <span>學號</span>
            <input v-model="form.account" disabled type="text" />
          </label>
          <label>
            <span>姓名</span>
            <input v-model="form.name" disabled type="text" />
          </label>
          <label>
            <span>科系</span>
            <input v-model="form.department" disabled type="text" />
          </label>
          <label>
            <span>年級</span>
            <input v-model="form.grade" disabled type="text" />
          </label>
          <label>
            <span>GPA</span>
            <input v-model="form.gpa" disabled type="text" />
          </label>
          <label>
            <span>身份類別</span>
            <input v-model="form.identity_type" disabled type="text" />
          </label>
        </div>
      </div>

      <div class="field-group">
        <p class="field-group__title">聯絡資料</p>
        <div class="form-grid">
          <label>
            <span>Email</span>
            <input v-model="form.email" type="email" />
          </label>
          <label>
            <span>聯絡電話</span>
            <input v-model="form.contact_phone" type="tel" />
          </label>
          <label class="form-grid__wide">
            <span>通訊地址</span>
            <input v-model="form.address" type="text" />
          </label>
        </div>
      </div>

      <div class="field-group">
        <p class="field-group__title">緊急聯絡資料</p>
        <div class="form-grid">
          <label>
            <span>緊急聯絡人</span>
            <input v-model="form.emergency_contact_name" type="text" />
          </label>
          <label>
            <span>緊急聯絡電話</span>
            <input v-model="form.emergency_contact_phone" type="tel" />
          </label>
        </div>
      </div>

      <div class="form-actions profile-actions">
        <button class="primary-button" type="button" :disabled="saving" @click="save">
          {{ saving ? '儲存中' : '儲存變更' }}
        </button>
      </div>
    </BaseCard>
  </div>
</template>

<style scoped>
.profile-page,
.profile-card {
  width: 100%;
}

.profile-page .muted-text {
  max-width: 920px;
}

.profile-page .form-grid {
  gap: 18px 20px;
}

.profile-page .profile-actions {
  position: static;
  bottom: auto;
  z-index: auto;
  margin-top: 24px;
  padding: 16px 0 0;
  border: 0;
  border-top: 1px solid var(--line);
  border-radius: 0;
  background: transparent;
  box-shadow: none;
  backdrop-filter: none;
}

@media (min-width: 1180px) {
  .profile-card {
    padding-inline: clamp(24px, 2.2vw, 40px);
  }
}

@media (max-width: 760px) {
  .profile-page .profile-actions {
    justify-content: stretch;
  }

  .profile-page .profile-actions .primary-button {
    width: 100%;
  }
}
</style>
