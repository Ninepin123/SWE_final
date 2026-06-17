<script setup>
import { useRoute } from 'vue-router'
import AppShell from '@/components/common/AppShell.vue'
import ToastHost from '@/components/common/ToastHost.vue'

const route = useRoute()
</script>

<template>
  <RouterView v-if="route.meta.public" />
  <AppShell v-else />
  <ToastHost />
</template>
