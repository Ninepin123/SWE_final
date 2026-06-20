import { defineStore } from 'pinia'

export const useToastStore = defineStore('toast', {
  state: () => ({
    items: [],
  }),
  actions: {
    push(message, type = 'success') {
      const toast = {
        id: `${Date.now()}-${Math.random().toString(16).slice(2, 8)}`,
        message,
        type,
      }
      this.items.push(toast)
      window.setTimeout(() => this.remove(toast.id), 3600)
    },
    success(message) {
      this.push(message, 'success')
    },
    error(message) {
      this.push(message, 'danger')
    },
    warning(message) {
      this.push(message, 'warning')
    },
    info(message) {
      this.push(message, 'info')
    },
    remove(id) {
      this.items = this.items.filter((item) => item.id !== id)
    },
  },
})
