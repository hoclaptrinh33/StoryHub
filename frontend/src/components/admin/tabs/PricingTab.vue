<template>
  <section class="tab-shell">
    <button class="mobile-toggle" @click="leftOpen = !leftOpen">
      {{ leftOpen ? 'Ẩn bộ lọc' : 'Hiện bộ lọc' }}
    </button>

    <div class="tab-split">
      <aside class="left-panel" :class="{ open: leftOpen }">
        <div class="panel-card">
          <h3>Cập nhật giá hàng loạt</h3>

          <label class="field-label">Phần trăm thay đổi (%)</label>
          <input v-model.number="bulkForm.percent_delta" class="field-input" type="number" step="0.1" />

          <label class="field-label">Lý do (bắt buộc)</label>
          <textarea v-model="bulkForm.reason" class="field-input" rows="3" />

          <button
            class="btn-warn"
            :disabled="isBusy('bulk-update') || !isReasonValid(bulkForm.reason)"
            @click="applyBulkUpdate"
          >
            {{ isBusy('bulk-update') ? 'Đang áp dụng...' : 'Áp dụng cập nhật' }}
          </button>

          <p v-if="errorMap['bulk-update']" class="error-text">{{ errorMap['bulk-update'] }}</p>

          <div v-if="bulkResult" class="result-card">
            <p>Số tập ảnh hưởng: <strong>{{ bulkResult.affected_volumes }}/{{ bulkResult.total_volumes }}</strong></p>
            <p>Khoảng giá mới: <strong>{{ bulkResult.min_new_price }} - {{ bulkResult.max_new_price }}</strong></p>
          </div>
        </div>

        <div class="panel-card">
          <h3>Thông tin Bảng giá</h3>
          <p class="stat-line">Phiên bản: <strong>{{ pricingForm.version_no }}</strong></p>
          <p class="stat-line">Hệ số thuê: <strong>{{ pricingForm.k_rent }}</strong></p>
          <p class="stat-line">Hệ số đặt cọc: <strong>{{ pricingForm.k_deposit }}</strong></p>
          <p class="stat-line">Giá sàn: <strong>{{ pricingForm.d_floor }}</strong></p>
          <button class="btn-ghost" :disabled="isBusy('load-pricing')" @click="loadPricing">
            {{ isBusy('load-pricing') ? 'Đang tải...' : 'Tải lại thông tin' }}
          </button>
          <p v-if="errorMap['load-pricing']" class="error-text">{{ errorMap['load-pricing'] }}</p>
        </div>
      </aside>

      <div class="right-panel">
        <article class="panel-card">
          <div class="card-head">
            <h3>Quy tắc Giá đang hoạt động</h3>
            <span class="pill">phiên bản {{ pricingForm.version_no }}</span>
          </div>

          <div class="form-grid">
            <div>
              <label class="field-label">Hệ số thuê (k_rent)</label>
              <input v-model.number="pricingForm.k_rent" class="field-input" type="number" step="0.01" />
            </div>
            <div>
              <label class="field-label">Hệ số đặt cọc (k_deposit)</label>
              <input v-model.number="pricingForm.k_deposit" class="field-input" type="number" step="0.01" />
            </div>
            <div>
              <label class="field-label">Giá sàn (d_floor)</label>
              <input v-model.number="pricingForm.d_floor" class="field-input" type="number" step="1000" />
            </div>
            <div>
              <label class="field-label">Hệ số cầu (used_demand_factor)</label>
              <input v-model.number="pricingForm.used_demand_factor" class="field-input" type="number" step="0.01" />
            </div>
            <div>
              <label class="field-label">Tỷ lệ trần (used_cap_ratio)</label>
              <input v-model.number="pricingForm.used_cap_ratio" class="field-input" type="number" step="0.01" />
            </div>
            <div class="full-width">
              <label class="field-label">Ghi chú</label>
              <input v-model="pricingForm.note" class="field-input" />
            </div>
          </div>

          <div class="form-actions">
            <button class="btn-primary" :disabled="isBusy('save-pricing')" @click="savePricingRule">
              {{ isBusy('save-pricing') ? 'Đang lưu...' : 'Cập nhật quy tắc' }}
            </button>
          </div>

          <p v-if="errorMap['save-pricing']" class="error-text">{{ errorMap['save-pricing'] }}</p>
        </article>

        <article class="panel-card info-section">
          <div class="card-head">
            <h3>Giải thích Công thức Tính giá</h3>
          </div>
          <div class="info-grid">
            <div class="info-item">
              <p class="formula-title">1. Giá Thuê (Cố định)</p>
              <code class="formula-box">Giá thuê = Max(2.000đ, Giá bìa × k_rent)</code>
              <p class="formula-desc">• Giá thuê không đổi bất kể truyện cũ hay mới.</p>
              <p class="formula-desc">• Đảm bảo tính nhất quán và dễ nhớ cho khách hàng.</p>
            </div>
            <div class="info-item">
              <p class="formula-title">2. Tiền Đặt cọc</p>
              <code class="formula-box">Tiền cọc = Max(Giá bìa × k_deposit, Giá sàn)</code>
              <p class="formula-desc">• Giá sàn (d_floor) đảm bảo thu hồi vốn cho truyện giá thấp.</p>
            </div>
            <div class="info-item">
              <p class="formula-title">3. Giá Bán (Truyện cũ)</p>
              <code class="formula-box">Giá bán = Min(Giá bìa × Chất lượng% × Hệ số cầu, Giá bìa × Tỷ lệ trần)</code>
              <p class="formula-desc">• Hệ số cầu: Điều chỉnh giá theo độ hot của truyện.</p>
              <p class="formula-desc">• Tỷ lệ trần: Đảm bảo giá bán cũ không vượt quá giá bìa.</p>
            </div>
          </div>
        </article>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref, watch } from 'vue';
