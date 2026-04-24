<template>
  <section class="tab-shell">
    <button class="mobile-toggle" @click="leftOpen = !leftOpen">
      {{ leftOpen ? 'Ẩn bộ lọc' : 'Hiện bộ lọc' }}
    </button>

    <div class="tab-split">
      <aside class="left-panel" :class="{ open: leftOpen }">
        <div class="panel-card">
          <h3>Bộ lọc Dữ liệu</h3>
          <label class="field-label">Tìm kiếm khách hàng</label>
          <input v-model="customerQuery" class="field-input" placeholder="Tên hoặc số điện thoại" />

          <label class="field-checkbox">
            <input v-model="blacklistedOnly" type="checkbox" />
            Chỉ danh sách đen
          </label>

          <button class="btn-primary" :disabled="isBusy('load-customers')" @click="loadCustomers">
            {{ isBusy('load-customers') ? 'Đang tải...' : 'Tải khách hàng' }}
          </button>
          <p v-if="errorMap['load-customers']" class="error-text">{{ errorMap['load-customers'] }}</p>
        </div>

        <div class="panel-card">
          <h3>Bộ lọc Giao dịch</h3>
          <label class="field-label">Tìm kiếm giao dịch</label>
          <input v-model="transactionQuery" class="field-input" placeholder="Mã đơn / khách hàng" />

          <label class="field-label">Loại</label>
          <select v-model="transactionKind" class="field-input">
            <option value="all">Tất cả</option>
            <option value="sale">Bán hàng</option>
            <option value="rental">Cho thuê</option>
          </select>

          <button class="btn-primary" :disabled="isBusy('load-transactions')" @click="loadTransactions">
            {{ isBusy('load-transactions') ? 'Đang tải...' : 'Tải giao dịch' }}
          </button>
          <p v-if="errorMap['load-transactions']" class="error-text">{{ errorMap['load-transactions'] }}</p>
        </div>

        <div class="panel-card">
          <h3>Bộ lọc Nhật ký</h3>
          <label class="field-label">Mã hành động</label>
          <input v-model="auditAction" class="field-input" placeholder="AUTO_PROMO_UPDATED" />

          <button class="btn-primary" :disabled="isBusy('load-audit')" @click="loadAuditLogs">
            {{ isBusy('load-audit') ? 'Đang tải...' : 'Tải nhật ký' }}
          </button>
          <p v-if="errorMap['load-audit']" class="error-text">{{ errorMap['load-audit'] }}</p>
        </div>

        <button class="btn-ghost" :disabled="isBusy('refresh-all')" @click="refreshAll">
          {{ isBusy('refresh-all') ? 'Đang làm mới...' : 'Làm mới tất cả' }}
        </button>
      </aside>

      <div class="right-panel">
        <article class="panel-card">
          <div class="card-head">
            <h3>Quản lý Khách hàng</h3>
            <span class="pill">{{ customers.length }} khách hàng</span>
          </div>

          <div class="table-wrap">
            <table class="table">
              <thead>
                <tr>
                  <th>Tên</th>
                  <th>Điện thoại</th>
                  <th>Tiền cọc</th>
                  <th>Công nợ</th>
                  <th>Trạng thái</th>
                  <th>Hành động</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="customer in customers" :key="customer.id">
                  <td>{{ customer.name }}</td>
                  <td>{{ customer.phone }}</td>
                  <td>{{ formatNumber(customer.deposit_balance) }}</td>
                  <td>{{ formatNumber(customer.debt) }}</td>
                  <td>
                    <span :class="customer.blacklist_flag ? 'pill-danger' : 'pill-ok'">
                      {{ customer.blacklist_flag ? 'Danh sách đen' : 'Hoạt động' }}
                    </span>
                  </td>
                  <td>
                    <button class="btn-row" @click="openOverrideModal(customer)">Điều chỉnh</button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </article>

        <article class="panel-card">
          <div class="card-head">
            <h3>Giao dịch</h3>
            <span class="pill">{{ transactions.length }} bản ghi</span>
          </div>

          <div class="table-wrap">
            <table class="table">
              <thead>
                <tr>
                  <th>Mã tham chiếu</th>
                  <th>Loại</th>
                  <th>Khách hàng</th>
                  <th>Số tiền</th>
                  <th>Trạng thái</th>
                  <th>Hành động</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="tx in transactions"
                  :key="`${tx.transaction_type}-${tx.reference_id}`"
                >
                  <td>{{ tx.reference_id }}</td>
                  <td>{{ tx.transaction_type }}</td>
                  <td>{{ tx.customer_name }}</td>
                  <td>{{ formatNumber(tx.amount) }}</td>
                  <td>{{ tx.status }}</td>
                  <td class="row-actions">
                    <button
                      v-if="tx.can_refund"
                      class="btn-row warn"
                      @click="openRefundModal(tx)"
                    >
                      Hoàn tiền khẩn cấp
                    </button>
                    <button
                      v-if="tx.can_hard_delete"
                      class="btn-row danger"
                      @click="openHardDeleteModal(tx)"
                    >
                      Xóa vĩnh viễn
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </article>

        <article class="panel-card">
          <div class="card-head">
            <h3>Nhật ký Hệ thống</h3>
            <span class="pill">{{ auditLogs.length }} mới nhất</span>
          </div>

          <div class="table-wrap">
            <table class="table">
              <thead>
                <tr>
                  <th>Thời gian</th>
                  <th>Hành động</th>
                  <th>Đối tượng</th>
                  <th>Người thực hiện</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="log in auditLogs" :key="log.id">
                  <td>{{ formatDate(log.created_at) }}</td>
                  <td>{{ log.action }}</td>
                  <td>{{ log.entity_type }}#{{ log.entity_id }}</td>
                  <td>{{ log.actor_full_name || log.actor_name || 'N/A' }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </article>
      </div>
    </div>

    <Teleport to="body">
      <div v-if="overrideModal.open" class="modal-overlay">
        <div class="modal-card">
          <h3>Điều chỉnh Khách hàng</h3>
          <p class="modal-subtitle">{{ overrideModal.customer?.name }}</p>

          <label class="field-label">Số dư tiền cọc</label>
          <input v-model.number="overrideModal.deposit_balance" class="field-input" type="number" />

          <label class="field-label">Công nợ</label>
          <input v-model.number="overrideModal.debt" class="field-input" type="number" />

          <label class="field-checkbox">
            <input v-model="overrideModal.blacklist_flag" type="checkbox" />
            Đưa vào danh sách đen
          </label>

          <label class="field-label">Lý do (bắt buộc)</label>
          <textarea v-model="overrideModal.reason" class="field-input" rows="3" />

          <div class="modal-actions">
            <button class="btn-ghost" @click="overrideModal.open = false">Hủy</button>
            <button
              class="btn-primary"
              :disabled="isBusy('override-customer') || !isReasonValid(overrideModal.reason)"
              @click="submitOverride"
            >
              {{ isBusy('override-customer') ? 'Đang gửi...' : 'Xác nhận điều chỉnh' }}
            </button>
          </div>
        </div>
      </div>

      <div v-if="hardDeleteModal.open" class="modal-overlay">
        <div class="modal-card">
          <h3>Xóa vĩnh viễn giao dịch</h3>
          <p class="modal-subtitle">
            {{ hardDeleteModal.tx?.transaction_type }}#{{ hardDeleteModal.tx?.reference_id }}
          </p>

          <label class="field-label">Lý do (bắt buộc)</label>
          <textarea v-model="hardDeleteModal.reason" class="field-input" rows="3" />

          <div class="modal-actions">
            <button class="btn-ghost" @click="hardDeleteModal.open = false">Hủy</button>
            <button
              class="btn-danger"
              :disabled="isBusy('hard-delete') || !isReasonValid(hardDeleteModal.reason)"
              @click="submitHardDelete"
            >
              {{ isBusy('hard-delete') ? 'Đang xóa...' : 'Xóa ngay lập tức' }}
            </button>
          </div>
        </div>
      </div>

      <div v-if="refundModal.open" class="modal-overlay">
        <div class="modal-card">
          <h3>Hoàn tiền khẩn cấp</h3>
          <p class="modal-subtitle">
            {{ refundModal.tx?.transaction_type }}#{{ refundModal.tx?.reference_id }}
          </p>

          <label class="field-label">Phương thức hoàn tiền</label>
          <select v-model="refundModal.refund_method" class="field-input">
            <option value="original_method">Phương thức gốc</option>
            <option value="cash">Tiền mặt</option>
            <option value="bank_transfer">Chuyển khoản</option>
            <option value="e_wallet">Ví điện tử</option>
          </select>

          <label class="field-label">Lý do (bắt buộc)</label>
          <textarea v-model="refundModal.reason" class="field-input" rows="3" />

          <div class="modal-actions">
            <button class="btn-ghost" @click="refundModal.open = false">Hủy</button>
            <button
              class="btn-warn"
              :disabled="isBusy('emergency-refund') || !isReasonValid(refundModal.reason)"
              @click="submitEmergencyRefund"
            >
              {{ isBusy('emergency-refund') ? 'Đang xử lý...' : 'Thực hiện hoàn tiền' }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue';
import { StoryHubApiError } from '../../../services/storyhubApi';
import type {
  AdminTransactionItem,
  AuditLogItem,
  CustomerListItem,
} from '../../../services/storyhubApi';
import { useAdminApi } from '../../../composables/useAdminApi';

type ActionKey =
  | 'refresh-all'
  | 'load-customers'
  | 'load-transactions'
  | 'load-audit'
  | 'override-customer'
  | 'hard-delete'
  | 'emergency-refund';

type RefundMethod = 'cash' | 'bank_transfer' | 'e_wallet' | 'original_method';

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

const customers = ref<CustomerListItem[]>([]);
const transactions = ref<AdminTransactionItem[]>([]);
const auditLogs = ref<AuditLogItem[]>([]);

const customerQuery = ref('');
const blacklistedOnly = ref(false);
const transactionQuery = ref('');
const transactionKind = ref<'all' | 'sale' | 'rental'>('all');
const auditAction = ref('');

const loadingMap = reactive<Record<ActionKey, boolean>>({
  'refresh-all': false,
  'load-customers': false,
  'load-transactions': false,
  'load-audit': false,
  'override-customer': false,
  'hard-delete': false,
  'emergency-refund': false,
});

const errorMap = reactive<Record<ActionKey, string | null>>({
  'refresh-all': null,
  'load-customers': null,
  'load-transactions': null,
  'load-audit': null,
  'override-customer': null,
  'hard-delete': null,
  'emergency-refund': null,
});

const overrideModal = reactive({
  open: false,
  customer: null as CustomerListItem | null,
  deposit_balance: 0,
  debt: 0,
  blacklist_flag: false,
  reason: '',
});

const hardDeleteModal = reactive({
  open: false,
  tx: null as AdminTransactionItem | null,
  reason: '',
});

const refundModal = reactive({
  open: false,
  tx: null as AdminTransactionItem | null,
  reason: '',
  refund_method: 'original_method' as RefundMethod,
});

const blacklistedCount = computed(() => customers.value.filter((customer) => customer.blacklist_flag).length);

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
  () => [customers.value.length, blacklistedCount.value, auditLogs.value.length],
  () => {
    emit('kpi', {
      primaryLabel: 'Khách hàng',
      primaryValue: String(customers.value.length),
      secondaryLabel: 'Danh sách đen',
      secondaryValue: String(blacklistedCount.value),
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

function formatNumber(value: number) {
  return new Intl.NumberFormat('vi-VN').format(value ?? 0);
}

function formatDate(value: string) {
  return new Date(value).toLocaleString('vi-VN');
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
    await Promise.all([loadCustomers(), loadTransactions(), loadAuditLogs()]);
  });
}

async function loadCustomers() {
  await runAction('load-customers', async () => {
    customers.value = await adminApi.fetchCustomers(customerQuery.value.trim(), blacklistedOnly.value);
  });
}

async function loadTransactions() {
  await runAction('load-transactions', async () => {
    transactions.value = await adminApi.fetchTransactions({
      q: transactionQuery.value.trim() || undefined,
      kind: transactionKind.value,
      limit: 50,
      offset: 0,
    });
  });
}

async function loadAuditLogs() {
  await runAction('load-audit', async () => {
    auditLogs.value = await adminApi.fetchAuditLogs({
      action: auditAction.value.trim() || undefined,
      limit: 40,
      offset: 0,
    });
  });
}

function openOverrideModal(customer: CustomerListItem) {
  overrideModal.customer = customer;
  overrideModal.deposit_balance = customer.deposit_balance;
  overrideModal.debt = customer.debt;
  overrideModal.blacklist_flag = customer.blacklist_flag;
  overrideModal.reason = '';
  overrideModal.open = true;
}

function openHardDeleteModal(tx: AdminTransactionItem) {
  hardDeleteModal.tx = tx;
  hardDeleteModal.reason = '';
  hardDeleteModal.open = true;
}

function openRefundModal(tx: AdminTransactionItem) {
  refundModal.tx = tx;
  refundModal.reason = '';
  refundModal.refund_method = 'original_method';
  refundModal.open = true;
}

async function submitOverride() {
  if (!overrideModal.customer || !isReasonValid(overrideModal.reason)) {
    return;
  }

  await runAction('override-customer', async () => {
    await adminApi.overrideCustomer(overrideModal.customer!.id, {
      deposit_balance: overrideModal.deposit_balance,
      debt: overrideModal.debt,
      blacklist_flag: overrideModal.blacklist_flag,
      reason: overrideModal.reason.trim(),
    });

    overrideModal.open = false;
    emit('notify', { type: 'success', message: 'Đã áp dụng thay đổi khách hàng.' });
    await Promise.all([loadCustomers(), loadAuditLogs()]);
  });
}

async function submitHardDelete() {
  if (!hardDeleteModal.tx || !isReasonValid(hardDeleteModal.reason)) {
    return;
  }

  await runAction('hard-delete', async () => {
    await adminApi.hardDeleteTransaction(
      hardDeleteModal.tx!.transaction_type,
      hardDeleteModal.tx!.reference_id,
      hardDeleteModal.reason.trim(),
    );

    hardDeleteModal.open = false;
    emit('notify', { type: 'success', message: 'Đã xóa vĩnh viễn giao dịch.' });
    await Promise.all([loadTransactions(), loadAuditLogs()]);
  });
}

async function submitEmergencyRefund() {
  if (!refundModal.tx || !isReasonValid(refundModal.reason)) {
    return;
  }

  await runAction('emergency-refund', async () => {
    const referenceId = Number(refundModal.tx!.reference_id);
    if (!Number.isFinite(referenceId)) {
      throw new Error('Invalid reference id for refund action.');
    }

    if (refundModal.tx!.transaction_type === 'sale') {
      await adminApi.emergencyRefundSale(referenceId, refundModal.reason.trim(), refundModal.refund_method);
    } else {
      await adminApi.emergencyRefundRental(referenceId, refundModal.reason.trim(), refundModal.refund_method);
    }

    refundModal.open = false;
    emit('notify', { type: 'success', message: 'Đã hoàn tất hoàn tiền khẩn cấp.' });
    await Promise.all([loadTransactions(), loadAuditLogs()]);
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

.field-checkbox {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 10px 0;
  font-size: 13px;
}

.btn-primary,
.btn-ghost,
.btn-danger,
.btn-warn,
.btn-row {
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

.btn-danger {
  background: #b91c1c;
  color: #ffffff;
}

.btn-warn {
  background: #c2410c;
  color: #ffffff;
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

.btn-primary:disabled,
.btn-ghost:disabled,
.btn-danger:disabled,
.btn-warn:disabled {
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
  width: min(520px, calc(100vw - 24px));
  background: #ffffff;
  border-radius: 16px;
  border: 1px solid #dbe4f0;
  padding: 18px;
}

.modal-card h3 {
  margin: 0;
  color: #0f172a;
}

.modal-subtitle {
  margin: 6px 0 10px;
  color: #475569;
  font-size: 13px;
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
