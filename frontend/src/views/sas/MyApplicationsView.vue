<script setup>
import { onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import AuditTimeline from '@/components/common/AuditTimeline.vue'
import BaseCard from '@/components/common/BaseCard.vue'
import BaseModal from '@/components/common/BaseModal.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import LoadingSkeleton from '@/components/common/LoadingSkeleton.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import { listApplicationDocuments, listApplicationEvents, listMyApplications } from '@/api/sas'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'

const auth = useAuthStore()
const toast = useToastStore()
const loading = ref(true)
const applications = ref([])
const selected = ref(null)
const selectedEvents = ref([])
const selectedDocuments = ref([])
const detailLoading = ref(false)

const eventLabels = {
  DRAFT_CREATED: '建立申請草稿',
  DRAFT_UPDATED: '更新申請草稿',
  DOCUMENT_CREATED: '新增文字文件',
  DOCUMENT_UPDATED: '更新文字文件',
  DOCUMENT_DELETED: '刪除文字文件',
  APPLICATION_SUBMITTED: '正式送出申請',
  SUPPLEMENT_REQUESTED: '審查人員要求補件',
  SUPPLEMENT_SUBMITTED: '學生完成補件',
  STATUS_CHANGED: '申請狀態更新',
}

function formatDate(value) {
  if (!value) return '—'
  return new Intl.DateTimeFormat('zh-TW', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(value))
}

async function openDetail(application) {
  selected.value = application
  selectedEvents.value = []
  selectedDocuments.value = []
  detailLoading.value = true
  try {
    const [events, documents] = await Promise.all([
      listApplicationEvents(application.application_id),
      listApplicationDocuments(application.application_id),
    ])
    selectedEvents.value = events.map((event) => ({
      ...event,
      action: eventLabels[event.action] || event.action,
    }))
    selectedDocuments.value = documents
  } catch (error) {
    toast.error(error.response?.data?.detail || error.message || '申請詳情載入失敗')
  } finally {
    detailLoading.value = false
  }
}

onMounted(async () => {
  try {
    applications.value = await listMyApplications(auth.user?.user_id ?? auth.user?.id)
  } catch (error) {
    toast.error(error.response?.data?.detail || error.message || '申請紀錄載入失敗')
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <LoadingSkeleton v-if="loading" :rows="4" />

  <EmptyState
    v-else-if="!applications.length"
    title="尚未建立任何申請"
    description="從可申請獎學金開始，可以先儲存草稿，再於期限內正式送出。"
    icon="application"
  />

  <div v-else class="page-grid">
    <BaseCard title="我的申請紀錄" eyebrow="Applications">
      <div class="table-wrap">
        <table class="data-table">
          <thead>
            <tr>
              <th>獎學金</th>
              <th>建立時間</th>
              <th>送出時間</th>
              <th>狀態</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="application in applications" :key="application.application_id ?? application.id">
              <td>
                <strong>{{ application.scholarship_name ?? application.scholarship?.title }}</strong>
              </td>
              <td>{{ formatDate(application.created_at ?? application.submittedAt) }}</td>
              <td>{{ formatDate(application.submitted_at ?? application.submittedAt) }}</td>
              <td><StatusBadge :value="application.status" /></td>
              <td>
                <div class="table-actions">
                  <button class="secondary-button" type="button" @click="openDetail(application)">
                    查看進度
                  </button>
                  <RouterLink
                    v-if="application.status === 'DRAFT'"
                    class="primary-button"
                    :to="`/scholarships/${application.scholarship_id}/apply`"
                  >
                    繼續填寫
                  </RouterLink>
                  <RouterLink
                    v-else-if="application.status === 'NEED_SUPPLEMENT'"
                    class="primary-button"
                    :to="`/applications/${application.application_id}/supplement`"
                  >
                    提交補件
                  </RouterLink>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </BaseCard>
  </div>

  <BaseModal
    :show="!!selected"
    :title="selected?.scholarship_name || '申請詳情'"
    width="920px"
    @close="selected = null"
  >
    <LoadingSkeleton v-if="detailLoading" :rows="4" />
    <div v-else-if="selected" class="detail-grid">
      <section>
        <h3>申請摘要</h3>
        <dl class="review-list">
          <div>
            <dt>目前狀態</dt>
            <dd><StatusBadge :value="selected.status" /></dd>
          </div>
          <div>
            <dt>建立時間</dt>
            <dd>{{ formatDate(selected.created_at) }}</dd>
          </div>
          <div>
            <dt>正式送出</dt>
            <dd>{{ formatDate(selected.submitted_at) }}</dd>
          </div>
          <div>
            <dt>申請理由</dt>
            <dd>{{ selected.statement || '—' }}</dd>
          </div>
        </dl>

        <h3>文字文件</h3>
        <div v-if="selectedDocuments.length" class="recommendation-list">
          <article v-for="document in selectedDocuments" :key="document.document_id" class="mini-panel">
            <strong>{{ document.title }}</strong>
            <p>{{ document.content_text }}</p>
          </article>
        </div>
        <p v-else class="muted-text">目前沒有文字文件。</p>
      </section>

      <section>
        <h3>申請進度</h3>
        <AuditTimeline v-if="selectedEvents.length" :logs="selectedEvents" />
        <p v-else class="muted-text">目前沒有進度紀錄。</p>
      </section>
    </div>
  </BaseModal>
</template>
