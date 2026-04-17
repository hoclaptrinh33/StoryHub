<script setup lang="ts">
import { ref } from 'vue';

const isOpen = ref(false);
const title = ref('Xác nhận');
const message = ref('Bạn có chắc chắn muốn thực hiện hành động này?');
const resolvePromise = ref<((value: boolean) => void) | null>(null);

const show = (msg: string, t?: string) => {
  message.value = msg;
  if (t) title.value = t;
  isOpen.value = true;
  return new Promise<boolean>((resolve) => {
    resolvePromise.value = resolve;
  });
};

const confirm = () => {
  isOpen.value = false;
  if (resolvePromise.value) resolvePromise.value(true);
};

const cancel = () => {
  isOpen.value = false;
  if (resolvePromise.value) resolvePromise.value(false);
};

defineExpose({ show });
</script>

<template>
  <Teleport to="body">
    <Transition name="fade">
      <div v-if="isOpen" class="confirm-overlay" @click="cancel">
        <Transition name="bounce">
          <div v-if="isOpen" class="confirm-card" @click.stop>
            <div class="confirm-header">
              <span class="material-icons warning-icon">warning_amber</span>
              <h3>{{ title }}</h3>
            </div>
            <div class="confirm-body">
              <p>{{ message }}</p>
            </div>
            <div class="confirm-footer">
              <button class="btn-cancel" @click="cancel">Hủy bỏ</button>
              <button class="btn-confirm" @click="confirm">Đồng ý</button>
            </div>
          </div>
        </Transition>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
/* Giữ nguyên các style cũ của bạn, chỉ thêm/sửa các phần sau */

.confirm-card {
  background: white;
  width: 400px;
  border-radius: 24px;
  padding: 32px;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
  text-align: center;
  /* Đảm bảo icon Material hiển thị đúng */
  display: flex;
  flex-direction: column;
  align-items: center;
}

.confirm-header {
  margin-bottom: 16px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

/* SỬA STYLE CHO ICON MỚI */
.warning-icon {
  font-family: 'Material Icons';
  font-size: 4rem; /* Kích thước icon lớn */
  color: #f59e0b; /* Màu vàng cảnh báo (Amber) */
  display: block;
}

.confirm-header h3 {
  font-size: 1.25rem;
  font-weight: 800;
  color: #1e293b;
  margin: 0;
}

/* Các style khác giữ nguyên như code cũ của bạn */
.confirm-overlay { position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; background: rgba(15, 23, 42, 0.6); backdrop-filter: blur(4px); display: flex; align-items: center; justify-content: center; z-index: 11000; }
.confirm-body p { color: #64748b; font-size: 1rem; line-height: 1.6; margin: 0 0 32px 0; }
.confirm-footer { display: flex; gap: 12px; width: 100%; }
.confirm-footer button { flex: 1; padding: 12px; border-radius: 14px; font-weight: 700; font-size: 0.95rem; cursor: pointer; transition: 0.2s; border: none; }
.btn-cancel { background: #f1f5f9; color: #64748b; }
.btn-cancel:hover { background: #e2e8f0; }
.btn-confirm { background: #ef4444; color: white; }
.btn-confirm:hover { background: #dc2626; transform: translateY(-2px); }
.fade-enter-active, .fade-leave-active { transition: opacity 0.3s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
.bounce-enter-active { animation: bounce-in 0.3s; }
.bounce-leave-active { animation: bounce-in 0.3s reverse; }
@keyframes bounce-in { 0% { transform: scale(0.9); opacity: 0; } 100% { transform: scale(1); opacity: 1; } }
</style>