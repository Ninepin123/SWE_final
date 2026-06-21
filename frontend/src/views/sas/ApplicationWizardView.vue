<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import BaseCard from '@/components/common/BaseCard.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import LoadingSkeleton from '@/components/common/LoadingSkeleton.vue'
import StepForm from '@/components/common/StepForm.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import {
  createApplication,
  getProfile,
  listApplicationDocuments,
  listAvailableScholarships,
  listMyApplications,
  saveApplicationDocument,
  submitApplication,
  updateApplication,
} from '@/api/sas'
import { listTeachers } from '@/api/aas'
import { listStudentRecommendationStatus, requestRecommendation } from '@/api/trs'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const toast = useToastStore()

const steps = ['基本資料', '申請內容', '附件文件', '推薦信邀請', '確認送出']
const currentStep = ref(0)
const loading = ref(true)
const saving = ref(false)
const submitting = ref(false)
const error = ref('')
const scholarship = ref(null)
const applicationId = ref(null)
const existingSubmitted = ref(false)
const teachers = ref([])
const recommendations = ref([])
const recommendationLoading = ref(false)
const recommendationError = ref('')
const inviteTeacherId = ref('')
const invitingRecommendation = ref(false)

const RECOMMENDATION_STATUS_LABEL = {
  REQUESTED: '已邀請（等待老師撰寫）',
  PENDING: '已邀請（等待老師撰寫）',
  DRAFT: '老師撰寫中',
  SUBMITTED: '已提交',
}

// 自動儲存草稿：使用者一邊填、系統一邊存，不需要手動按「儲存草稿」。
const ready = ref(false)
const autoSaveState = ref('idle') // 'idle' | 'saving' | 'saved' | 'error'
const lastSavedAt = ref(null)
let autoSaveTimer = null
let lastSavedAppJson = ''
const lastSavedDocs = reactive({})

const form = reactive({
  contact_phone: '',
  address: '',
  household_status: '',
  academic_note: '',
  statement: '',
  documents: {
    TRANSCRIPT: {
      title: '成績單內容',
      content_text: '',
    },
    AUTOBIOGRAPHY: {
      title: '自傳',
      content_text: '',
    },
    CERTIFICATE: {
      title: '證明文件說明',
      content_text: '',
    },
  },
})

const isDraft = computed(() => !!applicationId.value && !existingSubmitted.value)
const requiresRecommendation = computed(() =>
  Boolean(scholarship.value?.requireRecommendation ?? scholarship.value?.require_recommendation),
)

function applicationPayload() {
  return {
    statement: form.statement.trim() || null,
    contact_phone: form.contact_phone.trim() || null,
    address: form.address.trim() || null,
    household_status: form.household_status.trim() || null,
    academic_note: form.academic_note.trim() || null,
  }
}

