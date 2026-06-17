<script setup>
// 輕量 inline SVG icon 系統（stroke-based，lucide 風格）。
// 用法：<Icon name="home" />，尺寸由父層 .icon CSS 控制（預設 18px）。
// 路徑表放在獨立模組 icons.js，避免 defineProps 引用外部變數的編譯限制。
import { ICON_PATHS, ICON_NAMES } from './icons'

defineProps({
  name: {
    type: String,
    required: true,
    validator: (value) => ICON_NAMES.includes(value),
  },
})
</script>

<template>
  <svg
    class="icon"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="1.8"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
  >
    <path :d="ICON_PATHS[name]" />
  </svg>
</template>
