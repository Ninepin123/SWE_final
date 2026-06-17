<script setup>
import Icon from '@/components/common/Icon.vue'

defineProps({
  title: {
    type: String,
    required: true,
  },
  description: {
    type: String,
    required: true,
  },
  icon: {
    type: String,
    default: 'inbox',
  },
})
</script>

<template>
  <div class="empty-state">
    <div class="empty-state__mark">
      <Icon :name="icon" />
    </div>
    <h3>{{ title }}</h3>
    <p>{{ description }}</p>
    <slot />
  </div>
</template>
