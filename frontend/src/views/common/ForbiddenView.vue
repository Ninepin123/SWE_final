<script setup>
import { RouterLink } from 'vue-router'
import BaseCard from '@/components/common/BaseCard.vue'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
</script>

<template>
  <BaseCard title="沒有權限" eyebrow="Access Control">
    <div class="empty-state empty-state--inline">
      <div class="empty-state__mark">禁</div>
      <h3>這個功能不屬於目前角色</h3>
      <p>
        目前登入角色是 {{ auth.roleLabel }}。請回到總覽，或切換為具備權限的測試角色。
      </p>
      <RouterLink class="primary-button" to="/dashboard">回到總覽</RouterLink>
    </div>
  </BaseCard>
</template>
