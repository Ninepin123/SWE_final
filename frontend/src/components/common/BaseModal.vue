<script setup>
import Icon from '@/components/common/Icon.vue'

defineProps({
  show: {
    type: Boolean,
    default: false,
  },
  title: {
    type: String,
    default: '',
  },
  width: {
    type: String,
    default: '720px',
  },
})

defineEmits(['close'])
</script>

<template>
  <Teleport to="body">
    <div v-if="show" class="modal-backdrop" @mousedown.self="$emit('close')">
      <section class="modal-panel" :style="{ maxWidth: width }">
        <header class="modal-panel__header">
          <h2>{{ title }}</h2>
          <button class="icon-button" type="button" aria-label="關閉" @click="$emit('close')">
            <Icon name="close" />
          </button>
        </header>
        <div class="modal-panel__body">
          <slot />
        </div>
        <footer v-if="$slots.footer" class="modal-panel__footer">
          <slot name="footer" />
        </footer>
      </section>
    </div>
  </Teleport>
</template>