function validateStep(step = currentStep.value, { focusInvalidStep = false } = {}) {
  error.value = ''
  if (step === 0 && (!form.contact_phone.trim() || !form.address.trim())) {
    error.value = '請填寫聯絡電話與通訊地址。'
  } else if (
    step === 1 &&
    (!form.household_status.trim() || form.statement.trim().length < 20)
  ) {
    error.value = '請填寫家庭狀況，且申請理由至少需 20 個字。'
  } else if (
    step === 2 &&
    !Object.values(form.documents).some((document) => document.content_text.trim())
  ) {
    error.value = '請至少填寫一份文字文件。'
  } else if (step === 3 && requiresRecommendation.value && !recommendations.value.length) {
    error.value = '此獎學金需要推薦信，請先邀請至少一位老師。'
  }
  if (error.value) {
    if (focusInvalidStep) currentStep.value = step
    toast.warning(error.value)
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

// 記住「上次成功存檔的內容」，用來判斷是否真的有改動、要不要重存文件。
function snapshotSaved() {
  lastSavedAppJson = JSON.stringify(applicationPayload())
  for (const [documentType, document] of Object.entries(form.documents)) {
    lastSavedDocs[documentType] = document.content_text
  }
}

function hasUnsavedChanges() {
  if (JSON.stringify(applicationPayload()) !== lastSavedAppJson) return true
  return Object.entries(form.documents).some(
    ([documentType, document]) => (lastSavedDocs[documentType] ?? '') !== document.content_text,
  )
}

// 所有存檔（自動 + 手動 + 送出前）串接在同一條 promise 上，避免兩個存檔同時
// 跑而重複建立草稿（例如自動儲存還沒回來、使用者就按了正式送出）。
let saveChain = Promise.resolve()

function persistDraft(options = {}) {
  saveChain = saveChain.then(() => doPersistDraft(options))
  return saveChain
}

async function doPersistDraft({ showSuccess = true, silentError = false } = {}) {
  saving.value = true
  if (!showSuccess) autoSaveState.value = 'saving'
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
    for (const [documentType, document] of Object.entries(form.documents)) {
      if (!document.content_text.trim()) continue
      // 內容沒變就不重存，避免每次自動存檔都灌一筆「更新文件」事件。
      if (lastSavedDocs[documentType] === document.content_text) continue
      await saveApplicationDocument(applicationId.value, {
        document_type: documentType,
        title: document.title,
        content_text: document.content_text,
      })
    }
    snapshotSaved()
    lastSavedAt.value = new Date()
    autoSaveState.value = 'saved'
    if (showSuccess) toast.success('草稿與文字文件已儲存')
    return saved
  } catch (saveError) {
    error.value = saveError.response?.data?.detail || saveError.message || '草稿儲存失敗'
    autoSaveState.value = 'error'
    if (!silentError) toast.error(error.value)
    return null
  } finally {
    saving.value = false
  }
}

function saveDraft() {
  return persistDraft({ showSuccess: true })
}

function scheduleAutoSave() {
  if (!ready.value || existingSubmitted.value) return
  if (autoSaveTimer) clearTimeout(autoSaveTimer)
  autoSaveTimer = setTimeout(runAutoSave, 1200)
}

async function runAutoSave() {
  // 有其他存檔/送出正在進行時稍後再試，避免重複建立草稿。
  if (!ready.value || saving.value || submitting.value || existingSubmitted.value) {
    scheduleAutoSave()
    return
  }
  if (!hasUnsavedChanges()) return
  await persistDraft({ showSuccess: false, silentError: true })
}

async function submit() {
  for (const step of [0, 1, 2, 3]) {
    if (!validateStep(step, { focusInvalidStep: true })) return
  }
  if (!window.confirm('正式送出後將無法修改申請資料，確定送出嗎？')) return
  submitting.value = true
  try {
    const saved = await persistDraft({ showSuccess: false })
    if (!saved) return
    await submitApplication(applicationId.value)
    toast.success('申請已正式送出')
    router.push('/applications')
  } catch (submitError) {
    error.value =
      submitError.response?.data?.detail || submitError.message || '申請送出失敗'
    toast.error(error.value)
  } finally {
    submitting.value = false
  }
}

function recommendationStatusLabel(status) {
  return RECOMMENDATION_STATUS_LABEL[status] || status
}

async function loadTeachers() {
  try {
    teachers.value = await listTeachers()
  } catch (teacherError) {
    recommendationError.value =
      teacherError.response?.data?.detail || teacherError.message || '老師清單載入失敗'
  }
}

async function loadRecommendations() {
  if (!applicationId.value) {
    recommendations.value = []
    return
  }
  recommendationLoading.value = true
  try {
    const all = await listStudentRecommendationStatus()
    recommendations.value = all.filter(
      (rec) => String(rec.applicationId) === String(applicationId.value),
    )
  } catch (loadError) {
    recommendationError.value =
      loadError.response?.data?.detail || loadError.message || '推薦邀請狀態載入失敗'
  } finally {
    recommendationLoading.value = false
  }
}

async function inviteRecommendation() {
  if (!inviteTeacherId.value) return
  invitingRecommendation.value = true
  recommendationError.value = ''
  try {
    const saved = await persistDraft({ showSuccess: false })
    if (!saved) return
    await requestRecommendation(applicationId.value, Number(inviteTeacherId.value))
    toast.success('已送出推薦邀請')
    inviteTeacherId.value = ''
    await loadRecommendations()
  } catch (inviteError) {
    recommendationError.value =
      inviteError.response?.data?.detail || inviteError.message || '推薦邀請送出失敗'
    toast.error(recommendationError.value)
  } finally {
    invitingRecommendation.value = false
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
      const documents = await listApplicationDocuments(applicationId.value)
      for (const document of documents) {
        if (form.documents[document.document_type]) {
          form.documents[document.document_type].title = document.title
          form.documents[document.document_type].content_text = document.content_text
        }
      }
    } else {
      form.contact_phone = profile.contact_phone ?? profile.phone ?? ''
      form.address = profile.address ?? ''
    }
    await Promise.all([
      loadTeachers(),
      applicationId.value ? loadRecommendations() : Promise.resolve(),
    ])
  } catch (loadError) {
    error.value = loadError.response?.data?.detail || loadError.message || '申請資料載入失敗'
  } finally {
    loading.value = false
    // 以載入完成當下的內容作為基準，之後使用者一改動就會觸發自動儲存。
    snapshotSaved()
    ready.value = true
  }
})

// 監看所有可編輯欄位，改動後 1.2 秒（去抖動）自動把草稿存回後端。
watch(
  () => [
    form.contact_phone,
    form.address,
    form.household_status,
    form.academic_note,
    form.statement,
    form.documents.TRANSCRIPT.content_text,
    form.documents.AUTOBIOGRAPHY.content_text,
    form.documents.CERTIFICATE.content_text,
  ],
  scheduleAutoSave,
)

onBeforeUnmount(() => {
  if (autoSaveTimer) clearTimeout(autoSaveTimer)
})

