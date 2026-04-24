<template>
  <section class="tab-shell">
    <button class="mobile-toggle" @click="leftOpen = !leftOpen">
      {{ leftOpen ? 'Ẩn bộ lọc' : 'Hiện bộ lọc' }}
    </button>

    <div class="tab-split">
      <aside class="left-panel" :class="{ open: leftOpen }">
        <div class="panel-card">
          <h3>Hành động Khuyến mãi</h3>
          <button class="btn-primary" @click="openVoucherCreate">Tạo Voucher</button>
          <button class="btn-primary" @click="openAutoPromoCreate">Tạo Khuyến mãi tự động</button>
          <button class="btn-ghost" :disabled="isBusy('refresh-all')" @click="refreshAll">
            {{ isBusy('refresh-all') ? 'Đang tải...' : 'Làm mới tất cả' }}
          </button>
          <p v-if="errorMap['refresh-all']" class="error-text">{{ errorMap['refresh-all'] }}</p>
        </div>

        <div class="panel-card">
          <h3>Thống kê nhanh</h3>
          <p class="stat-line">Voucher: <strong>{{ vouchers.length }}</strong></p>
          <p class="stat-line">Khuyến mãi tự động: <strong>{{ autoPromos.length }}</strong></p>
          <p class="stat-line">Đang hoạt động: <strong>{{ activeAutoPromoCount }}</strong></p>
        </div>
      </aside>

      <div class="right-panel">
        <article class="panel-card">
          <div class="card-head">
            <h3>Danh sách Voucher</h3>
            <span class="pill">{{ vouchers.length }} mã</span>
          </div>

          <div class="table-wrap">
            <table class="table">
              <thead>
                <tr>
                  <th>Mã</th>
                  <th>Loại</th>
                  <th>Giá trị</th>
                  <th>Đã dùng</th>
                  <th>Trạng thái</th>
                  <th>Hành động</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="voucher in vouchers" :key="voucher.id">
                  <td>{{ voucher.code }}</td>
                  <td>{{ voucher.voucher_type }}</td>
                  <td>{{ voucher.value }}</td>
                  <td>{{ voucher.current_uses }}/{{ voucher.max_uses ?? 'inf' }}</td>
                  <td>
                    <span :class="voucher.is_active ? 'pill-ok' : 'pill-danger'">
                      {{ voucher.is_active ? 'Hoạt động' : 'Đã khóa' }}
                    </span>
                  </td>
                  <td class="row-actions">
                    <button class="btn-row" @click="openVoucherEdit(voucher)">Sửa</button>
                    <button class="btn-row warn" @click="toggleVoucher(voucher)">
                      {{ voucher.is_active ? 'Khóa' : 'Mở' }}
                    </button>
                    <button class="btn-row danger" @click="removeVoucher(voucher)">Xóa</button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <p v-if="errorMap['load-vouchers']" class="error-text">{{ errorMap['load-vouchers'] }}</p>
        </article>

        <article class="panel-card">
          <div class="card-head">
            <h3>Khuyến mãi Tự động</h3>
            <span class="pill">{{ autoPromos.length }} quy tắc</span>
          </div>

          <div class="table-wrap">
            <table class="table">
              <thead>
                <tr>
                  <th>Tên</th>
                  <th>Ngày</th>
                  <th>Giảm giá</th>
                  <th>Trạng thái</th>
                  <th>Hành động</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="promo in autoPromos" :key="promo.id">
                  <td>{{ promo.name }}</td>
                  <td>{{ dayName(promo.day_of_week) }}</td>
                  <td>{{ promo.discount_percent }}%</td>
                  <td>
                    <span :class="promo.is_active ? 'pill-ok' : 'pill-danger'">
                      {{ promo.is_active ? 'Hoạt động' : 'Đã khóa' }}
                    </span>
                  </td>
                  <td class="row-actions">
                    <button class="btn-row" @click="openAutoPromoEdit(promo)">Sửa</button>
                    <button class="btn-row warn" @click="toggleAutoPromo(promo)">
                      {{ promo.is_active ? 'Khóa' : 'Mở' }}
                    </button>
                    <button class="btn-row danger" @click="removeAutoPromo(promo)">Xóa</button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <p v-if="errorMap['load-auto-promos']" class="error-text">{{ errorMap['load-auto-promos'] }}</p>
        </article>
      </div>
    </div>

    <Teleport to="body">
      <!-- Modal xác nhận xóa Voucher -->
      <div v-if="deleteVoucherModal.open" class="modal-overlay">
        <div class="modal-card">
          <h3>Xóa Voucher vĩnh viễn</h3>
          <p class="modal-subtitle">{{ deleteVoucherModal.code }}</p>

          <label class="field-label">Lý do xóa (bắt buộc)</label>
          <textarea v-model="deleteVoucherModal.reason" class="field-input" rows="3" placeholder="Nhập lý do xóa (tối thiểu 3 ký tự)" />

          <div class="modal-actions">
            <button class="btn-ghost" @click="deleteVoucherModal.open = false">Hủy</button>
            <button
              class="btn-danger"
              :disabled="isBusy('delete-voucher') || !isReasonValid(deleteVoucherModal.reason)"
              @click="submitDeleteVoucher"
            >
              {{ isBusy('delete-voucher') ? 'Đang xóa...' : 'Xóa ngay' }}
            </button>
          </div>
          <p v-if="errorMap['delete-voucher']" class="error-text">{{ errorMap['delete-voucher'] }}</p>
        </div>
      </div>

      <!-- Modal xác nhận xóa AutoPromo -->
      <div v-if="deleteAutoPromoModal.open" class="modal-overlay">
        <div class="modal-card">
          <h3>Xóa Khuyến mãi tự động vĩnh viễn</h3>
          <p class="modal-subtitle">{{ deleteAutoPromoModal.name }}</p>

          <label class="field-label">Lý do xóa (bắt buộc)</label>
          <textarea v-model="deleteAutoPromoModal.reason" class="field-input" rows="3" placeholder="Nhập lý do xóa (tối thiểu 3 ký tự)" />

          <div class="modal-actions">
            <button class="btn-ghost" @click="deleteAutoPromoModal.open = false">Hủy</button>
            <button
              class="btn-danger"
              :disabled="isBusy('delete-auto-promo') || !isReasonValid(deleteAutoPromoModal.reason)"
              @click="submitDeleteAutoPromo"
            >
              {{ isBusy('delete-auto-promo') ? 'Đang xóa...' : 'Xóa ngay' }}
            </button>
          </div>
          <p v-if="errorMap['delete-auto-promo']" class="error-text">{{ errorMap['delete-auto-promo'] }}</p>
        </div>
      </div>

      <div v-if="voucherModal.open" class="modal-overlay">
        <div class="modal-card">
          <h3>{{ voucherModal.mode === 'create' ? 'Tạo Voucher' : 'Cập nhật Voucher' }}</h3>

          <label class="field-label">Mã Code</label>
          <input
            v-model="voucherModal.code"
            class="field-input"
            :disabled="voucherModal.mode === 'edit'"
            placeholder="SUMMER2026"
          />

          <label class="field-label">Loại</label>
          <select v-model="voucherModal.voucher_type" class="field-input">
            <option value="percent">percent</option>
            <option value="amount">amount</option>
          </select>

          <label class="field-label">Giá trị</label>
          <input v-model.number="voucherModal.value" class="field-input" type="number" min="1" />

          <label class="field-label">Chi tiêu tối thiểu</label>
          <input v-model.number="voucherModal.min_spend" class="field-input" type="number" min="0" />

          <label class="field-label">Giảm tối đa</label>
          <input v-model.number="voucherModal.max_discount" class="field-input" type="number" min="0" />

          <label class="field-label">Số lần dùng tối đa</label>
          <input v-model.number="voucherModal.max_uses" class="field-input" type="number" min="1" />

          <label class="field-label">Kết thúc (ISO datetime)</label>
          <input v-model="voucherModal.end_at" class="field-input" placeholder="2026-12-31T23:59:00" />

          <label class="field-checkbox">
            <input v-model="voucherModal.is_active" type="checkbox" />
            Đang hoạt động
          </label>

          <div class="modal-actions">
            <button class="btn-ghost" @click="voucherModal.open = false">Hủy</button>
            <button class="btn-primary" :disabled="isBusy('save-voucher')" @click="saveVoucher">
              {{ isBusy('save-voucher') ? 'Đang lưu...' : 'Lưu Voucher' }}
            </button>
          </div>
          <p v-if="errorMap['save-voucher']" class="error-text">{{ errorMap['save-voucher'] }}</p>
        </div>
      </div>

      <div v-if="autoPromoModal.open" class="modal-overlay">
        <div class="modal-card">
          <h3>{{ autoPromoModal.mode === 'create' ? 'Tạo Khuyến mãi tự động' : 'Cập nhật Khuyến mãi' }}</h3>

          <label class="field-label">Tên chương trình</label>
          <input v-model="autoPromoModal.name" class="field-input" />

          <label class="field-label">Ngày trong tuần (0..6, 0=CN)</label>
          <input v-model.number="autoPromoModal.day_of_week" class="field-input" type="number" min="0" max="6" />

          <label class="field-label">Phần trăm giảm giá</label>
          <input v-model.number="autoPromoModal.discount_percent" class="field-input" type="number" min="1" max="90" />

          <label class="field-checkbox">
            <input v-model="autoPromoModal.is_active" type="checkbox" />
            Đang hoạt động
          </label>

          <div class="modal-actions">
            <button class="btn-ghost" @click="autoPromoModal.open = false">Hủy</button>
            <button class="btn-primary" :disabled="isBusy('save-auto-promo')" @click="saveAutoPromo">
              {{ isBusy('save-auto-promo') ? 'Đang lưu...' : 'Lưu Khuyến mãi' }}
            </button>
          </div>
          <p v-if="errorMap['save-auto-promo']" class="error-text">{{ errorMap['save-auto-promo'] }}</p>
        </div>
      </div>
    </Teleport>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue';
