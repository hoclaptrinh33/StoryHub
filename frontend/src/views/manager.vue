<template>
  <DefaultLayout>
    <div class="manager-shell">
      <header class="manager-hero">
        <div>
          <p class="eyebrow">Bảng điều khiển Chủ sở hữu StoryHub</p>
          <h1>Trung tâm Quản lý</h1>
          <p class="hero-subtitle">
            Một điểm đến duy nhất cho Dữ liệu & Kiểm tra, Khuyến mãi, Nhân sự & Quyền hạn, Giá cả, Hệ thống & Sao lưu.
          </p>
        </div>
        <span class="owner-badge">
          <span class="material-icons" aria-hidden="true">verified_user</span>
          chỉ dành cho chủ sở hữu
        </span>
      </header>

      <section class="kpi-strip">
        <article class="kpi-card">
          <p class="kpi-label">{{ currentKpi.primaryLabel }}</p>
          <p class="kpi-value">{{ currentKpi.primaryValue }}</p>
        </article>
        <article class="kpi-card alt">
          <p class="kpi-label">{{ currentKpi.secondaryLabel }}</p>
          <p class="kpi-value">{{ currentKpi.secondaryValue }}</p>
        </article>
      </section>

      <nav class="tab-strip" aria-label="Admin tabs">
        <button
          v-for="tab in tabs"
          :key="tab.id"
          class="tab-button"
          :class="{ active: activeTab === tab.id }"
          @click="activeTab = tab.id"
        >
          <span class="material-icons" aria-hidden="true">{{ tab.icon }}</span>
          {{ tab.label }}
        </button>
      </nav>

      <section class="tab-host">
        <DataAuditTab
          v-show="activeTab === 'data-audit'"
          :is-active="activeTab === 'data-audit'"
          @notify="handleNotify"
          @kpi="updateKpi('data-audit', $event)"
        />

        <PromotionsTab
          v-show="activeTab === 'promotions'"
          :is-active="activeTab === 'promotions'"
          @notify="handleNotify"
          @kpi="updateKpi('promotions', $event)"
        />

        <HrRbacTab
          v-show="activeTab === 'hr-rbac'"
          :is-active="activeTab === 'hr-rbac'"
          @notify="handleNotify"
          @kpi="updateKpi('hr-rbac', $event)"
        />

        <PricingTab
          v-show="activeTab === 'pricing'"
          :is-active="activeTab === 'pricing'"
          @notify="handleNotify"
          @kpi="updateKpi('pricing', $event)"
        />

        <SystemTab
          v-show="activeTab === 'system-backup'"
          :is-active="activeTab === 'system-backup'"
          @notify="handleNotify"
          @kpi="updateKpi('system-backup', $event)"
        />
      </section>

      <transition name="toast-fade">
        <aside v-if="toast.visible" class="toast" :class="toast.type">
          <span class="material-icons" aria-hidden="true">
            {{ toast.type === 'success' ? 'check_circle' : 'error' }}
          </span>
          {{ toast.message }}
        </aside>
      </transition>
    </div>
  </DefaultLayout>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue';
import { useRouter } from 'vue-router';
import DefaultLayout from '../components/layout/defaultLayout.vue';
import DataAuditTab from '../components/admin/tabs/DataAuditTab.vue';
import PromotionsTab from '../components/admin/tabs/PromotionsTab.vue';
import HrRbacTab from '../components/admin/tabs/HrRbacTab.vue';
import PricingTab from '../components/admin/tabs/PricingTab.vue';
import SystemTab from '../components/admin/tabs/SystemTab.vue';
import { useAuthStore } from '../stores/auth';

type TabId = 'data-audit' | 'promotions' | 'hr-rbac' | 'pricing' | 'system-backup';

type KpiPayload = {
  primaryLabel: string;
  primaryValue: string;
  secondaryLabel: string;
  secondaryValue: string;
};

const router = useRouter();
const authStore = useAuthStore();

const tabs: Array<{ id: TabId; label: string; icon: string }> = [
  { id: 'data-audit', label: 'Dữ liệu & Kiểm tra', icon: 'monitoring' },
  { id: 'promotions', label: 'Khuyến mãi', icon: 'local_offer' },
  { id: 'hr-rbac', label: 'Nhân sự & Quyền hạn', icon: 'badge' },
  { id: 'pricing', label: 'Bảng giá', icon: 'paid' },
  { id: 'system-backup', label: 'Hệ thống & Sao lưu', icon: 'settings_backup_restore' },
];

const activeTab = ref<TabId>('data-audit');

