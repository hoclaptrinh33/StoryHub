<template>
  <div class="notification-container">
    <transition-group name="list">
      <div v-for="n in notifications" :key="n.id" :class="['toast', n.type]">
        <span class="material-icons">{{ getIconName(n.type) }}</span>
        <span class="message">{{ n.message }}</span>
        <button class="close-btn" @click="remove(n.id)">
          <span class="material-icons">close</span>
        </button>
      </div>
    </transition-group>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';

const notifications = ref<any[]>([]);

const getIconName = (type: string) => {
  switch(type) {
    case 'success': return 'check_circle'; 
    case 'error': return 'error';           
    case 'warning': return 'warning';       
    default: return 'info';
  }
};

const remove = (id: number) => {
  notifications.value = notifications.value.filter(n => n.id !== id);
};

const addNotification = (type: 'success' | 'error' | 'warning' | 'info', message: string) => {
  const id = Date.now();
  notifications.value.push({ id, type, message });
  setTimeout(() => remove(id), 4000); // Auto-close after 4 seconds
};

defineExpose({ addNotification });
</script>

<style scoped>
.notification-container {
  position: fixed;
  top: 24px;
  right: 24px;
  z-index: 10000;
  display: flex;
  flex-direction: column;
  gap: 12px;
  pointer-events: none;
}

.toast {
  pointer-events: auto;
  padding: 16px 20px;
  border-radius: 12px;
  color: white;
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 320px;
  max-width: 450px;
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
  font-family: 'Inter', system-ui, sans-serif;
  font-weight: 500;
}

.success { background: linear-gradient(135deg, #10b981, #059669); }
.error { background: linear-gradient(135deg, #ef4444, #dc2626); }
.warning { background: linear-gradient(135deg, #f59e0b, #d97706); }
.info { background: linear-gradient(135deg, #3b82f6, #2563eb); }

.message { flex: 1; font-size: 0.95rem; line-height: 1.4; }

.material-icons { font-size: 22px; }

.close-btn {
  background: rgba(255, 255, 255, 0.2);
  border: none;
  color: white;
  cursor: pointer;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: 0.2s;
}

.close-btn:hover { background: rgba(255, 255, 255, 0.3); }
.close-btn .material-icons { font-size: 16px; }

/* Transitions */
.list-enter-active, .list-leave-active { transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1); }
.list-enter-from { opacity: 0; transform: translateX(50px) scale(0.9); }
.list-leave-to { opacity: 0; transform: translateX(50px) scale(0.9); }
</style>