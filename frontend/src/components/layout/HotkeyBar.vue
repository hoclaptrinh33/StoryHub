<template>
  <div class="hotkey-bar" role="status" aria-live="polite">
    <div v-for="item in items" :key="item.key" class="hotkey-item">
      <kbd>{{ item.key }}</kbd>
      <span>{{ item.label }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
export interface HotkeyItem {
  key: string;
  label: string;
}

defineProps<{
  items: HotkeyItem[];
}>();
</script>

<style scoped>
.hotkey-bar {
  position: sticky;
  bottom: 0;
  z-index: 30;
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  padding: 10px 14px;
  border-radius: 14px 14px 0 0;
  border: 1px solid #d4d4d8;
  border-bottom: none;
  background: linear-gradient(90deg, #fafaf9 0%, #f5f5f4 100%);
  box-shadow: 0 -10px 24px rgba(0, 0, 0, 0.08);
}

.hotkey-item {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px;
  border-radius: 10px;
  background: white;
  border: 1px solid #e7e5e4;
  color: #44403c;
  font-size: 0.85rem;
  font-weight: 700;
}

kbd {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 34px;
  padding: 4px 8px;
  border: 1px solid #a8a29e;
  border-radius: 8px;
  background: #fafaf9;
  color: #1c1917;
  font-family: "Plus Jakarta Sans", "Segoe UI", sans-serif;
  font-size: 0.78rem;
}

@media (max-width: 768px) {
  .hotkey-bar {
    gap: 8px;
    padding: 8px 10px;
    border-radius: 10px 10px 0 0;
  }

  .hotkey-item {
    padding: 5px 8px;
    font-size: 0.78rem;
  }

  kbd {
    min-width: 28px;
    padding: 3px 6px;
    font-size: 0.72rem;
  }
}
</style>
