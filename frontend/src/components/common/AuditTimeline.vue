<script setup>
import { computed } from 'vue'
import StatusBadge from './StatusBadge.vue'

const props = defineProps({
  logs: {
    type: Array,
    default: () => [],
  },
})

// 依動作性質決定 timeline dot 顏色，讓事件流向更易讀：
// 通過/完成 → success（綠）、未通過 → danger（紅）、補件 → warning（琥珀）、其餘 → info（藍）
function variantOf(log) {
  const text = `${log.action} ${log.result ?? ''} ${log.toStatus ?? ''}`
  if (/通過|APPROVED|完成|SUBMITTED/.test(text)) return 'success'
  if (/未通過|REJECTED|拒絕/.test(text)) return 'danger'
  if (/補件|NEEDS_SUPPLEMENT/.test(text)) return 'warning'
  return 'info'
}

const decorated = computed(() =>
  props.logs.map((log) => ({ ...log, variant: variantOf(log) })),
)

function formatDate(value) {
  if (!value) return '-'
  return new Intl.DateTimeFormat('zh-TW', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(value))
}
</script>

<template>
  <ol class="audit-timeline">
    <li
      v-for="log in decorated"
      :key="log.id"
      class="audit-timeline__item"
      :class="`audit-timeline__item--${log.variant}`"
    >
      <div class="audit-timeline__dot" />
      <div class="audit-timeline__content">
        <div class="audit-timeline__top">
          <strong>{{ log.action }}</strong>
          <time>{{ formatDate(log.createdAt) }}</time>
        </div>
        <div class="audit-timeline__meta">
          <span>{{ log.actorName }} · {{ log.actorRole }}</span>
          <StatusBadge v-if="log.toStatus" :value="log.toStatus" />
        </div>
        <p v-if="log.comment">{{ log.comment }}</p>
      </div>
    </li>
  </ol>
</template>
