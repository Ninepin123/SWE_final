<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import BaseCard from '@/components/common/BaseCard.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import LoadingSkeleton from '@/components/common/LoadingSkeleton.vue'
import StepForm from '@/components/common/StepForm.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import {
  createApplication,
  getProfile,
  listAvailableScholarships,
  listMyApplications,
  submitApplication,
  updateApplication,
} from '@/api/sas'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const toast = useToastStore()

const steps = ['聯絡資料', '申請內容', '確認送出']
const currentStep = ref(0)
const loading = ref(true)
const saving = ref(false)
const submitting = ref(false)
const error = ref('')
const scholarship = ref(null)
const applicationId = ref(null)
const existingSubmitted = ref(false)

const form = reactive({
  contact_phone: '',
  address: '',
  household_status: '',
  academic_note: '',
  statement: '',
})

const isDraft = computed(() => !!applicationId.value && !existingSubmitted.value)

function applicationPayload() {
  return {
    statement: form.statement.trim() || null,
    contact_phone: form.contact_phone.trim() || null,
    address: form.address.trim() || null,
    household_status: form.household_status.trim() || null,
    academic_note: form.academic_note.trim() || null,
  }
}

function validateStep(step = currentStep.value) {
  error.value = ''
  if (step === 0 && (!form.contact_phone.trim() || !form.address.trim())) {
    error.value = '請填寫聯絡電話與通訊地址。'
  } else if (
    step === 1 &&
    (!form.household_status.trim() || form.statement.trim().length < 20)
  ) {
    error.value = '請填寫家庭狀況，且申請理由至少需 20 個字。'
  }
  return !error.value
}

function nextStep() {
  if (!validateStep()) return
  currentStep.value += 1
}

function prevStep() {
  error.value = ''
  currentStep.value -= 1
}

async function saveDraft(showMessage = true) {
  saving.value = true
  error.value = ''
  try {
    const payload = applicationPayload()
    let saved
    if (applicationId.value) {
      saved = await updateApplication(applicationId.value, payload)
    } else {
      saved = await createApplication(auth.user?.user_id ?? auth.user?.id, {
        scholarship_id: scholarship.value.id,
        ...payload,
      })
      applicationId.value = saved.application_id
    }
    if (showMessage) toast.success('草稿已儲存')
    return saved
  } catch (saveError) {
    error.value = saveError.response?.data?.detail || saveError.message || '草稿儲存失敗'
    return null
  } finally {
    saving.value = false
  }
}

async function submit() {
  if (!validateStep(0) || !validateStep(1)) return
  if (!window.confirm('正式送出後將無法修改申請資料，確定送出嗎？')) return
  submitting.value = true
  try {
    const saved = await saveDraft(false)
    if (!saved) return
    await submitApplication(applicationId.value)
    toast.success('申請已正式送出')
    router.push('/applications')
  } catch (submitError) {
    error.value =
      submitError.response?.data?.detail || submitError.message || '申請送出失敗'
  } finally {
    submitting.value = false
  }
}

onMounted(async () => {
  try {
    const userId = auth.user?.user_id ?? auth.user?.id
    const [profile, scholarships, applications] = await Promise.all([
      getProfile(userId),
      listAvailableScholarships(userId),
      listMyApplications(userId),
    ])
    scholarship.value = scholarships.find(
      (item) => String(item.id) === String(route.params.id),
    )
    if (!scholarship.value) throw new Error('找不到獎學金')

    const existing = applications.find(
      (item) => String(item.scholarship_id ?? item.scholarshipId) === String(route.params.id),
    )
    if (existing) {
      applicationId.value = existing.application_id ?? existing.id
      existingSubmitted.value = existing.status !== 'DRAFT'
      Object.assign(form, {
        contact_phone: existing.contact_phone ?? '',
        address: existing.address ?? '',
        household_status: existing.household_status ?? '',
        academic_note: existing.academic_note ?? '',
        statement: existing.statement ?? '',
      })
    } else {
      form.contact_phone = profile.contact_phone ?? profile.phone ?? ''
      form.address = profile.address ?? ''
    }
  } catch (loadError) {
    error.value = loadError.response?.data?.detail || loadError.message || '申請資料載入失敗'
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <LoadingSkeleton v-if="loading" :rows="5" />

  <EmptyState
    v-else-if="existingSubmitted"
    title="這份申請已正式送出"
    description="正式送出的申請不能再修改，請到我的申請查看目前狀態。"
    icon="archive"
  >
    <RouterLink class="primary-button" to="/applications">查看申請狀態</RouterLink>
  </EmptyState>

  <div v-else-if="scholarship" class="page-grid">
    <BaseCard :title="scholarship.title" eyebrow="Application">
      <div class="card-row card-row--between">
        <p class="muted-text">{{ scholarship.description }}</p>
        <StatusBadge :value="isDraft ? 'DRAFT' : scholarship.status" />
      </div>
      <StepForm :steps="steps" :current="currentStep" />
      <p v-if="error" class="form-error">{{ error }}</p>
    </BaseCard>

    <BaseCard v-if="currentStep === 0" title="基本聯絡資料">
      <div class="form-grid">
        <label>
          <span>聯絡電話</span>
          <input v-model="form.contact_phone" type="tel" />
        </label>
        <label>
          <span>通訊地址</span>
          <input v-model="form.address" type="text" />
        </label>
      </div>
    </BaseCard>

    <BaseCard v-if="currentStep === 1" title="申請內容">
      <div class="form-grid">
        <label class="form-grid__wide">
          <span>家庭與經濟狀況</span>
          <textarea v-model="form.household_status" rows="4" />
        </label>
        <label class="form-grid__wide">
          <span>學業表現或特殊成就</span>
          <textarea v-model="form.academic_note" rows="4" />
        </label>
        <label class="form-grid__wide">
          <span>申請理由</span>
          <textarea
            v-model="form.statement"
            rows="7"
            placeholder="請說明申請原因、學習計畫與經費用途（至少 20 字）"
          />
        </label>
      </div>
    </BaseCard>

    <BaseCard v-if="currentStep === 2" title="確認送出">
      <dl class="review-list">
        <div>
          <dt>獎學金</dt>
          <dd>{{ scholarship.title }}</dd>
        </div>
        <div>
          <dt>聯絡方式</dt>
          <dd>{{ form.contact_phone }} · {{ form.address }}</dd>
        </div>
        <div>
          <dt>家庭狀況</dt>
          <dd>{{ form.household_status }}</dd>
        </div>
        <div>
          <dt>申請理由</dt>
          <dd>{{ form.statement }}</dd>
        </div>
      </dl>
      <p class="muted-text">正式送出後不能再修改；若尚未完成，可以先儲存草稿。</p>
    </BaseCard>

    <div class="form-actions">
      <button
        class="secondary-button"
        type="button"
        :disabled="saving || submitting"
        @click="saveDraft"
      >
        {{ saving ? '儲存中' : '儲存草稿' }}
      </button>
      <button
        class="secondary-button"
        type="button"
        :disabled="currentStep === 0 || submitting"
        @click="prevStep"
      >
        上一步
      </button>
      <button
        v-if="currentStep < steps.length - 1"
        class="primary-button"
        type="button"
        @click="nextStep"
      >
        下一步
      </button>
      <button v-else class="primary-button" type="button" :disabled="submitting" @click="submit">
        {{ submitting ? '送出中' : '正式送出' }}
      </button>
    </div>
  </div>
</template>
