<script setup>
import { useToastStore } from '@/stores/toast'

const toast = useToastStore()
</script>

<template>
  <div class="toast-host" aria-live="polite">
    <button
      v-for="item in toast.items"
      :key="item.id"
      type="button"
      class="toast"
      :class="`toast--${item.type}`"
      @click="toast.remove(item.id)"
    >
      {{ item.message }}
    </button>
  </div>
</template>
