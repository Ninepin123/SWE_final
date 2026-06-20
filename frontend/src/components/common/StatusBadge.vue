<script setup>
import { computed } from 'vue'

const props = defineProps({
  value: {
    type: String,
    required: true,
  },
})

const meta = computed(() => {
  const labels = {
    SUBMITTED: '已送出',
    UNDER_REVIEW: '審查中',
    NEED_SUPPLEMENT: '需補件',
    NEEDS_SUPPLEMENT: '需補件',
    APPROVED: '已通過',
    REJECTED: '未通過',
    REQUESTED: '已邀請',
    PENDING: '等待填寫',
    REMINDED: '已提醒',
    OPEN: '開放申請',
    CLOSED: '已截止',
    DRAFT: '草稿',
    ACTIVE: '啟用',
    DISABLED: '停用',
  }

  const variants = {
    OPEN: 'success',
    ACTIVE: 'success',
    APPROVED: 'success',
    SUBMITTED: 'success',
    UNDER_REVIEW: 'info',
    REQUESTED: 'warning',
    PENDING: 'warning',
    REMINDED: 'warning',
    NEED_SUPPLEMENT: 'warning',
    NEEDS_SUPPLEMENT: 'warning',
    REJECTED: 'danger',
    CLOSED: 'muted',
    DRAFT: 'muted',
    DISABLED: 'muted',
  }

  return {
    label: labels[props.value] ?? props.value,
    variant: variants[props.value] ?? 'info',
  }
})
</script>

<template>
  <span class="status-badge" :class="`status-badge--${meta.variant}`">
    {{ meta.label }}
  </span>
</template>