import { StoryHubApiError } from '../../../services/storyhubApi';
import type { AutoPromoItem, VoucherItem } from '../../../services/storyhubApi';
import { useAdminApi } from '../../../composables/useAdminApi';

type ActionKey =
  | 'refresh-all'
  | 'load-vouchers'
  | 'load-auto-promos'
  | 'save-voucher'
  | 'delete-voucher'
  | 'save-auto-promo'
  | 'delete-auto-promo';

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

const vouchers = ref<VoucherItem[]>([]);
const autoPromos = ref<AutoPromoItem[]>([]);

const loadingMap = reactive<Record<ActionKey, boolean>>({
  'refresh-all': false,
  'load-vouchers': false,
  'load-auto-promos': false,
  'save-voucher': false,
  'delete-voucher': false,
  'save-auto-promo': false,
  'delete-auto-promo': false,
});

const errorMap = reactive<Record<ActionKey, string | null>>({
  'refresh-all': null,
  'load-vouchers': null,
  'load-auto-promos': null,
  'save-voucher': null,
  'delete-voucher': null,
  'save-auto-promo': null,
  'delete-auto-promo': null,
});

const voucherModal = reactive({
  open: false,
  mode: 'create' as 'create' | 'edit',
  id: null as number | null,
  code: '',
  voucher_type: 'percent' as 'percent' | 'amount',
  value: 10,
  min_spend: 0,
  max_discount: null as number | null,
  max_uses: null as number | null,
  end_at: '',
  is_active: true,
});

