<script setup lang="ts">
defineProps<{
  isOpen: boolean,
  title: string, // Thêm prop này
  selectedBook?: any // Có thể bỏ nếu không dùng đến
}>();

defineEmits(['close']);
</script>

<template>
  <Teleport to="body">
    <div v-if="isOpen" class="modal-overlay" @click="$emit('close')">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>{{ title }}</h3> <button class="close-btn" @click="$emit('close')">&times;</button>
        </div>
        <div class="modal-body">
          <slot />
        </div>
        <div class="modal-footer" v-if="$slots.footer">
          <slot name="footer" />
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
/* Overlay làm mờ nền */
.modal-overlay { 
  position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; 
  background: rgba(0, 0, 0, 0.5); display: flex; align-items: center; justify-content: center; 
  z-index: 1000; 
}

/* Nội dung modal */
.modal-content { 
  background: white; width: 1200px; border-radius: 12px; 
  box-shadow: 0 10px 25px rgba(0,0,0,0.2); overflow: hidden;
  display: flex; flex-direction: column;
}

.modal-header {
  padding: 16px 24px; background: #f8fafc; border-bottom: 1px solid #e2e8f0;
  display: flex; justify-content: space-between; align-items: center;
}

.close-btn { background: none; border: none; font-size: 1.5rem; cursor: pointer; color: #64748b; }

.modal-body { padding: 20px; max-height: 400px; overflow-y: auto; }

/* Bảng volume */
.volume-table { width: 100%; border-collapse: collapse; }
.volume-table th { background: #f1f5f9; padding: 12px; text-align: left; font-size: 0.8rem; color: #475569; }
.volume-table td { padding: 12px; border-bottom: 1px solid #f1f5f9; font-size: 0.9rem; }

.modal-footer {
  padding: 16px 24px; border-top: 1px solid #e2e8f0;
  display: flex; justify-content: flex-end; gap: 10px;
}

/* Các button */
.btn-action { padding: 4px 8px; border: none; background: none; cursor: pointer; }
.btn-action:hover { transform: scale(1.2); }

.btn-primary { background: #2563eb; color: white; padding: 8px 16px; border-radius: 6px; border: none; cursor: pointer; }
.btn-primary:hover { background: #1d4ed8; }

.btn-secondary { background: #e2e8f0; color: #475569; padding: 8px 16px; border-radius: 6px; border: none; cursor: pointer; }
</style>