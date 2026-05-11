<template>
  <div class="notification-bell" ref="bellRef">
    <button
      class="bell-trigger"
      :class="{ 'has-critical': hasCritical, 'has-alerts': hasAlerts }"
      @click="togglePanel"
      title="Thông báo hệ thống"
      id="notification-bell-btn"
    >
      <span class="material-icons bell-icon">notifications</span>
      <span
        v-if="badgeCount > 0"
        class="bell-badge"
        :class="{ bounce: justUpdated }"
      >
        {{ badgeCount > 99 ? '99+' : badgeCount }}
      </span>
    </button>

    <Transition name="panel-slide">
      <div v-if="isPanelOpen" class="notification-panel" id="notification-panel">
        <div class="panel-header">
          <h3>
            <span class="material-icons">notifications_active</span>
            Thông báo
          </h3>
          <div class="panel-summary" v-if="summary">
            <span class="summary-chip critical" v-if="summary.critical > 0">
              {{ summary.critical }} khẩn cấp
            </span>
            <span class="summary-chip warning" v-if="summary.warning > 0">
              {{ summary.warning }} cảnh báo
            </span>
            <span class="summary-chip info" v-if="summary.info > 0">
              {{ summary.info }} thông tin
            </span>
            <span class="summary-chip action" v-if="summary.action > 0">
              {{ summary.action }} hành động
            </span>
          </div>
        </div>

        <div class="panel-body" v-if="notifications.length > 0">
          <button
            v-for="item in notifications"
            :key="item.id"
            class="notification-item"
            :class="item.severity"
            @click="handleItemClick(item)"
          >
            <span class="material-icons notif-icon">{{ getIcon(item.type) }}</span>
            <div class="notif-content">
              <span class="notif-title">{{ item.title }}</span>
              <span class="notif-message">{{ item.message }}</span>
              <span class="notif-time">{{ formatTime(item.created_at) }}</span>
            </div>
            <span class="material-icons notif-arrow">chevron_right</span>
          </button>
        </div>

        <div class="panel-empty" v-else>
          <span class="material-icons empty-icon">check_circle</span>
          <p>Không có thông báo nào</p>
          <p class="empty-sub">Hệ thống đang hoạt động bình thường</p>
        </div>

        <div class="panel-footer">
          <span class="footer-status">
            <span class="status-dot" :class="isLoading ? 'loading' : 'connected'"></span>
            {{ isLoading ? 'Đang tải...' : `Cập nhật lúc ${lastFetchTime}` }}
          </span>
          <button class="refresh-btn" @click="refresh" :disabled="isLoading">
            <span class="material-icons" :class="{ spinning: isLoading }">refresh</span>
          </button>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../../stores/auth'
import {
  fetchNotifications,
  type NotificationItem,
  type NotificationSummary,
} from '../../services/storyhubApi'

const router = useRouter()
const authStore = useAuthStore()

const bellRef = ref<HTMLElement | null>(null)
const isPanelOpen = ref(false)
const isLoading = ref(false)
const justUpdated = ref(false)

const notifications = ref<NotificationItem[]>([])
const summary = ref<NotificationSummary | null>(null)
const lastFetchTime = ref('--:--')

let pollTimer: number | null = null
const POLL_INTERVAL_MS = 60_000

// ─── Computed ────────────────────────────────────────────────────────────────

const badgeCount = computed(() => {
  if (!summary.value) return 0
  return summary.value.critical + summary.value.warning
})

const hasCritical = computed(() => (summary.value?.critical ?? 0) > 0)
const hasAlerts = computed(() => badgeCount.value > 0)

// ─── Data Fetching ───────────────────────────────────────────────────────────

async function loadNotifications() {
  const token = authStore.token
  if (!token) return

  isLoading.value = true
  try {
    const payload = await fetchNotifications(token)
    const oldCritical = summary.value?.critical ?? 0
    notifications.value = payload.notifications
    summary.value = payload.summary

    // Trigger bounce if new critical notifications appeared
    if (payload.summary.critical > oldCritical) {
      justUpdated.value = true
      setTimeout(() => { justUpdated.value = false }, 1200)
    }

    const now = new Date()
    lastFetchTime.value = now.toLocaleTimeString('vi-VN', {
      hour: '2-digit',
      minute: '2-digit',
    })
  } catch (err) {
    console.error('[NotificationBell] Fetch failed:', err)
  } finally {
    isLoading.value = false
  }
}

function refresh() {
  void loadNotifications()
}

function startPolling() {
  stopPolling()
  pollTimer = window.setInterval(() => {
    void loadNotifications()
  }, POLL_INTERVAL_MS)
}

function stopPolling() {
  if (pollTimer !== null) {
    window.clearInterval(pollTimer)
    pollTimer = null
  }
}

// ─── Interactions ────────────────────────────────────────────────────────────

function togglePanel() {
  isPanelOpen.value = !isPanelOpen.value
  if (isPanelOpen.value) {
    void loadNotifications()
  }
}