import { StoryHubApiError } from '../../../services/storyhubApi';
import type { BulkPriceUpdatePayload } from '../../../services/storyhubApi';
import { useAdminApi } from '../../../composables/useAdminApi';

type ActionKey = 'load-pricing' | 'save-pricing' | 'bulk-update';

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

const pricingForm = reactive({
  version_no: 0,
  k_rent: 0.05,
  k_deposit: 1,
  d_floor: 5000,
  used_demand_factor: 1,
  used_cap_ratio: 0.8,
  note: '',
});

const bulkForm = reactive({
  percent_delta: 0,
  reason: '',
});

const bulkResult = ref<BulkPriceUpdatePayload | null>(null);

const loadingMap = reactive<Record<ActionKey, boolean>>({
  'load-pricing': false,
  'save-pricing': false,
  'bulk-update': false,
});

const errorMap = reactive<Record<ActionKey, string | null>>({
  'load-pricing': null,
  'save-pricing': null,
  'bulk-update': null,
});

onMounted(() => {
  if (props.isActive) {
    initialized.value = true;
    void loadPricing();
  }
});

watch(
  () => props.isActive,
  (isActive) => {
    if (isActive && !initialized.value) {
      initialized.value = true;
      void loadPricing();
    }
  },
);

watch(
  () => [pricingForm.version_no, pricingForm.k_rent],
  () => {
    emit('kpi', {
      primaryLabel: 'Phiên bản quy tắc',
      primaryValue: String(pricingForm.version_no),
      secondaryLabel: 'hệ số thuê',
      secondaryValue: String(pricingForm.k_rent),
    });
  },
  { immediate: true },
);

function isBusy(key: ActionKey) {
  return loadingMap[key];
}

function isReasonValid(reason: string) {
  return reason.trim().length >= 3;
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

async function loadPricing() {
  await runAction('load-pricing', async () => {
    const payload = await adminApi.fetchActivePricingRule();

    pricingForm.version_no = payload.version_no;
    pricingForm.k_rent = payload.k_rent;
    pricingForm.k_deposit = payload.k_deposit;
    pricingForm.d_floor = payload.d_floor;
    pricingForm.used_demand_factor = payload.used_demand_factor;
    pricingForm.used_cap_ratio = payload.used_cap_ratio;
    pricingForm.note = payload.note || '';
  });
}

async function savePricingRule() {
  await runAction('save-pricing', async () => {
    const payload = await adminApi.updateActivePricingRule({
      k_rent: pricingForm.k_rent,
      k_deposit: pricingForm.k_deposit,
      d_floor: pricingForm.d_floor,
      used_demand_factor: pricingForm.used_demand_factor,
      used_cap_ratio: pricingForm.used_cap_ratio,
      note: pricingForm.note.trim() || null,
    });

    pricingForm.version_no = payload.version_no;
    emit('notify', { type: 'success', message: 'Đã cập nhật quy tắc giá.' });
  });
}

async function applyBulkUpdate() {
  if (!isReasonValid(bulkForm.reason)) {
    emit('notify', { type: 'error', message: 'Lý do là bắt buộc khi cập nhật hàng loạt.' });
    return;
  }

  await runAction('bulk-update', async () => {
    bulkResult.value = await adminApi.applyBulkPriceUpdate(
      bulkForm.percent_delta,
      bulkForm.reason.trim(),
    );

    emit('notify', {
      type: 'success',
      message: `Đã áp dụng giá mới cho ${bulkResult.value.affected_volumes} tập truyện.`,
    });
  });
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

.result-card {
  margin-top: 12px;
  border-radius: 12px;
  border: 1px dashed #cbd5e1;
  background: #f8fafc;
  padding: 10px;
  font-size: 13px;
  color: #334155;
}

.stat-line {
  margin: 8px 0;
  color: #334155;
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

.info-section {
  margin-top: 24px;
  background: linear-gradient(180deg, #f0f9ff 0%, #ffffff 100%) !important;
  border-color: #bae6fd !important;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 20px;
  margin-top: 12px;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.formula-title {
  margin: 0;
  font-size: 14px;
  font-weight: 700;
  color: #0369a1;
}

.formula-box {
  display: block;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 8px 12px;
  font-family: 'Courier New', Courier, monospace;
  font-size: 13px;
  color: #1e293b;
}

.formula-desc {
  margin: 0;
  font-size: 12px;
  color: #64748b;
  line-height: 1.5;
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
