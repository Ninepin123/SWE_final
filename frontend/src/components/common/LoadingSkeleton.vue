<template>
  <div class="skeleton-list" :aria-label="label">
    <div v-for="index in rows" :key="index" class="skeleton-row">
      <span />
      <span />
      <span />
    </div>
  </div>
</template>

<script setup>
defineProps({
  rows: {
    type: Number,
    default: 3,
  },
  label: {
    type: String,
    default: '資料載入中',
  },
})
</script>
