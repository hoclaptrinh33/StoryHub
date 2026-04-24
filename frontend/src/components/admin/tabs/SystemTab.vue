<template>
  <section class="tab-shell">
    <button class="mobile-toggle" @click="leftOpen = !leftOpen">
      {{ leftOpen ? 'Ẩn điều khiển' : 'Hiện điều khiển' }}
    </button>

    <div class="tab-split">
      <aside class="left-panel" :class="{ open: leftOpen }">
        <div class="panel-card">
          <h3>Điều khiển Sao lưu</h3>
          <button class="btn-warn" :disabled="isBusy('trigger-backup')" @click="triggerBackupNow">
            {{ isBusy('trigger-backup') ? 'Đang chạy...' : 'Chạy sao lưu ngay' }}
          </button>
          <button class="btn-ghost" :disabled="isBusy('load-system')" @click="loadSystemData">
            {{ isBusy('load-system') ? 'Đang tải...' : 'Tải lại trạng thái' }}
          </button>
          <p v-if="errorMap['trigger-backup']" class="error-text">{{ errorMap['trigger-backup'] }}</p>
          <p v-if="errorMap['load-system']" class="error-text">{{ errorMap['load-system'] }}</p>
        </div>

        <div class="panel-card">
          <h3>Sao lưu mới nhất</h3>
          <p class="stat-line">Trạng thái: <strong>{{ latestBackup?.status || 'N/A' }}</strong></p>
          <p class="stat-line">Loại: <strong>{{ latestBackup?.backup_type || 'N/A' }}</strong></p>
          <p class="stat-line">Ngày tạo: <strong>{{ latestBackup ? formatDate(latestBackup.created_at) : 'N/A' }}</strong></p>
        </div>
      </aside>

      <div class="right-panel">
        <article class="panel-card">
          <div class="card-head">
            <h3>Cấu hình Hệ thống</h3>
            <span class="pill">chỉ dành cho chủ sở hữu</span>
          </div>

          <div class="form-grid">
            <div>
              <label class="field-label">Tên cửa hàng</label>
              <input v-model="configForm.shop_name" class="field-input" />
            </div>
            <div>
              <label class="field-label">Số điện thoại</label>
              <input v-model="configForm.shop_phone" class="field-input" />
            </div>
            <div class="full-width">
              <label class="field-label">Địa chỉ</label>
              <input v-model="configForm.shop_address" class="field-input" />
            </div>
            <div class="full-width">
              <label class="field-label">Thông báo chân hóa đơn</label>
              <textarea v-model="configForm.bill_footer" class="field-input" rows="2" />
            </div>
            <div>
              <label class="field-label">Tiền phạt mỗi ngày (quá hạn)</label>
              <input v-model.number="configForm.penalty_per_day" class="field-input" type="number" min="0" />
            </div>
          </div>

          <div class="form-actions">
            <button class="btn-primary" :disabled="isBusy('save-config')" @click="saveSystemConfig">
              {{ isBusy('save-config') ? 'Đang lưu...' : 'Lưu cấu hình' }}
            </button>
          </div>
          <p v-if="errorMap['save-config']" class="error-text">{{ errorMap['save-config'] }}</p>
        </article>

        <article v-if="latestBackup" class="panel-card">
          <h3>Chi tiết Sao lưu</h3>
          <p class="stat-line">Đường dẫn: {{ latestBackup.file_path || 'N/A' }}</p>
          <p class="stat-line">Mã kiểm tra: {{ latestBackup.checksum || 'N/A' }}</p>
          <p class="stat-line">Lỗi: {{ latestBackup.error_message || 'Không có' }}</p>
          <p class="stat-line">Bắt đầu: {{ latestBackup.started_at ? formatDate(latestBackup.started_at) : 'N/A' }}</p>
          <p class="stat-line">Hoàn thành: {{ latestBackup.finished_at ? formatDate(latestBackup.finished_at) : 'N/A' }}</p>
        </article>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref, watch } from 'vue';
import { StoryHubApiError } from '../../../services/storyhubApi';
import type { LatestBackupPayload } from '../../../services/storyhubApi';
import { useAdminApi } from '../../../composables/useAdminApi';

type ActionKey = 'load-system' | 'save-config' | 'trigger-backup';

type KpiPayload = {
  primaryLabel: string;
  primaryValue: string;
  secondaryLabel: string;
  secondaryValue: string;
};

const props = defineProps<{ isActive: boolean }>();

const emit = defineEmits<{
  (e: 'notify', payload: { type: 'success' | 'error'; message: string }): void;
  (e: 'kpi', payload: KpiPayload): void;
}>();

const adminApi = useAdminApi();

const initialized = ref(false);
const leftOpen = ref(false);

const latestBackup = ref<LatestBackupPayload | null>(null);

const configForm = reactive({
  shop_name: '',
  shop_address: '',
  shop_phone: '',
  bill_footer: '',
  penalty_per_day: 0,
});

const loadingMap = reactive<Record<ActionKey, boolean>>({
  'load-system': false,
  'save-config': false,
  'trigger-backup': false,
});

const errorMap = reactive<Record<ActionKey, string | null>>({
  'load-system': null,
  'save-config': null,
  'trigger-backup': null,
});

