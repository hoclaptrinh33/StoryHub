<template>
  <section class="tab-shell">
    <button class="mobile-toggle" @click="leftOpen = !leftOpen">
      {{ leftOpen ? 'Ẩn bộ lọc' : 'Hiện bộ lọc' }}
    </button>

    <div class="tab-split">
      <aside class="left-panel" :class="{ open: leftOpen }">
        <div class="panel-card">
          <h3>Hành động người dùng</h3>
          <button class="btn-primary" @click="openCreateModal">Tạo người dùng</button>
          <button class="btn-ghost" :disabled="isBusy('load-users')" @click="loadUsers">
            {{ isBusy('load-users') ? 'Đang tải...' : 'Tải lại danh sách' }}
          </button>
          <p v-if="errorMap['load-users']" class="error-text">{{ errorMap['load-users'] }}</p>
        </div>

        <div class="panel-card">
          <h3>Thống kê</h3>
          <p class="stat-line">Tổng số: <strong>{{ users.length }}</strong></p>
          <p class="stat-line">Đang hoạt động: <strong>{{ activeUsersCount }}</strong></p>
          <p class="stat-line">Quản lý: <strong>{{ managerCount }}</strong></p>
        </div>
      </aside>

      <div class="right-panel">
        <article class="panel-card">
          <div class="card-head">
            <h3>Người dùng Hệ thống</h3>
            <span class="pill">{{ users.length }} người dùng</span>
          </div>

          <div class="table-wrap">
            <table class="table">
              <thead>
                <tr>
                  <th>Tên đăng nhập</th>
                  <th>Họ và tên</th>
                  <th>Vai trò</th>
                  <th>Trạng thái</th>
                  <th>Ngày tạo</th>
                  <th>Hành động</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="user in users" :key="user.id">
                  <td>{{ user.username }}</td>
                  <td>{{ user.full_name || 'N/A' }}</td>
                  <td>{{ user.role }}</td>
                  <td>
                    <span :class="user.is_active ? 'pill-ok' : 'pill-danger'">
                      {{ user.is_active ? 'Hoạt động' : 'Đã khóa' }}
                    </span>
                  </td>
                  <td>{{ formatDate(user.created_at) }}</td>
                  <td class="row-actions">
                    <button class="btn-row" @click="openEditModal(user)">Sửa</button>
                    <button class="btn-row warn" @click="toggleUserStatus(user)">
                      {{ user.is_active ? 'Khóa' : 'Mở khóa' }}
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <p v-if="errorMap['save-user']" class="error-text">{{ errorMap['save-user'] }}</p>
        </article>
      </div>
    </div>

    <Teleport to="body">
      <div v-if="createModal.open" class="modal-overlay">
        <div class="modal-card">
          <h3>Tạo người dùng hệ thống</h3>

          <label class="field-label">Tên đăng nhập</label>
          <input v-model="createModal.username" class="field-input" />

          <label class="field-label">Họ và tên</label>
          <input v-model="createModal.full_name" class="field-input" />

          <label class="field-label">Vai trò</label>
          <select v-model="createModal.role" class="field-input">
            <option value="cashier">Nhân viên thu ngân</option>
            <option value="manager">Quản lý</option>
          </select>

          <label class="field-label">Mật khẩu</label>
          <input v-model="createModal.password" class="field-input" type="password" />

          <div class="modal-actions">
            <button class="btn-ghost" @click="createModal.open = false">Hủy</button>
            <button class="btn-primary" :disabled="isBusy('save-user')" @click="submitCreateUser">
              {{ isBusy('save-user') ? 'Đang lưu...' : 'Tạo người dùng' }}
            </button>
          </div>
        </div>
      </div>

      <!-- Modal xác nhận khóa/mở khóa tài khoản -->
      <div v-if="toggleStatusModal.open" class="modal-overlay">
        <div class="modal-card">
          <h3>{{ toggleStatusModal.targetStatus ? 'Mở khóa tài khoản' : 'Khóa tài khoản' }}</h3>
          <p class="modal-subtitle">{{ toggleStatusModal.username }}</p>
          <p class="modal-warning" v-if="!toggleStatusModal.targetStatus">
            ⚠️ Tài khoản bị khóa sẽ không thể đăng nhập vào hệ thống.
          </p>

          <label class="field-label">Lý do (bắt buộc)</label>
          <textarea
            v-model="toggleStatusModal.reason"
            class="field-input"
            rows="3"
            placeholder="Nhập lý do khóa/mở khóa (tối thiểu 3 ký tự)"
          />

          <div class="modal-actions">
            <button class="btn-ghost" @click="toggleStatusModal.open = false">Hủy</button>
            <button
              :class="toggleStatusModal.targetStatus ? 'btn-primary' : 'btn-danger'"
              :disabled="isBusy('save-user') || !isReasonValid(toggleStatusModal.reason)"
              @click="submitToggleUserStatus"
            >
              <template v-if="isBusy('save-user')">Đang xử lý...</template>
              <template v-else>{{ toggleStatusModal.targetStatus ? 'Mở khóa' : 'Khóa tài khoản' }}</template>
            </button>
          </div>
        </div>
      </div>

      <div v-if="editModal.open" class="modal-overlay">
        <div class="modal-card">
          <h3>Cập nhật người dùng</h3>
          <p class="modal-subtitle">{{ editModal.username }}</p>

          <label class="field-label">Họ và tên</label>
          <input v-model="editModal.full_name" class="field-input" />

          <label class="field-label">Vai trò</label>
          <select v-model="editModal.role" class="field-input">
            <option value="cashier">Nhân viên thu ngân</option>
            <option value="manager">Quản lý</option>
          </select>

          <label class="field-checkbox">
            <input v-model="editModal.is_active" type="checkbox" />
            Đang hoạt động
          </label>

          <label class="field-label">Mật khẩu mới (không bắt buộc)</label>
          <input v-model="editModal.new_password" class="field-input" type="password" />

          <div class="modal-actions">
            <button class="btn-ghost" @click="editModal.open = false">Hủy</button>
            <button class="btn-primary" :disabled="isBusy('save-user')" @click="submitUpdateUser">
              {{ isBusy('save-user') ? 'Đang lưu...' : 'Lưu thay đổi' }}
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
import type { SystemUser } from '../../../services/storyhubApi';
import { useAdminApi } from '../../../composables/useAdminApi';