function handleItemClick(item: NotificationItem) {
  isPanelOpen.value = false
  if (item.action_url) {
    void router.push(item.action_url)
  }
}

function handleClickOutside(event: MouseEvent) {
  if (
    bellRef.value &&
    !bellRef.value.contains(event.target as Node)
  ) {
    isPanelOpen.value = false
  }
}

// ─── Formatters ──────────────────────────────────────────────────────────────

function getIcon(type: string): string {
  const map: Record<string, string> = {
    overdue: 'warning',
    due_soon: 'schedule',
    low_stock: 'inventory',
    out_of_stock: 'remove_shopping_cart',
    customer_debt: 'account_balance_wallet',
    reservation_ready: 'bookmark_added',
  }
  return map[type] ?? 'info'
}

function formatTime(isoStr: string): string {
  try {
    const date = new Date(isoStr)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMin = Math.floor(diffMs / 60_000)
    const diffHour = Math.floor(diffMs / 3_600_000)
    const diffDay = Math.floor(diffMs / 86_400_000)

    if (diffMin < 1) return 'Vừa xong'
    if (diffMin < 60) return `${diffMin} phút trước`
    if (diffHour < 24) return `${diffHour} giờ trước`
    if (diffDay < 7) return `${diffDay} ngày trước`

    return date.toLocaleDateString('vi-VN')
  } catch {
    return ''
  }
}

// ─── Lifecycle ───────────────────────────────────────────────────────────────

onMounted(() => {
  void loadNotifications()
  startPolling()
  document.addEventListener('click', handleClickOutside, true)
})

onBeforeUnmount(() => {
  stopPolling()
  document.removeEventListener('click', handleClickOutside, true)
})

// Stop polling when logged out
watch(
  () => authStore.token,
  (newToken) => {
    if (!newToken) {
      stopPolling()
      notifications.value = []
      summary.value = null
    } else {
      void loadNotifications()
      startPolling()
    }
  },
)
</script>

<style scoped>
@import url("https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@500;600;700;800&display=swap");

.notification-bell {
  position: relative;
  font-family: "Plus Jakarta Sans", "Segoe UI", sans-serif;
}

/* ─── Bell Trigger ────────────────────────────────────────────────────────── */

.bell-trigger {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 38px;
  height: 38px;
  border-radius: 50%;
  border: 1px solid #e2e8f0;
  background: #f8fafc;
  cursor: pointer;
  transition: all 0.25s ease;
  padding: 0;
}

.bell-trigger:hover {
  background: #eef2ff;
  border-color: #c7d2fe;
  transform: scale(1.08);
}

.bell-trigger.has-critical {
  animation: pulse-critical 2s ease-in-out infinite;
}

.bell-trigger.has-alerts .bell-icon {
  color: #f59e0b;
}

.bell-icon {
  font-size: 20px;
  color: #64748b;
  transition: color 0.2s;
}

.bell-trigger:hover .bell-icon {
  color: #4f46e5;
}

/* ─── Badge ───────────────────────────────────────────────────────────────── */

