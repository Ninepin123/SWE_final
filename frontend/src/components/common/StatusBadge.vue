<script setup>
import { computed } from 'vue'
import {
  APPLICATION_STATUS,
  RECOMMENDATION_STATUS,
  SCHOLARSHIP_STATUS,
} from '@/services/mockBackend'

const props = defineProps({
  value: {
    type: String,
    required: true,
  },
})

const meta = computed(() => {
  const labels = {
    ...APPLICATION_STATUS,
    ...RECOMMENDATION_STATUS,
    ...SCHOLARSHIP_STATUS,
    ACTIVE: '啟用',
    DISABLED: '停用',
  }

  const variants = {
    OPEN: 'success',
    ACTIVE: 'success',
    APPROVED: 'success',
    SUBMITTED: 'success',
    UNDER_REVIEW: 'info',
    PENDING: 'warning',
    REMINDED: 'warning',
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