type ActionKey = 'load-users' | 'save-user';

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

const users = ref<SystemUser[]>([]);

const loadingMap = reactive<Record<ActionKey, boolean>>({
  'load-users': false,
  'save-user': false,
});

const errorMap = reactive<Record<ActionKey, string | null>>({
  'load-users': null,
  'save-user': null,
});

const createModal = reactive({
  open: false,
  username: '',
  full_name: '',
  role: 'cashier' as 'cashier' | 'manager',
  password: '',
});

const editModal = reactive({
  open: false,
  id: null as number | null,
  username: '',
  full_name: '',
  role: 'cashier' as 'cashier' | 'manager',
  is_active: true,
  new_password: '',
});

const activeUsersCount = computed(() => users.value.filter((user) => user.is_active).length);
const managerCount = computed(() => users.value.filter((user) => user.role === 'manager').length);

const toggleStatusModal = reactive({
  open: false,
  id: null as number | null,
  username: '',
  targetStatus: false, // trạng thái mới muốn set (true = mở khóa, false = khóa)
  reason: '',
});

onMounted(() => {
  if (props.isActive) {
    initialized.value = true;
    void loadUsers();
  }
});

watch(
  () => props.isActive,
  (isActive) => {
    if (isActive && !initialized.value) {
      initialized.value = true;
      void loadUsers();
    }
  },
);

watch(
  () => [users.value.length, activeUsersCount.value, managerCount.value],
  () => {
    emit('kpi', {
      primaryLabel: 'Người dùng',
      primaryValue: String(users.value.length),
      secondaryLabel: 'Đang hoạt động',
      secondaryValue: String(activeUsersCount.value),
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

async function loadUsers() {
  await runAction('load-users', async () => {
    users.value = await adminApi.fetchSystemUsers();
  });
}

function openCreateModal() {
  createModal.username = '';
  createModal.full_name = '';
  createModal.role = 'cashier';
  createModal.password = '';
  createModal.open = true;
}

function openEditModal(user: SystemUser) {
  editModal.id = user.id;
  editModal.username = user.username;
  editModal.full_name = user.full_name || '';
  editModal.role = user.role;
  editModal.is_active = user.is_active;
  editModal.new_password = '';
  editModal.open = true;
}

async function submitCreateUser() {
  if (!createModal.username.trim() || !createModal.password.trim()) {
    emit('notify', { type: 'error', message: 'Tên đăng nhập và mật khẩu là bắt buộc.' });
    return;
  }

  await runAction('save-user', async () => {
    await adminApi.createSystemUser({
      username: createModal.username.trim(),
      password: createModal.password,
      full_name: createModal.full_name.trim() || undefined,
      role: createModal.role,
    });

    createModal.open = false;
    emit('notify', { type: 'success', message: 'Tạo người dùng thành công.' });
    await loadUsers();
  });
}

async function submitUpdateUser() {
  if (editModal.id === null) {
    return;
  }

  await runAction('save-user', async () => {
    await adminApi.updateSystemUser(editModal.id!, {
      full_name: editModal.full_name.trim() || undefined,
      role: editModal.role,
      is_active: editModal.is_active,
      new_password: editModal.new_password.trim() || undefined,
    });

    editModal.open = false;
    emit('notify', { type: 'success', message: 'Cập nhật người dùng thành công.' });
    await loadUsers();
  });
}

function openToggleStatusModal(user: SystemUser) {
  toggleStatusModal.id = user.id;
  toggleStatusModal.username = user.username;
  toggleStatusModal.targetStatus = !user.is_active; // đảo ngược trạng thái hiện tại
  toggleStatusModal.reason = '';
  toggleStatusModal.open = true;
}

async function submitToggleUserStatus() {
  if (toggleStatusModal.id === null || !isReasonValid(toggleStatusModal.reason)) {
    return;
  }

  await runAction('save-user', async () => {
    await adminApi.updateSystemUser(toggleStatusModal.id!, {
      is_active: toggleStatusModal.targetStatus,
    });

    toggleStatusModal.open = false;
    const action = toggleStatusModal.targetStatus ? 'mở khóa' : 'khóa';
    emit('notify', { type: 'success', message: `Đã ${action} tài khoản thành công.` });
    await loadUsers();
  });
}

// Alias wrapper – được gọi từ template
function toggleUserStatus(user: SystemUser) {
  openToggleStatusModal(user);
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

.btn-danger {
  background: #b91c1c;
  color: #ffffff;
}

.modal-warning {
  margin: 8px 0;
  color: #c2410c;
  font-size: 13px;
  font-weight: 600;
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