onMounted(() => {
  if (props.isActive) {
    initialized.value = true;
    void loadSystemData();
  }
});

watch(
  () => props.isActive,
  (isActive) => {
    if (isActive && !initialized.value) {
      initialized.value = true;
      void loadSystemData();
    }
  },
);

watch(
  () => [configForm.shop_name, latestBackup.value?.status],
  () => {
    emit('kpi', {
      primaryLabel: 'Cửa hàng',
      primaryValue: configForm.shop_name || 'N/A',
      secondaryLabel: 'Trạng thái sao lưu',
      secondaryValue: latestBackup.value?.status || 'không xác định',
    });
  },
  { immediate: true },
);

function isBusy(key: ActionKey) {
  return loadingMap[key];
}

function mapError(error: unknown) {
  if (error instanceof StoryHubApiError) {
    // Xử lý lỗi quyền truy cập rõ ràng
    if (error.status === 403) {
      return 'Không có quyền thực hiện thao tác này. Vui lòng đăng nhập lại với tài khoản chủ sở hữu.';
    }
    if (error.status === 401) {
      return 'Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.';
    }
    return error.message;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return 'Lỗi không xác định. Vui lòng thử lại.';
}

async function runAction<T>(key: ActionKey, work: () => Promise<T>) {
  loadingMap[key] = true;
  errorMap[key] = null;

  try {
    return await work();
  } catch (error) {
    const message = mapError(error);
    errorMap[key] = message;
    emit('notify', { type: 'error', message });
    return undefined;
  } finally {
    loadingMap[key] = false;
  }
}

async function loadSystemData() {
  await runAction('load-system', async () => {
    const [config, backup] = await Promise.all([
      adminApi.fetchSystemConfig(),
      adminApi.fetchLatestBackup(),
    ]);

    configForm.shop_name = config.shop_name || '';
    configForm.shop_address = config.shop_address || '';
    configForm.shop_phone = config.shop_phone || '';
    configForm.bill_footer = config.bill_footer || '';
    configForm.penalty_per_day = Number(config.penalty_per_day || 0);

    latestBackup.value = backup;
  });
}

async function saveSystemConfig() {
  await runAction('save-config', async () => {
    await adminApi.updateSystemConfig({
      shop_name: configForm.shop_name,
      shop_address: configForm.shop_address,
      shop_phone: configForm.shop_phone,
      bill_footer: configForm.bill_footer,
      penalty_per_day: String(configForm.penalty_per_day),
    });

    emit('notify', { type: 'success', message: 'Đã cập nhật cấu hình hệ thống.' });
  });
}

async function triggerBackupNow() {
  await runAction('trigger-backup', async () => {
    await adminApi.triggerBackup();
    emit('notify', { type: 'success', message: 'Đã bắt đầu tiến trình sao lưu.' });
    await loadSystemData();
  });
}

function formatDate(value: string) {
  return new Date(value).toLocaleString('vi-VN');
}
</script>

<style scoped>
.tab-shell {
  width: 100%;
}

.mobile-toggle {
  display: none;
  margin-bottom: 12px;
  border: 1px solid #cbd5e1;
  background: #ffffff;
  color: #0f172a;
  border-radius: 12px;
  padding: 8px 12px;
  font-weight: 600;
}

.tab-split {
  display: grid;
  grid-template-columns: 320px minmax(0, 1fr);
  gap: 16px;
}

.left-panel,
.right-panel {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.panel-card {
  border: 1px solid #dbe4f0;
  background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
  border-radius: 16px;
  padding: 16px;
}

.card-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.card-head h3,
.panel-card h3 {
  margin: 0;
  font-size: 16px;
  color: #0f172a;
}

.field-label {
  display: block;
  font-size: 12px;
  font-weight: 700;
  color: #334155;
  margin: 8px 0 6px;
}

.field-input {
  width: 100%;
  border: 1px solid #cbd5e1;
  background: #ffffff;
  border-radius: 10px;
  padding: 9px 10px;
  font-size: 14px;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.full-width {
  grid-column: 1 / -1;
}

.form-actions {
  margin-top: 14px;
}

.stat-line {
  margin: 8px 0;
  color: #334155;
  word-break: break-word;
}

.btn-primary,
.btn-ghost,
.btn-warn {
  border: none;
  border-radius: 10px;
  padding: 9px 12px;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
}

.btn-primary {
  background: #2563eb;
  color: #ffffff;
}

.btn-ghost {
  background: #e2e8f0;
  color: #0f172a;
  margin-top: 8px;
}

.btn-warn {
  background: #c2410c;
  color: #ffffff;
}

.btn-primary:disabled,
.btn-ghost:disabled,
.btn-warn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.pill {
  display: inline-flex;
  align-items: center;
  border-radius: 999px;
  padding: 4px 10px;
  font-size: 11px;
  font-weight: 700;
  background: #e2e8f0;
  color: #0f172a;
}

.error-text {
  margin-top: 8px;
  color: #b91c1c;
  font-size: 12px;
}

@media (max-width: 1024px) {
  .mobile-toggle {
    display: inline-flex;
  }

  .tab-split {
    grid-template-columns: 1fr;
  }

  .left-panel {
    display: none;
  }

  .left-panel.open {
    display: flex;
  }

  .form-grid {
    grid-template-columns: 1fr;
  }
}
</style>