function formatSavedTime(value) {
  if (!value) return ''
  return new Intl.DateTimeFormat('zh-TW', { hour: '2-digit', minute: '2-digit' }).format(value)
}
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

  <div v-else-if="scholarship" class="application-page page-grid">
    <section class="application-hero">
      <div>
        <p class="eyebrow">Application Wizard</p>
        <h2>{{ scholarship.title }}</h2>
        <p>{{ scholarship.description }}</p>
      </div>
      <StatusBadge :value="isDraft ? 'DRAFT' : scholarship.status" />
    </section>

    <BaseCard class="application-step-card">
      <StepForm :steps="steps" :current="currentStep" />
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

    <BaseCard v-if="currentStep === 2" title="附件文件">
      <p class="muted-text">目前以文字內容代替實體附件；每一格可視為一份申請附件，送出前至少填寫一份。</p>
      <div class="document-grid">
        <label class="document-box">
          <span>成績單內容</span>
          <textarea
            v-model="form.documents.TRANSCRIPT.content_text"
            rows="5"
            placeholder="請以文字整理主要科目、成績、排名或 GPA 說明"
          />
        </label>
        <label class="document-box document-box--wide">
          <span>自傳</span>
          <textarea
            v-model="form.documents.AUTOBIOGRAPHY.content_text"
            rows="7"
            placeholder="請輸入自傳內容"
          />
        </label>
        <label class="document-box">
          <span>其他證明文件說明</span>
          <textarea
            v-model="form.documents.CERTIFICATE.content_text"
            rows="5"
            placeholder="請描述相關證明、獎項或經歷"
          />
        </label>
      </div>
    </BaseCard>

    <BaseCard v-if="currentStep === 3" title="推薦信邀請">
      <p class="muted-text">
        推薦信邀請需在申請草稿階段完成；送出邀請時會先建立或更新目前草稿。
      </p>
      <p v-if="recommendationError" class="form-error">{{ recommendationError }}</p>

      <p v-if="recommendationLoading" class="muted-text">推薦邀請狀態載入中…</p>
      <div v-else-if="recommendations.length" class="recommendation-list">
        <article
          v-for="rec in recommendations"
          :key="rec.recId"
          class="mini-panel rec-status-panel"
        >
          <div>
            <strong>{{ rec.teacherName || '推薦老師' }}</strong>
            <p class="muted-text">{{ recommendationStatusLabel(rec.status) }}</p>
          </div>
          <StatusBadge :value="rec.status" />
        </article>
      </div>
      <p v-else class="muted-text">
        {{ requiresRecommendation ? '此獎學金需要推薦信，請先邀請老師。' : '尚未邀請任何老師撰寫推薦信。' }}
      </p>

      <div class="rec-invite">
        <label>
          <span>邀請老師撰寫推薦信</span>
          <select v-model="inviteTeacherId">
            <option value="">請選擇老師</option>
            <option v-for="teacher in teachers" :key="teacher.user_id" :value="teacher.user_id">
              {{ teacher.name }}<template v-if="teacher.department"> · {{ teacher.department }}</template>
            </option>
          </select>
        </label>
        <button
          class="primary-button"
          type="button"
          :disabled="!inviteTeacherId || invitingRecommendation || saving || submitting"
          @click="inviteRecommendation"
        >
          {{ invitingRecommendation ? '送出中' : '送出邀請' }}
        </button>
      </div>
    </BaseCard>

    <BaseCard v-if="currentStep === 4" title="確認送出">
      <dl class="review-list application-review-list">
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
        <div>
          <dt>文字文件</dt>
          <dd>
            {{
              Object.values(form.documents).filter((document) => document.content_text.trim())
                .length
            }}
            份
          </dd>
        </div>
        <div>
          <dt>推薦信邀請</dt>
          <dd>{{ recommendations.length }} 位老師</dd>
        </div>
      </dl>
      <p class="muted-text">正式送出後不能再修改；若尚未完成，可以先儲存草稿。</p>
    </BaseCard>

    <div class="form-actions">
      <span class="autosave-status" :class="`autosave-status--${autoSaveState}`">
        <template v-if="autoSaveState === 'saving'">草稿自動儲存中…</template>
        <template v-else-if="autoSaveState === 'error'">自動儲存失敗，請按「儲存草稿」</template>
        <template v-else-if="autoSaveState === 'saved'">已自動儲存 · {{ formatSavedTime(lastSavedAt) }}</template>
        <template v-else>系統會自動保留草稿，免按儲存</template>
      </span>
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

  <EmptyState
    v-else
    title="無法載入申請資料"
    :description="error || '找不到這個獎學金，請回到可申請獎學金列表重新選擇。'"
    icon="archive"
  >
    <RouterLink class="primary-button" to="/scholarships">回到獎學金列表</RouterLink>
  </EmptyState>
</template>

<style scoped>
.rec-invite {
  display: flex;
  align-items: flex-end;
  gap: 0.75rem;
  margin-top: 0.75rem;
}

.rec-invite label {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
}

@media (max-width: 760px) {
  .rec-invite {
    align-items: stretch;
    flex-direction: column;
  }
}
</style>
