<script setup>
import { computed, onMounted, ref } from 'vue'
import BaseCard from '@/components/common/BaseCard.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import LoadingSkeleton from '@/components/common/LoadingSkeleton.vue'
import { listNotifications, markNotificationRead } from '@/api/ncs'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'

const auth = useAuthStore()
const toast = useToastStore()
const loading = ref(true)
const notifications = ref([])
const filter = ref('all')

const visibleNotifications = computed(() => {
  if (filter.value === 'unread') return notifications.value.filter((item) => !item.read)
  return notifications.value
})

function formatDate(value) {
  return new Intl.DateTimeFormat('zh-TW', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(value))
}

async function reload() {
  notifications.value = await listNotifications(auth.user.id)
}

async function read(item) {
  if (item.read) return
  await markNotificationRead(auth.user.id, item.id)
  toast.success('已標記為已讀')
  await reload()
}

onMounted(async () => {
  await reload()
  loading.value = false
})
</script>

<template>
  <div class="page-grid">
    <BaseCard title="通知中心" eyebrow="Notifications">
      <div class="segmented">
        <button
          type="button"
          :class="{ active: filter === 'all' }"
          @click="filter = 'all'"
        >
          全部
        </button>
        <button
          type="button"
          :class="{ active: filter === 'unread' }"
          @click="filter = 'unread'"
        >
          未讀
        </button>
      </div>
    </BaseCard>

    <LoadingSkeleton v-if="loading" :rows="5" />
    <EmptyState
      v-else-if="!visibleNotifications.length"
      title="目前沒有通知"
      description="申請成功、補件、審查結果與推薦信提醒會出現在這裡。"
      icon="notification"
    />

    <BaseCard v-else>
      <div class="notification-list">
        <button
          v-for="item in visibleNotifications"
          :key="item.id"
          type="button"
          class="notification-item"
          :class="[`notification-item--${item.type}`, { 'notification-item--read': item.read }]"
          @click="read(item)"
        >
          <span class="notification-item__dot" />
          <div>
            <div class="notification-item__top">
              <strong>{{ item.title }}</strong>
              <time>{{ formatDate(item.createdAt) }}</time>
            </div>
            <p>{{ item.message }}</p>
          </div>
          <span>{{ item.read ? '已讀' : '未讀' }}</span>
        </button>
      </div>
    </BaseCard>
  </div>
</template>
