<script setup>
import { computed, onMounted, ref } from 'vue'
import AuditTimeline from '@/components/common/AuditTimeline.vue'
import BaseCard from '@/components/common/BaseCard.vue'
import BaseModal from '@/components/common/BaseModal.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import LoadingSkeleton from '@/components/common/LoadingSkeleton.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import { listMyApplications, sendRecommendationReminder } from '@/api/sas'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'

const auth = useAuthStore()
const toast = useToastStore()
const loading = ref(true)
const applications = ref([])
const selected = ref(null)

const sortedApplications = computed(() =>
  [...applications.value].sort((a, b) => new Date(b.updatedAt) - new Date(a.updatedAt)),
)

function formatDate(value) {
  if (!value) return '-'
  return new Intl.DateTimeFormat('zh-TW', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  }).format(new Date(value))
}

async function reload() {
  applications.value = await listMyApplications(auth.user.id)
}

async function remind(request) {
  await sendRecommendationReminder(auth.user.id, request.id)
  toast.success('已送出推薦信提醒')
  await reload()
  selected.value = applications.value.find((item) => item.id === selected.value.id)
}

onMounted(async () => {
  await reload()
  loading.value = false
})
</script>

<template>
  <LoadingSkeleton v-if="loading" :rows="4" />

  <EmptyState
    v-else-if="!applications.length"
    title="尚未送出任何申請"
    description="從可申請獎學金開始，完成多步驟表單後即可在這裡追蹤進度。"
    icon="application"
  />

  <div v-else class="page-grid">
    <BaseCard title="我的申請紀錄" eyebrow="Applications">
      <div class="table-wrap">
        <table class="data-table">
          <thead>
            <tr>
              <th>獎學金</th>
              <th>送出日期</th>
              <th>狀態</th>
              <th>推薦信</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="application in sortedApplications" :key="application.id">
              <td>
                <strong>{{ application.scholarship?.title }}</strong>
                <span>{{ application.scholarship?.category }}</span>
              </td>
              <td>{{ formatDate(application.submittedAt) }}</td>
              <td><StatusBadge :value="application.status" /></td>
              <td>
                <StatusBadge
                  v-if="application.recommendations.length"
                  :value="application.recommendations[0].status"
                />
                <span v-else class="muted-text">不需要</span>
              </td>
              <td>
                <button class="secondary-button" type="button" @click="selected = application">
                  查看狀態
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </BaseCard>
  </div>

  <BaseModal
    :show="!!selected"
    :title="selected ? selected.scholarship?.title : ''"
    width="920px"
    @close="selected = null"
  >
    <div v-if="selected" class="detail-grid">
      <section>
        <h3>申請摘要</h3>
        <dl class="review-list">
          <div>
            <dt>目前狀態</dt>
            <dd><StatusBadge :value="selected.status" /></dd>
          </div>
          <div>
            <dt>送出時間</dt>
            <dd>{{ formatDate(selected.submittedAt) }}</dd>
          </div>
          <div>
            <dt>GPA</dt>
            <dd>{{ selected.form.academics.gpa }}</dd>
          </div>
          <div>
            <dt>文件</dt>
            <dd>{{ selected.form.documents.join('、') }}</dd>
          </div>
        </dl>

        <h3>推薦信狀態</h3>
        <div v-if="selected.recommendations.length" class="recommendation-list">
          <div v-for="request in selected.recommendations" :key="request.id" class="mini-panel">
            <div>
              <strong>{{ request.recommenderName }}</strong>
              <p>{{ request.recommenderTitle }} · {{ request.recommenderEmail }}</p>
            </div>
            <StatusBadge :value="request.status" />
            <button
              v-if="request.status !== 'SUBMITTED'"
              class="secondary-button"
              type="button"
              @click="remind(request)"
            >
              提醒推薦人
            </button>
          </div>
        </div>
        <p v-else class="muted-text">此申請不需要推薦信。</p>
      </section>

      <section>
        <h3>審核紀錄</h3>
        <AuditTimeline :logs="selected.auditLogs" />
      </section>
    </div>
  </BaseModal>
</template>
