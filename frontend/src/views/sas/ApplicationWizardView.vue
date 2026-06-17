<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import BaseCard from '@/components/common/BaseCard.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import LoadingSkeleton from '@/components/common/LoadingSkeleton.vue'
import StepForm from '@/components/common/StepForm.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import { getScholarship } from '@/api/sms'
import { createApplication, getProfile, listMyApplications } from '@/api/sas'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const toast = useToastStore()

const steps = ['基本資料', '學業與經濟', '推薦人', '文件與聲明', '確認送出']
const currentStep = ref(0)
const loading = ref(true)
const submitting = ref(false)
const error = ref('')
const scholarship = ref(null)
const alreadyApplied = ref(false)

const form = reactive({
  personal: {
    phone: '',
    address: '',
  },
  academics: {
    gpa: '',
    credits: '',
    achievements: '',
  },
  finance: {
    familyStatus: '',
    monthlyExpense: '',
  },
  recommender: {
    name: '陳明哲',
    email: 'mchen@nuk.edu.tw',
    title: '資訊管理學系副教授',
    relationship: '導師',
  },
  documents: [],
  statement: '',
})

const requiredDocs = computed(() => scholarship.value?.requiredDocs ?? [])

function validateStep(step = currentStep.value) {
  error.value = ''
  if (step === 0 && (!form.personal.phone || !form.personal.address)) {
    error.value = '請填寫聯絡電話與通訊地址。'
  }
  if (
    step === 1 &&
    (!form.academics.gpa ||
      Number(form.academics.gpa) <= 0 ||
      !form.finance.familyStatus ||
      !form.finance.monthlyExpense)
  ) {
    error.value = '請填寫 GPA、家庭狀況與每月支出。'
  }
  if (step === 2 && scholarship.value?.requireRecommendation) {
    const emailOk = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.recommender.email)
    if (
      !form.recommender.name ||
      !emailOk ||
      !form.recommender.title ||
      !form.recommender.relationship
    ) {
      error.value = '請完整填寫推薦人姓名、Email、職稱與關係。'
    }
  }
  if (step === 3) {
    const missingDocs = requiredDocs.value.filter((doc) => !form.documents.includes(doc))
    if (missingDocs.length) {
      error.value = `請確認已備妥：${missingDocs.join('、')}。`
    } else if (form.statement.trim().length < 20) {
      error.value = '申請動機至少需 20 個字。'
    }
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

async function submit() {
  if (!validateStep(3)) return
  submitting.value = true
  try {
    await createApplication(auth.user.id, {
      scholarshipId: scholarship.value.id,
      form: {
        personal: { ...form.personal },
        academics: {
          gpa: Number(form.academics.gpa),
          credits: Number(form.academics.credits || 0),
          achievements: form.academics.achievements,
        },
        finance: {
          familyStatus: form.finance.familyStatus,
          monthlyExpense: Number(form.finance.monthlyExpense),
        },
        statement: form.statement,
        documents: [...form.documents],
      },
      recommender: scholarship.value.requireRecommendation ? { ...form.recommender } : null,
    })
    toast.success('申請已送出，推薦信邀請與通知已建立')
    router.push('/applications')
  } catch (submitError) {
    toast.error(submitError.message || '申請送出失敗')
  } finally {
    submitting.value = false
  }
}

onMounted(async () => {
  const [profile, item, applications] = await Promise.all([
    getProfile(auth.user.id),
    getScholarship(route.params.id),
    listMyApplications(auth.user.id),
  ])
  scholarship.value = item
  alreadyApplied.value = applications.some((application) => application.scholarshipId === item.id)
  form.personal.phone = profile.phone
  form.personal.address = profile.address
  form.academics.gpa = profile.gpa
  form.academics.credits = profile.credits
  form.finance.familyStatus = profile.familyStatus
  loading.value = false
})
</script>

<template>
  <LoadingSkeleton v-if="loading" :rows="5" />

  <EmptyState
    v-else-if="alreadyApplied"
    title="你已經申請過此獎學金"
    description="系統不允許重複申請同一項獎學金，請到我的申請查看狀態。"
    icon="archive"
  >
    <RouterLink class="primary-button" to="/applications">查看狀態</RouterLink>
  </EmptyState>

  <div v-else class="page-grid">
    <BaseCard :title="scholarship.title" eyebrow="Application">
      <div class="card-row card-row--between">
        <p class="muted-text">{{ scholarship.description }}</p>
        <StatusBadge :value="scholarship.status" />
      </div>
      <StepForm :steps="steps" :current="currentStep" />
      <p v-if="error" class="form-error">{{ error }}</p>
    </BaseCard>

    <BaseCard v-if="currentStep === 0" title="基本聯絡資料">
      <div class="form-grid">
        <label>
          <span>聯絡電話</span>
          <input v-model="form.personal.phone" type="tel" />
        </label>
        <label>
          <span>通訊地址</span>
          <input v-model="form.personal.address" type="text" />
        </label>
      </div>
    </BaseCard>

    <BaseCard v-if="currentStep === 1" title="學業與經濟狀況">
      <div class="form-grid">
        <label>
          <span>GPA</span>
          <input v-model="form.academics.gpa" min="0" max="4.3" step="0.01" type="number" />
        </label>
        <label>
          <span>已修學分</span>
          <input v-model="form.academics.credits" min="0" type="number" />
        </label>
        <label>
          <span>每月支出</span>
          <input v-model="form.finance.monthlyExpense" min="0" type="number" />
        </label>
        <label class="form-grid__wide">
          <span>家庭與經濟狀況</span>
          <textarea v-model="form.finance.familyStatus" rows="4" />
        </label>
        <label class="form-grid__wide">
          <span>學業表現或特殊成就</span>
          <textarea v-model="form.academics.achievements" rows="4" />
        </label>
      </div>
    </BaseCard>

    <BaseCard v-if="currentStep === 2" title="推薦人資料">
      <div v-if="scholarship.requireRecommendation" class="form-grid">
        <label>
          <span>推薦人姓名</span>
          <input v-model="form.recommender.name" type="text" />
        </label>
        <label>
          <span>推薦人 Email</span>
          <input v-model="form.recommender.email" type="email" />
        </label>
        <label>
          <span>職稱或單位</span>
          <input v-model="form.recommender.title" type="text" />
        </label>
        <label>
          <span>與申請人關係</span>
          <input v-model="form.recommender.relationship" type="text" />
        </label>
      </div>
      <EmptyState
        v-else
        title="此獎學金不需要推薦信"
        description="你可以直接前往下一步確認文件與申請聲明。"
        icon="check"
      />
    </BaseCard>

    <BaseCard v-if="currentStep === 3" title="文件與申請聲明">
      <div class="check-list">
        <label v-for="doc in requiredDocs" :key="doc">
          <input v-model="form.documents" type="checkbox" :value="doc" />
          <span>{{ doc }}</span>
        </label>
      </div>
      <label class="stacked-field">
        <span>申請動機與說明</span>
        <textarea v-model="form.statement" rows="7" placeholder="請說明申請原因、學習計畫與經費用途" />
      </label>
    </BaseCard>

    <BaseCard v-if="currentStep === 4" title="確認送出">
      <dl class="review-list">
        <div>
          <dt>獎學金</dt>
          <dd>{{ scholarship.title }}</dd>
        </div>
        <div>
          <dt>聯絡方式</dt>
          <dd>{{ form.personal.phone }} · {{ form.personal.address }}</dd>
        </div>
        <div>
          <dt>GPA / 學分</dt>
          <dd>{{ form.academics.gpa }} / {{ form.academics.credits }}</dd>
        </div>
        <div v-if="scholarship.requireRecommendation">
          <dt>推薦人</dt>
          <dd>{{ form.recommender.name }} · {{ form.recommender.email }}</dd>
        </div>
        <div>
          <dt>文件</dt>
          <dd>{{ form.documents.join('、') }}</dd>
        </div>
      </dl>
    </BaseCard>

    <div class="form-actions">
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
        {{ submitting ? '送出中' : '送出申請' }}
      </button>
    </div>
  </div>
</template>