const autoPromoModal = reactive({
  open: false,
  mode: 'create' as 'create' | 'edit',
  id: null as number | null,
  name: '',
  day_of_week: 2,
  discount_percent: 10,
  is_active: true,
});

const activeAutoPromoCount = computed(() => autoPromos.value.filter((promo) => promo.is_active).length);

const deleteVoucherModal = reactive({
  open: false,
  id: null as number | null,
  code: '',
  reason: '',
});

const deleteAutoPromoModal = reactive({
  open: false,
  id: null as number | null,
  name: '',
  reason: '',
});

onMounted(() => {
  if (props.isActive) {
    initialized.value = true;
    void refreshAll();
  }
});

watch(
  () => props.isActive,
  (isActive) => {
    if (isActive && !initialized.value) {
      initialized.value = true;
      void refreshAll();
    }
  },
);

watch(
  () => [vouchers.value.length, autoPromos.value.length, activeAutoPromoCount.value],
  () => {
    emit('kpi', {
      primaryLabel: 'Voucher',
      primaryValue: String(vouchers.value.length),
      secondaryLabel: 'Khuyến mãi tự động',
      secondaryValue: String(activeAutoPromoCount.value),
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

async function refreshAll() {
  await runAction('refresh-all', async () => {
    await Promise.all([loadVouchers(), loadAutoPromotions()]);
  });
}

async function loadVouchers() {
  await runAction('load-vouchers', async () => {
    vouchers.value = await adminApi.fetchVouchers();
  });
}

async function loadAutoPromotions() {
  await runAction('load-auto-promos', async () => {
    autoPromos.value = await adminApi.fetchAutoPromotions();
  });
}

function openVoucherCreate() {
  voucherModal.mode = 'create';
  voucherModal.id = null;
  voucherModal.code = '';
  voucherModal.voucher_type = 'percent';
  voucherModal.value = 10;
  voucherModal.min_spend = 0;
  voucherModal.max_discount = null;
  voucherModal.max_uses = null;
  voucherModal.end_at = '';
  voucherModal.is_active = true;
  voucherModal.open = true;
}

function openVoucherEdit(voucher: VoucherItem) {
  voucherModal.mode = 'edit';
  voucherModal.id = voucher.id;
  voucherModal.code = voucher.code;
  voucherModal.voucher_type = voucher.voucher_type;
  voucherModal.value = voucher.value;
  voucherModal.min_spend = voucher.min_spend;
  voucherModal.max_discount = voucher.max_discount;
  voucherModal.max_uses = voucher.max_uses;
  voucherModal.end_at = voucher.end_at ?? '';
  voucherModal.is_active = voucher.is_active;
  voucherModal.open = true;
}

async function saveVoucher() {
  if (!voucherModal.code.trim() && voucherModal.mode === 'create') {
    emit('notify', { type: 'error', message: 'Mã Voucher là bắt buộc.' });
    return;
  }

  await runAction('save-voucher', async () => {
    if (voucherModal.mode === 'create') {
      await adminApi.createVoucher({
        code: voucherModal.code.trim(),
        voucher_type: voucherModal.voucher_type,
        value: voucherModal.value,
        min_spend: voucherModal.min_spend,
        max_discount: voucherModal.max_discount,
        max_uses: voucherModal.max_uses,
        end_at: voucherModal.end_at.trim() || null,
      });
    } else if (voucherModal.id !== null) {
      await adminApi.updateVoucher(voucherModal.id, {
        value: voucherModal.value,
        min_spend: voucherModal.min_spend,
        max_discount: voucherModal.max_discount,
        max_uses: voucherModal.max_uses,
        end_at: voucherModal.end_at.trim() || null,
        is_active: voucherModal.is_active,
      });
    }

    voucherModal.open = false;
    emit('notify', { type: 'success', message: 'Lưu Voucher thành công.' });
    await loadVouchers();
  });
}

async function toggleVoucher(voucher: VoucherItem) {
  await runAction('save-voucher', async () => {
    await adminApi.updateVoucher(voucher.id, { is_active: !voucher.is_active });
    emit('notify', { type: 'success', message: 'Đã thay đổi trạng thái Voucher.' });
    await loadVouchers();
  });
}

function openDeleteVoucherModal(voucher: VoucherItem) {
  deleteVoucherModal.id = voucher.id;
  deleteVoucherModal.code = voucher.code;
  deleteVoucherModal.reason = '';
  deleteVoucherModal.open = true;
}

async function submitDeleteVoucher() {
  if (deleteVoucherModal.id === null || !isReasonValid(deleteVoucherModal.reason)) {
    return;
  }

  await runAction('delete-voucher', async () => {
    await adminApi.deleteVoucher(deleteVoucherModal.id!);
    deleteVoucherModal.open = false;
    emit('notify', { type: 'success', message: 'Đã xóa Voucher thành công.' });
    await loadVouchers();
  });
}

// Hàm cũ removeVoucher thay bằng openDeleteVoucherModal – xem ở template
function removeVoucher(voucher: VoucherItem) {
  openDeleteVoucherModal(voucher);
}

function openAutoPromoCreate() {
  autoPromoModal.mode = 'create';
  autoPromoModal.id = null;
  autoPromoModal.name = '';
  autoPromoModal.day_of_week = 2;
  autoPromoModal.discount_percent = 10;
  autoPromoModal.is_active = true;
  autoPromoModal.open = true;
}

function openAutoPromoEdit(promo: AutoPromoItem) {
  autoPromoModal.mode = 'edit';
  autoPromoModal.id = promo.id;
  autoPromoModal.name = promo.name;
  autoPromoModal.day_of_week = promo.day_of_week;
  autoPromoModal.discount_percent = promo.discount_percent;
  autoPromoModal.is_active = promo.is_active;
  autoPromoModal.open = true;
}

async function saveAutoPromo() {
  if (!autoPromoModal.name.trim()) {
    emit('notify', { type: 'error', message: 'Tên chương trình là bắt buộc.' });
    return;
  }

  await runAction('save-auto-promo', async () => {
    if (autoPromoModal.mode === 'create') {
      await adminApi.createAutoPromotion({
        name: autoPromoModal.name.trim(),
        day_of_week: autoPromoModal.day_of_week,
        discount_percent: autoPromoModal.discount_percent,
      });
    } else if (autoPromoModal.id !== null) {
      await adminApi.updateAutoPromotion(autoPromoModal.id, {
        name: autoPromoModal.name.trim(),
        day_of_week: autoPromoModal.day_of_week,
        discount_percent: autoPromoModal.discount_percent,
        is_active: autoPromoModal.is_active,
      });
    }

    autoPromoModal.open = false;
    emit('notify', { type: 'success', message: 'Lưu khuyến mãi tự động thành công.' });
    await loadAutoPromotions();
  });
}

async function toggleAutoPromo(promo: AutoPromoItem) {
  await runAction('save-auto-promo', async () => {
    await adminApi.updateAutoPromotion(promo.id, { is_active: !promo.is_active });
    emit('notify', { type: 'success', message: 'Đã thay đổi trạng thái khuyến mãi.' });
    await loadAutoPromotions();
  });
}

function openDeleteAutoPromoModal(promo: AutoPromoItem) {
  deleteAutoPromoModal.id = promo.id;
  deleteAutoPromoModal.name = promo.name;
  deleteAutoPromoModal.reason = '';
  deleteAutoPromoModal.open = true;
}

async function submitDeleteAutoPromo() {
  if (deleteAutoPromoModal.id === null || !isReasonValid(deleteAutoPromoModal.reason)) {
    return;
  }

  await runAction('delete-auto-promo', async () => {
    await adminApi.deleteAutoPromotion(deleteAutoPromoModal.id!);
    deleteAutoPromoModal.open = false;
    emit('notify', { type: 'success', message: 'Đã xóa khuyến mãi tự động thành công.' });
    await loadAutoPromotions();
  });
}

// Hàm cũ removeAutoPromo thay bằng openDeleteAutoPromoModal – xem ở template
function removeAutoPromo(promo: AutoPromoItem) {
  openDeleteAutoPromoModal(promo);
}

function dayName(dayOfWeek: number) {
  const labels = ['CN', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7'];
  return labels[dayOfWeek] ?? String(dayOfWeek);
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

.field-checkbox {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 10px 0;
  font-size: 13px;
}

.stat-line {
  margin: 8px 0;
  color: #334155;
}

.btn-primary,
.btn-ghost,
.btn-row,
.btn-danger {
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
  margin-bottom: 8px;
}

.btn-ghost {
  background: #e2e8f0;
  color: #0f172a;
}

.btn-row {
  background: #dbeafe;
  color: #1e3a8a;
}

.btn-row.warn {
  background: #ffedd5;
  color: #9a3412;
}

.btn-row.danger {
  background: #fee2e2;
  color: #991b1b;
}

.btn-danger {
  background: #b91c1c;
  color: #ffffff;
}

.btn-primary:disabled,
.btn-ghost:disabled,
.btn-danger:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.table-wrap {
  overflow-x: auto;
}

.table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.table th,
.table td {
  border-bottom: 1px solid #e2e8f0;
  text-align: left;
  padding: 8px;
  vertical-align: top;
}

.table th {
  color: #334155;
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.03em;
}

.row-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.pill,
.pill-ok,
.pill-danger {
  display: inline-flex;
  align-items: center;
  border-radius: 999px;
  padding: 4px 10px;
  font-size: 11px;
  font-weight: 700;
}

.pill {
  background: #e2e8f0;
  color: #0f172a;
}

.pill-ok {
  background: #dcfce7;
  color: #166534;
}

.pill-danger {
  background: #fee2e2;
  color: #991b1b;
}

.error-text {
  margin-top: 8px;
  color: #b91c1c;
  font-size: 12px;
}

.modal-overlay {
  position: fixed;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(15, 23, 42, 0.55);
  z-index: 2000;
}

.modal-card {
  width: min(560px, calc(100vw - 24px));
  background: #ffffff;
  border-radius: 16px;
  border: 1px solid #dbe4f0;
  padding: 18px;
}

.modal-card h3 {
  margin: 0;
  color: #0f172a;
}

.modal-actions {
  margin-top: 14px;
  display: flex;
  justify-content: flex-end;
  gap: 8px;
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
}
</style>
