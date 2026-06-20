<template>
  <section class="card" :class="{ 'card--flush': flush }">
    <div v-if="$slots.header || title" class="card__header">
      <div class="card__title-group">
        <p v-if="eyebrow" class="eyebrow">{{ eyebrow }}</p>
        <h2 v-if="title">{{ title }}</h2>
      </div>
      <slot name="actions" />
    </div>
    <slot />
  </section>
</template>

<script setup>
defineProps({
  title: {
    type: String,
    default: '',
  },
  eyebrow: {
    type: String,
    default: '',
  },
  flush: {
    type: Boolean,
    default: false,
  },
})
</script>
