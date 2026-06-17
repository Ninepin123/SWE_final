<script setup>
defineProps({
  steps: {
    type: Array,
    required: true,
  },
  current: {
    type: Number,
    required: true,
  },
})
</script>

<template>
  <nav class="stepper" aria-label="申請步驟">
    <div
      v-for="(step, index) in steps"
      :key="step"
      class="stepper__item"
      :class="{
        'stepper__item--active': index === current,
        'stepper__item--done': index < current,
      }"
    >
      <span>{{ index + 1 }}</span>
      <strong>{{ step }}</strong>
    </div>
  </nav>
</template>