.bell-badge {
  position: absolute;
  top: -4px;
  right: -4px;
  min-width: 18px;
  height: 18px;
  padding: 0 5px;
  border-radius: 999px;
  background: linear-gradient(135deg, #ef4444, #dc2626);
  color: white;
  font-size: 10px;
  font-weight: 800;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 6px rgba(239, 68, 68, 0.45);
  line-height: 1;
}

.bell-badge.bounce {
  animation: badge-bounce 0.6s ease;
}

/* ─── Panel ───────────────────────────────────────────────────────────────── */

.notification-panel {
  position: absolute;
  top: calc(100% + 10px);
  right: -8px;
  width: 400px;
  max-height: 520px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(20px) saturate(180%);
  -webkit-backdrop-filter: blur(20px) saturate(180%);
  border: 1px solid rgba(226, 232, 240, 0.7);
  box-shadow:
    0 20px 50px -12px rgba(15, 23, 42, 0.2),
    0 0 0 1px rgba(15, 23, 42, 0.03);
  z-index: 9999;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* ─── Panel Header ────────────────────────────────────────────────────────── */

.panel-header {
  padding: 16px 18px 12px;
  border-bottom: 1px solid rgba(226, 232, 240, 0.6);
}

.panel-header h3 {
  margin: 0 0 10px;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 1rem;
  font-weight: 800;
  color: #0f172a;
  letter-spacing: -0.02em;
}

.panel-header h3 .material-icons {
  font-size: 20px;
  color: #4f46e5;
}

.panel-summary {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.summary-chip {
  display: inline-flex;
  align-items: center;
  padding: 3px 10px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.01em;
}

.summary-chip.critical {
  background: #fef2f2;
  color: #dc2626;
  border: 1px solid #fecaca;
}

.summary-chip.warning {
  background: #fffbeb;
  color: #d97706;
  border: 1px solid #fde68a;
}

.summary-chip.info {
  background: #eff6ff;
  color: #2563eb;
  border: 1px solid #bfdbfe;
}

.summary-chip.action {
  background: #f0fdf4;
  color: #16a34a;
  border: 1px solid #bbf7d0;
}

/* ─── Panel Body ──────────────────────────────────────────────────────────── */

.panel-body {
  flex: 1;
  overflow-y: auto;
  padding: 6px;
  max-height: 360px;
}

.panel-body::-webkit-scrollbar {
  width: 5px;
}

.panel-body::-webkit-scrollbar-track {
  background: transparent;
}

.panel-body::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 999px;
}

/* ─── Notification Item ───────────────────────────────────────────────────── */

.notification-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  width: 100%;
  padding: 12px 14px;
  border: none;
  border-radius: 14px;
  background: transparent;
  cursor: pointer;
  text-align: left;
  transition: all 0.2s ease;
  font-family: inherit;
  margin-bottom: 2px;
}

.notification-item:hover {
  background: rgba(241, 245, 249, 0.8);
  transform: translateX(2px);
}

.notification-item:active {
  transform: scale(0.99);
}

/* Severity left accent */
.notification-item::before {
  content: '';
  position: absolute;
  left: 6px;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 60%;
  border-radius: 3px;
  opacity: 0;
  transition: opacity 0.2s;
}

.notification-item:hover::before {
  opacity: 1;
}

.notif-icon {
  flex-shrink: 0;
  width: 36px;
  height: 36px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
}

.notification-item.critical .notif-icon {
  background: #fef2f2;
  color: #dc2626;
}

.notification-item.warning .notif-icon {
  background: #fffbeb;
  color: #d97706;
}

.notification-item.info .notif-icon {
  background: #eff6ff;
  color: #2563eb;
}

.notification-item.action .notif-icon {
  background: #f0fdf4;
  color: #16a34a;
}

.notif-content {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.notif-title {
  font-size: 13px;
  font-weight: 700;
  color: #0f172a;
  line-height: 1.3;
}

.notif-message {
  font-size: 12px;
  color: #64748b;
  line-height: 1.35;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.notif-time {
  font-size: 10.5px;
  color: #94a3b8;
  font-weight: 600;
  margin-top: 2px;
}

.notif-arrow {
  flex-shrink: 0;
  font-size: 18px;
  color: #cbd5e1;
  align-self: center;
  transition: color 0.2s, transform 0.2s;
}

.notification-item:hover .notif-arrow {
  color: #4f46e5;
  transform: translateX(2px);
}

/* ─── Empty State ─────────────────────────────────────────────────────────── */

.panel-empty {
  padding: 40px 20px;
  text-align: center;
}

.empty-icon {
  font-size: 48px;
  color: #a3e635;
  margin-bottom: 12px;
}

.panel-empty p {
  margin: 0;
  font-size: 14px;
  font-weight: 700;
  color: #334155;
}

.empty-sub {
  margin-top: 4px !important;
  font-size: 12px !important;
  font-weight: 500 !important;
  color: #94a3b8 !important;
}

/* ─── Panel Footer ────────────────────────────────────────────────────────── */

.panel-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 16px;
  border-top: 1px solid rgba(226, 232, 240, 0.6);
  background: rgba(248, 250, 252, 0.6);
}

.footer-status {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  color: #94a3b8;
  font-weight: 600;
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
}

.status-dot.connected {
  background: #22c55e;
  box-shadow: 0 0 6px rgba(34, 197, 94, 0.5);
}

.status-dot.loading {
  background: #f59e0b;
  animation: dot-pulse 1s ease infinite;
}

.refresh-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
  background: white;
  cursor: pointer;
  padding: 0;
  transition: all 0.2s;
}

.refresh-btn:hover:not(:disabled) {
  background: #eef2ff;
  border-color: #c7d2fe;
}

.refresh-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.refresh-btn .material-icons {
  font-size: 16px;
  color: #64748b;
}

.refresh-btn .material-icons.spinning {
  animation: spin 1s linear infinite;
}

/* ─── Transition ──────────────────────────────────────────────────────────── */

.panel-slide-enter-active {
  transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}

.panel-slide-leave-active {
  transition: all 0.2s ease-in;
}

.panel-slide-enter-from {
  opacity: 0;
  transform: translateY(-10px) scale(0.96);
}

.panel-slide-leave-to {
  opacity: 0;
  transform: translateY(-6px) scale(0.98);
}

/* ─── Animations ──────────────────────────────────────────────────────────── */

@keyframes pulse-critical {
  0%, 100% {
    box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.35);
  }
  50% {
    box-shadow: 0 0 0 8px rgba(239, 68, 68, 0);
  }
}

@keyframes badge-bounce {
  0%, 100% { transform: scale(1); }
  30% { transform: scale(1.35); }
  60% { transform: scale(0.9); }
  80% { transform: scale(1.1); }
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

@keyframes dot-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

/* ─── Responsive ──────────────────────────────────────────────────────────── */

@media (max-width: 480px) {
  .notification-panel {
    width: calc(100vw - 32px);
    right: -60px;
  }
}
</style>
