<template>
  <div class="category-tag-management-view">
    <h1 class="page-title">分類與標籤管理</h1>
    
    <div class="management-grid">
      <!-- Categories -->
      <section class="management-section">
        <div class="section-header">
          <h2>分類 (Categories)</h2>
          <button class="btn btn--primary" @click="openModal('CATEGORY')">新增分類</button>
        </div>
        
        <div class="table-container">
          <table class="data-table">
            <thead>
              <tr>
                <th>分類名稱</th>
                <th width="150">操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="cat in categories" :key="cat.id">
                <td>{{ cat.name }}</td>
                <td>
                  <button class="btn btn--sm" @click="openModal('CATEGORY', cat)">編輯</button>
                  <button class="btn btn--sm btn--danger" @click="handleDelete(cat.id)">刪除</button>
                </td>
              </tr>
              <tr v-if="categories.length === 0">
                <td colspan="2" class="text-center text-muted">目前沒有分類資料</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
      
      <!-- Tags -->
      <section class="management-section">
        <div class="section-header">
          <h2>標籤 (Tags)</h2>
          <button class="btn btn--primary" @click="openModal('TAG')">新增標籤</button>
        </div>
        
        <div class="table-container">
          <table class="data-table">
            <thead>
              <tr>
                <th>標籤名稱</th>
                <th width="150">操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="tag in tags" :key="tag.id">
                <td>{{ tag.name }}</td>
                <td>
                  <button class="btn btn--sm" @click="openModal('TAG', tag)">編輯</button>
                  <button class="btn btn--sm btn--danger" @click="handleDelete(tag.id)">刪除</button>
                </td>
              </tr>
              <tr v-if="tags.length === 0">
                <td colspan="2" class="text-center text-muted">目前沒有標籤資料</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </div>

    <!-- Modal -->
    <div v-if="showModal" class="modal-overlay" @click.self="closeModal">
      <div class="modal">
        <h3 class="modal__title">{{ editData.id ? '編輯' : '新增' }}{{ editData.type === 'CATEGORY' ? '分類' : '標籤' }}</h3>
        
        <div class="modal__body">
          <label>
            <span>名稱</span>
            <input v-model="editData.name" type="text" placeholder="輸入名稱" />
          </label>
          <div v-if="error" class="error-msg">{{ error }}</div>
        </div>
        
        <div class="modal__actions">
          <button class="btn btn--secondary" @click="closeModal">取消</button>
          <button class="btn btn--primary" @click="saveOption">儲存</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { getOptions, createOption, updateOption, deleteOption } from '@/api/sms'

const options = ref([])
const error = ref('')

const categories = computed(() => options.value.filter(o => o.type === 'CATEGORY'))
const tags = computed(() => options.value.filter(o => o.type === 'TAG'))

const showModal = ref(false)
const editData = ref({ id: null, type: '', name: '' })

const fetchOptions = async () => {
  try {
    const res = await getOptions()
    options.value = res
  } catch (err) {
    console.error(err)
  }
}

const openModal = (type, item = null) => {
  error.value = ''
  if (item) {
    editData.value = { ...item }
  } else {
    editData.value = { id: null, type, name: '' }
  }
  showModal.value = true
}

const closeModal = () => {
  showModal.value = false
}

const saveOption = async () => {
  if (!editData.value.name.trim()) {
    error.value = '名稱不可為空'
    return
  }
  
  try {
    if (editData.value.id) {
      await updateOption(editData.value.id, {
        type: editData.value.type,
        name: editData.value.name.trim()
      })
    } else {
      await createOption({
        type: editData.value.type,
        name: editData.value.name.trim()
      })
    }
    await fetchOptions()
    closeModal()
  } catch (err) {
    error.value = err.response?.data?.detail || '儲存失敗'
  }
}

const handleDelete = async (id) => {
  if (!confirm('確定要刪除此選項嗎？')) return
  
  try {
    await deleteOption(id)
    await fetchOptions()
  } catch (err) {
    alert(err.response?.data?.detail || '刪除失敗')
  }
}

onMounted(() => {
  fetchOptions()
})
</script>

<style scoped>
.category-tag-management-view {
  padding: var(--spacing-lg);
}

.management-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--spacing-xl);
  margin-top: var(--spacing-lg);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-md);
}

.section-header h2 {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--color-gray-800);
}

.table-container {
  background: white;
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-sm);
  overflow: hidden;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table th,
.data-table td {
  padding: var(--spacing-md);
  text-align: left;
  border-bottom: 1px solid var(--color-gray-200);
}

.data-table th {
  background: var(--color-gray-50);
  font-weight: 500;
  color: var(--color-gray-600);
}

.data-table td .btn {
  margin-right: var(--spacing-xs);
}

.error-msg {
  color: var(--color-danger);
  margin-top: var(--spacing-sm);
  font-size: 0.875rem;
}

@media (max-width: 768px) {
  .management-grid {
    grid-template-columns: 1fr;
  }
}
</style>