const tabKpis = reactive<Record<TabId, KpiPayload>>({
  'data-audit': {
    primaryLabel: 'Khách hàng',
    primaryValue: '0',
    secondaryLabel: 'Danh sách đen',
    secondaryValue: '0',
  },
  promotions: {
    primaryLabel: 'Mã giảm giá',
    primaryValue: '0',
    secondaryLabel: 'Khuyến mãi tự động',
    secondaryValue: '0',
  },
  'hr-rbac': {
    primaryLabel: 'Người dùng',
    primaryValue: '0',
    secondaryLabel: 'Đang hoạt động',
    secondaryValue: '0',
  },
  pricing: {
    primaryLabel: 'Phiên bản quy tắc',
    primaryValue: '0',
    secondaryLabel: 'hệ số thuê',
    secondaryValue: '0',
  },
  'system-backup': {
    primaryLabel: 'Cửa hàng',
    primaryValue: 'N/A',
    secondaryLabel: 'Trạng thái sao lưu',
    secondaryValue: 'không xác định',
  },
});

const currentKpi = computed(() => tabKpis[activeTab.value]);

const toast = reactive({
  visible: false,
  type: 'success' as 'success' | 'error',
  message: '',
  timeoutId: 0,
});

onMounted(() => {
  enforceOwnerAccess();
});

watch(
  () => [authStore.isAuthenticated, authStore.user?.role],
  () => {
    enforceOwnerAccess();
  },
);

function enforceOwnerAccess() {
  if (!authStore.isAuthenticated) {
    router.replace('/login');
    return;
  }

  if (authStore.user?.role !== 'owner') {
    router.replace('/');
  }
}

function updateKpi(tabId: TabId, payload: KpiPayload) {
  tabKpis[tabId] = payload;
}

function handleNotify(payload: { type: 'success' | 'error'; message: string }) {
  if (toast.timeoutId) {
    window.clearTimeout(toast.timeoutId);
  }

  toast.type = payload.type;
  toast.message = payload.message;
  toast.visible = true;

  toast.timeoutId = window.setTimeout(() => {
    toast.visible = false;
  }, 3000);
}
</script>

<style scoped>
.manager-shell {
  --shell-bg-1: #f7fbff;
  --shell-bg-2: #fefce8;
  --shell-line: #dbe4f0;
  --shell-ink: #0f172a;
  --shell-muted: #475569;
  --shell-brand: #0f172a;
  --shell-brand-alt: #9a3412;

  min-height: 100vh;
  padding: 24px;
  background:
    radial-gradient(circle at 0% 0%, rgba(59, 130, 246, 0.12), transparent 40%),
    radial-gradient(circle at 100% 100%, rgba(234, 179, 8, 0.14), transparent 45%),
    linear-gradient(140deg, var(--shell-bg-1) 0%, var(--shell-bg-2) 100%);
  color: var(--shell-ink);
}

.manager-hero {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 16px;
}

.eyebrow {
  margin: 0;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  font-size: 12px;
  font-weight: 700;
  color: var(--shell-muted);
}

.manager-hero h1 {
  margin: 8px 0;
  font-size: clamp(1.7rem, 3vw, 2.6rem);
  line-height: 1.1;
}

.hero-subtitle {
  margin: 0;
  max-width: 760px;
  color: var(--shell-muted);
}

.owner-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  border-radius: 999px;
  border: 1px solid #cbd5e1;
  background: #ffffff;
  padding: 8px 14px;
  font-weight: 700;
  white-space: nowrap;
}

.kpi-strip {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 16px;
}

.kpi-card {
  border: 1px solid var(--shell-line);
  border-radius: 16px;
  padding: 14px;
  background: #ffffff;
}

.kpi-card.alt {
  background: linear-gradient(120deg, #ffffff 0%, #fef3c7 100%);
}

.kpi-label {
  margin: 0;
  font-size: 12px;
  color: var(--shell-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.kpi-value {
  margin: 8px 0 0;
  font-size: clamp(1.2rem, 2.5vw, 1.9rem);
  font-weight: 800;
}

.tab-strip {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  margin-bottom: 16px;
}

.tab-button {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  border: 1px solid var(--shell-line);
  border-radius: 12px;
  background: #ffffff;
  padding: 10px 14px;
  font-weight: 700;
  color: #334155;
  cursor: pointer;
}

.tab-button.active {
  border-color: #2563eb;
  background: #2563eb;
  color: #ffffff;
}

.tab-host {
  min-height: 540px;
}

.toast {
  position: fixed;
  right: 20px;
  bottom: 20px;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  border-radius: 12px;
  border: 1px solid #cbd5e1;
  padding: 10px 14px;
  font-weight: 700;
  z-index: 2050;
}

.toast.success {
  background: #dcfce7;
  color: #166534;
}

.toast.error {
  background: #fee2e2;
  color: #991b1b;
}

.toast-fade-enter-active,
.toast-fade-leave-active {
  transition: opacity 0.2s ease;
}

.toast-fade-enter-from,
.toast-fade-leave-to {
  opacity: 0;
}

@media (max-width: 900px) {
  .manager-shell {
    padding: 16px;
  }

  .manager-hero {
    flex-direction: column;
  }

  .kpi-strip {
    grid-template-columns: 1fr;
  }

  .tab-strip {
    overflow-x: auto;
    flex-wrap: nowrap;
    padding-bottom: 4px;
  }

  .tab-button {
    white-space: nowrap;
  }
}
</style>
