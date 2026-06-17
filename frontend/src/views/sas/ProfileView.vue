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
  studentId: '',
  name: '',
  department: '',
  grade: '',
  email: '',
  phone: '',
  address: '',
  gpa: '',
  credits: '',
  familyStatus: '',
  bankAccount: '',
  emergencyContact: '',
})

function validate() {
  error.value = ''
  if (!form.email.includes('@')) error.value = 'Email 格式不正確。'
  if (!form.phone) error.value = '請填寫聯絡電話。'
  if (Number(form.gpa) < 0 || Number(form.gpa) > 4.3) error.value = 'GPA 必須介於 0 到 4.3。'
  return !error.value
}

async function save() {
  if (!validate()) return
  saving.value = true
  try {
    const updated = await updateProfile(auth.user.id, {
      grade: form.grade,
      email: form.email,
      phone: form.phone,
      address: form.address,
      gpa: Number(form.gpa),
      credits: Number(form.credits),
      familyStatus: form.familyStatus,
      bankAccount: form.bankAccount,
      emergencyContact: form.emergencyContact,
    })
    Object.assign(form, updated)
    toast.success('個人資料已更新')
  } finally {
    saving.value = false
  }
}

onMounted(async () => {
  Object.assign(form, await getProfile(auth.user.id))
  loading.value = false
})
</script>

<template>
  <LoadingSkeleton v-if="loading" :rows="5" />

  <div v-else class="page-grid">
    <BaseCard title="我的個人資料" eyebrow="Profile">
      <p class="muted-text">
        學號、姓名與科系為核心資料，需由管理單位更正；其餘資料會帶入獎學金申請表。
      </p>
      <p v-if="error" class="form-error">{{ error }}</p>

      <div class="field-group">
        <p class="field-group__title">核心資料</p>
        <p class="field-group__hint">以下欄位由管理單位維護，如需更正請聯繫系統管理員。</p>
        <div class="form-grid">
          <label>
            <span>學號</span>
            <input v-model="form.studentId" disabled type="text" />
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
            <input v-model="form.grade" type="text" />
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
            <input v-model="form.phone" type="tel" />
          </label>
          <label class="form-grid__wide">
            <span>通訊地址</span>
            <input v-model="form.address" type="text" />
          </label>
        </div>
      </div>

      <div class="field-group">
        <p class="field-group__title">學業與經濟</p>
        <div class="form-grid">
          <label>
            <span>GPA</span>
            <input v-model="form.gpa" max="4.3" min="0" step="0.01" type="number" />
          </label>
          <label>
            <span>已修學分</span>
            <input v-model="form.credits" min="0" type="number" />
          </label>
          <label class="form-grid__wide">
            <span>家庭與經濟狀況</span>
            <textarea v-model="form.familyStatus" rows="4" />
          </label>
        </div>
      </div>

      <div class="field-group">
        <p class="field-group__title">撥款與緊急聯絡</p>
        <div class="form-grid">
          <label>
            <span>撥款帳戶</span>
            <input v-model="form.bankAccount" type="text" />
          </label>
          <label>
            <span>緊急聯絡人</span>
            <input v-model="form.emergencyContact" type="text" />
          </label>
        </div>
      </div>

      <div class="form-actions">
        <button class="primary-button" type="button" :disabled="saving" @click="save">
          {{ saving ? '儲存中' : '儲存變更' }}
        </button>
      </div>
    </BaseCard>
  </div>
</template>
