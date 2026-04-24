<template>
  <DefaultLayout>
    <div class="management-container">
      <div class="header-section">
        <h2 class="page-title">Quản lý Nghiệp vụ</h2>
        <div class="quick-stats">
          <div class="stat-item">
            <span class="label">Hợp đồng mới</span>
            <span class="value">12</span>
            <span class="trend up">+15%</span>
          </div>
          <div class="stat-item warning">
            <span class="label">Sắp quá hạn</span>
            <span class="value">08</span>
          </div>
          <div class="stat-item info">
            <span class="label">Lịch hẹn hôm nay</span>
            <span class="value">{{
              appointments.filter((a) => isToday(a.date)).length
            }}</span>
          </div>
        </div>
      </div>

      <div class="management-tabs">
        <button
          v-for="tab in tabs"
          :key="tab.id"
          :class="['tab-item', { active: currentTab === tab.id }]"
          @click="handleTabClick(tab.id)"
        >
          <span class="material-icons">{{ tab.icon }}</span>
          {{ tab.label }}
        </button>
      </div>

      <Transition name="tab-fade" mode="out-in">
        <div :key="currentTab" class="tab-content card">
          <!-- Tab Hợp đồng -->
          <div v-if="currentTab === 'contracts'" class="tab-pane">
            <div class="table-header">
              <div class="header-left">
                <h3>Danh sách hợp đồng thuê</h3>
                <p>Quản lý và gia hạn các hợp đồng đang diễn ra</p>
              </div>
              <div class="search-box">
                <span class="material-icons">search</span>
                <input
                  type="text"
                  v-model="searchQuery"
                  placeholder="Tìm số hợp đồng, tên khách..."
                />
              </div>
            </div>
            <div class="table-responsive">
              <table>
                <thead>
                  <tr>
                    <th>Số HĐ</th>
                    <th>Khách hàng</th>
                    <th>Ngày thuê</th>
                    <th>Hạn trả</th>
                    <th>Trạng thái</th>
                    <th>Hành động</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="contract in filteredContracts" :key="contract.id">
                    <td>
                      <span class="id-tag">{{ contract.id }}</span>
                    </td>
                    <td>
                      <strong>{{ contract.customer }}</strong>
                    </td>
                    <td class="date-cell">{{ contract.startDate }}</td>
                    <td
                      class="date-cell"
                      :class="{ 'text-danger': contract.isOverdue }"
                    >
                      {{ contract.endDate }}
                    </td>
                    <td>
                      <span :class="['badge-glass', contract.statusType]">
                        {{ contract.statusLabel }}
                      </span>
                    </td>
                    <td class="actions">
                      <button
                        class="btn-icon-bg"
                        title="Gia hạn"
                        @click="handleExtend(contract)"
                      >
                        <span class="material-icons">history</span>
                      </button>
                      <button class="btn-icon-bg info" title="Xem chi tiết">
                        <span class="material-icons">visibility</span>
                      </button>
                    </td>
                  </tr>
                  <tr v-if="filteredContracts.length === 0">
                    <td colspan="6" class="empty-row">
                      Không tìm thấy kết quả phù hợp
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <!-- Tab Hoàn trả truyện -->
          <div v-if="currentTab === 'refunds'" class="tab-pane">
            <div class="refund-workflow-container">
              <div class="workflow-header text-center">
                <h3>Kiểm định trả tại màn chuyên dụng</h3>
                <p>
                  Tab này đã liên kết trực tiếp tới màn mới để xử lý quét hợp
                  đồng, quét item và kết toán đồng nhất.
                </p>
              </div>

              <div class="workflow-card-premium">
                <div class="alert-info-glass">
                  <span class="material-icons">open_in_new</span>
                  <span
                    >Nhấn nút bên dưới để mở màn <strong>Kiểm định trả</strong>
                    tại đường dẫn <strong>/hoan-tra</strong>.</span
                  >
                </div>

                <button class="btn-gradient" type="button" @click="openReturnScreen">
                  <span class="material-icons">assignment_return</span>
                  Mở màn kiểm định trả
                </button>
              </div>
            </div>
          </div>

          <!-- Tab Đặt lịch hẹn -->
          <div v-if="currentTab === 'appointments'" class="tab-pane">
            <div class="appointments-dashboard">
              <div class="form-aside">
                <div class="card-glass">
                  <div class="card-title">
                    <span class="material-icons">auto_stories</span>
                    <h3>Tạo lịch hẹn</h3>
                  </div>

                  <div class="appointment-form-premium">
                    <div class="field">
                      <label>Khách hàng</label>
                      <input
                        v-model="newAppointment.customer"
                        type="text"
                        placeholder="Tên khách hàng..."
                      />
                    </div>

                    <div class="field">
                      <label>Chọn bộ truyện</label>
                      <select
                        v-model="selectedTitleId"
                        class="select-premium"
                        @change="selectedVolume = ''"
                      >
                        <option value="" disabled>-- Chọn bộ truyện --</option>
                        <option
                          v-for="title in bookDB"
                          :key="title.id"
                          :value="title.id"
                        >
                          {{ title.name }}
                        </option>
                      </select>
                    </div>

                    <div class="field-row">
                      <div class="field flex-2">
                        <label>Tập</label>
                        <select
                          v-model="selectedVolume"
                          class="select-premium"
                          :disabled="!selectedTitle"
                        >
                          <option value="" disabled>Tập</option>
                          <option
                            v-for="vol in selectedTitle?.volumes"
                            :key="vol"
                            :value="vol"
                          >
                            Tập {{ vol }}
                          </option>
                        </select>
                      </div>
                      <div class="field flex-3">
                        <label>Ngày hẹn</label>
                        <input v-model="newAppointment.date" type="date" />
                      </div>
                    </div>

                    <div class="field">
                      <label>Ghi chú thêm</label>
                      <textarea
                        v-model="newAppointment.note"
                        placeholder="SĐT hoặc yêu cầu khác..."
                      ></textarea>
                    </div>

                    <button
                      class="btn-gradient"
                      @click="addStructuredAppointment"
                    >
                      <span class="material-icons">event_available</span>
                      Lưu lịch hẹn
                    </button>
                  </div>
                </div>
              </div>

              <div class="list-main">
                <div class="card-glass">
                  <div class="card-header-flex">
                    <div class="title">
                      <h3>Danh sách chờ</h3>
                      <span class="badge-count">{{
                        appointments.filter((a) => a.status === "pending")
                          .length
                      }}</span>
                    </div>
                    <div class="filters">
                      <!-- Ví dụ filter nhanh -->
                    </div>
                  </div>

                  <div class="appointment-grid-premium">
                    <div
                      v-for="app in appointments"
                      :key="app.id"
                      :class="['appointment-tile', app.status]"
                    >
                      <div class="tile-header">
                        <span class="date">{{ formatDate(app.date) }}</span>
                        <span
                          v-if="isOverdue(app.date) && app.status === 'pending'"
                          class="overdue-tag"
                          >Quá hạn</span
                        >
                      </div>
                      <div class="tile-body">
                        <h4 class="customer-name">{{ app.customer }}</h4>
                        <div class="book-info">
                          <span class="material-icons">book</span>
                          {{ app.bookName }}
                        </div>
                        <p class="note" v-if="app.note">{{ app.note }}</p>
                      </div>
                      <div class="tile-footer">
                        <div class="actions" v-if="app.status === 'pending'">
                          <button
                            class="btn-mini-success"
                            @click="completeAppointment(app.id)"
                          >
                            <span class="material-icons">done</span>
                          </button>
                          <button
                            class="btn-mini-danger"
                            @click="deleteAppointment(app.id)"
                          >
                            <span class="material-icons">delete_outline</span>
                          </button>
                        </div>
                        <span v-else class="done-label">Đã hoàn thành</span>
                      </div>
                    </div>
                    <div
                      v-if="appointments.length === 0"
                      class="empty-state-lux"
                    >
                      <span class="material-icons">calendar_today</span>
                      <p>Không có lịch hẹn nào</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Tab Lịch sử -->
          <div v-if="currentTab === 'history'" class="tab-pane">
            <div class="table-header">
              <h3>Nhật ký giao dịch</h3>
              <p>Theo dõi mọi thay đổi trên hệ thống</p>
            </div>
            <div class="table-responsive">
              <table>
                <thead>
                  <tr>
                    <th>Thời gian</th>
                    <th>Loại</th>
                    <th>Mô tả chi tiết</th>
                    <th class="text-right">Người thực hiện</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="log in transactionHistory" :key="log.id">
                    <td class="text-muted">{{ log.time }}</td>
                    <td>
                      <span class="type-indicator-wrapper">
                        <span :class="['type-dot', slugify(log.type)]"></span>
                        {{ log.type }}
                      </span>
                    </td>
                    <td>{{ log.desc }}</td>
                    <td class="text-right">
                      <strong>{{ log.user }}</strong>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
          <!-- Tab Lịch sử kho -->
          <div v-if="currentTab === 'inventory_history'" class="tab-pane">
  <div class="table-header">
    <div class="header-left">
      <h3>Biến động kho sách</h3>
      <p>Theo dõi các hoạt động thêm, sửa, xóa đầu truyện, tập truyện, bản sao và chuyển đổi sang thuê</p>
    </div>
    <div class="header-right">
      <button class="btn-icon-bg" @click="refreshHistory" :disabled="isLoadingHistory" title="Làm mới">
        <span class="material-icons">refresh</span>
      </button>
      <div class="search-box">
        <span class="material-icons">search</span>
        <input
          type="text"
          v-model="historySearchQuery"
          placeholder="Tìm theo hành động, đối tượng, ID..."
        />
      </div>
    </div>
  </div>

  <div v-if="isLoadingHistory && inventoryHistory.length === 0" class="loading-state">
    <div class="spinner"></div> <span>Đang tải dữ liệu...</span>
  </div>
  <div v-else class="table-container">
    <div class="table-responsive">
      <table class="history-table">
        <thead>
          <tr>
            <th>Thời gian</th>
            <th>Hành động</th>
            <th>Đối tượng</th>
            <th>ID</th>
            <th>Người thực hiện</th>
            <th>Chi tiết thay đổi</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in filteredHistory" :key="item.id">
            <td class="text-muted">{{ formatDateTime(item.timestamp) }}</td>
            <td><span :class="['badge-glass', getActionClass(item.action)]">{{ getActionLabel(item.action) }}</span></td>
            <td><span class="entity-type">{{ getEntityLabel(item.entity_type) }}</span></td>
            <td><span class="id-tag">{{ item.entity_id }}</span></td>
            <td class="user-cell">
              <span class="user-name">{{ item.user_name || `User #${item.user_id}` }}</span>
              <small class="ip-addr" v-if="item.ip_address">{{ item.ip_address }}</small>
            </td>
            <td class="change-detail">
              <div class="change-preview">
                <span v-if="item.before && item.after">🔁 {{ formatChange(item.before, item.after) }}</span>
                <span v-else-if="item.after">➕ {{ formatChange(null, item.after) }}</span>
                <span v-else-if="item.before">❌ {{ formatChange(item.before, null) }}</span>
                <span v-else>—</span>
              </div>
            </td>
          </tr>
          <tr v-if="filteredHistory.length === 0">
            <td colspan="6" class="empty-row">Không có dữ liệu lịch sử kho</td>
          </tr>
        </tbody>
      </table>
    </div>
    
    <div v-if="hasMoreHistory" class="load-more-section">
       <button class="btn-outline-premium" @click="loadMoreHistory" :disabled="isLoadingHistory">
         <span v-if="isLoadingHistory" class="spinner-mini"></span>
         {{ isLoadingHistory ? 'Đang tải...' : 'Xem thêm bản ghi' }}
       </button>
    </div>
  </div>
</div>
<div v-else-if="historyError" class="error-state">
  <span class="material-icons">error_outline</span>
  <p>{{ historyError }}</p>
  <button @click="refreshHistory" class="btn-outline-premium">Thử lại</button>
</div>
        </div>
      </Transition>
    </div>
  </DefaultLayout>
</template>

<script setup lang="ts">
import { computed, inject, ref } from "vue";
import { useRouter } from "vue-router";
import { fetchInventoryHistory, type InventoryHistoryItem } from '../services/storyhubApi';
import { useAuthStore } from '../stores/auth';


import DefaultLayout from "../components/layout/defaultLayout.vue";

interface ContractSummary {
  id: string;
  customer: string;
  startDate: string;
  endDate: string;
  statusLabel: string;
  statusType: "success" | "warning" | "danger";
  isOverdue: boolean;
  expectedRefund: number;
}

interface Appointment {
  id: number;
  customer: string;
  bookName: string;
  date: string;
  note: string;
  status: "pending" | "completed";
}
const authStore = useAuthStore();
const token = computed(() => authStore.token ?? 'manager-demo');
const historyError = ref('')
const inventoryHistory = ref<InventoryHistoryItem[]>([]);
const isLoadingHistory = ref(false);
const historySearchQuery = ref('');
const historyOffset = ref(0);
const historyLimit = 100;
const hasMoreHistory = ref(true);

const loadInventoryHistory = async (isLoadMore = false) => {
  if (!authStore.token) {
    addNotification?.('error', 'Vui lòng đăng nhập để xem lịch sử kho');
    router.push('/login');
    return;
  }
  if (!isLoadMore) {
    historyOffset.value = 0;
    inventoryHistory.value = [];
    hasMoreHistory.value = true;
  }
  
   if (isLoadingHistory.value) return;
  isLoadingHistory.value = true;
  try {
    const data = await fetchInventoryHistory(historyLimit, historyOffset.value, token.value);
    if (data.length < historyLimit) {
      hasMoreHistory.value = false;
    }
    
    if (isLoadMore) {
      inventoryHistory.value = [...inventoryHistory.value, ...data];
    } else {
      inventoryHistory.value = data;
    }
    
    historyOffset.value += data.length;
  } catch (err: any) {
    console.error('Inventory history error:', err);
    let errorMsg = err.message || 'Không thể tải lịch sử kho';
    if (err.status === 401) errorMsg = 'Phiên đăng nhập hết hạn, vui lòng đăng nhập lại';
    else if (err.status === 403) errorMsg = 'Bạn không có quyền xem lịch sử kho';
    addNotification?.('error', errorMsg);

    inventoryHistory.value = [];
  } finally {
    isLoadingHistory.value = false;
  }
};

const refreshHistory = () => loadInventoryHistory(false);
const loadMoreHistory = () => loadInventoryHistory(true);

const slugify = (text: string) => {
  if (text.includes("Cho")) return "rental";
  if (text.includes("Hoàn")) return "refund";
  if (text.includes("Gia")) return "extend";
  return "default";
};

const router = useRouter();
const currentTab = ref("contracts");
const searchQuery = ref("");

const addNotification = inject("addNotification") as (
  type: string,
  msg: string,
) => void;
const showConfirm = inject("showConfirm") as (
  msg: string,
  title?: string,
) => Promise<boolean>;

const bookDB = ref([
  { id: 1, name: "One Piece", volumes: [100, 101, 102, 103, 104, 105] },
  { id: 2, name: "Detective Conan", volumes: [90, 91, 98, 99, 100] },
  { id: 3, name: "Spy x Family", volumes: [1, 2, 3, 4, 10, 11] },
  { id: 4, name: "Jujutsu Kaisen", volumes: [0, 15, 18, 20, 22] },
]);

const selectedTitleId = ref<number | "">("");
const selectedVolume = ref<number | "">("");

const selectedTitle = computed(() =>
  bookDB.value.find((book) => book.id === selectedTitleId.value),
);

const contracts = ref<ContractSummary[]>([
  {
    id: "2001",
    customer: "Trần Thị Bình",
    startDate: "15/04/2026",
    endDate: "20/04/2026",
    statusLabel: "Đang thuê",
    statusType: "success",
    isOverdue: false,
    expectedRefund: 65000,
  },
  {
    id: "2002",
    customer: "Lê Minh Châu",
    startDate: "08/04/2026",
    endDate: "12/04/2026",
    statusLabel: "Đã đóng",
    statusType: "warning",
    isOverdue: false,
    expectedRefund: 0,
  },
  {
    id: "2003",
    customer: "Nguyễn Văn A",
    startDate: "10/04/2026",
    endDate: "15/04/2026",
    statusLabel: "Quá hạn",
    statusType: "danger",
    isOverdue: true,
    expectedRefund: 0,
  },
]);

const appointments = ref<Appointment[]>([
  {
    id: 1,
    customer: "Lê Văn C",
    bookName: "One Piece - Tập 105",
    date: "2026-04-20",
    note: "SĐT: 0987654321",
    status: "pending",
  },
  {
    id: 2,
    customer: "Phạm Thị D",
    bookName: "Detective Conan - Tập 98",
    date: "2026-04-18",
    note: "Gọi trước 1 tiếng",
    status: "pending",
  },
]);

const transactionHistory = ref([
  {
    id: 1,
    time: "14:30 17/04/2026",
    type: "Cho thuê",
    desc: "HĐ-1005: Cho thuê 3 cuốn truyện Conan",
    user: "Admin",
  },
  {
    id: 2,
    time: "12:15 17/04/2026",
    type: "Hoàn tiền",
    desc: "Hoàn trả HĐ-882 (Sách lỗi)",
    user: "Staff",
  },
  {
    id: 3,
    time: "09:00 17/04/2026",
    type: "Gia hạn",
    desc: "Gia hạn HĐ-990 thêm 3 ngày",
    user: "Admin",
  },
]);

const newAppointment = ref({
  customer: "",
  date: "",
  note: "",
});

const tabs = [
  { id: "contracts", label: "Hợp đồng", icon: "description" },
  { id: "refunds", label: "Hoàn trả", icon: "assignment_return" },
  { id: "appointments", label: "Đặt lịch", icon: "event_available" },
  { id: "history", label: "Lịch sử", icon: "receipt_long" },
  { id: "inventory_history", label: "Lịch sử kho", icon: "inventory_2" }
];

const openReturnScreen = async () => {
  await router.push("/hoan-tra");
};

const handleTabClick = async (tabId: string) => {
  if (tabId === "refunds") {
    await openReturnScreen();
    return;
  }
  currentTab.value = tabId;
  if (tabId === 'inventory_history' && inventoryHistory.value.length === 0) {
    await loadInventoryHistory();
  }
};
// hỗ trợ unils
const formatDateTime = (isoString: string) => {
  if (!isoString) return '';
  const date = new Date(isoString);
  return date.toLocaleString('vi-VN');
};

const getActionLabel = (action: string) => {
  const map: Record<string, string> = {
    'CREATE_TITLE': 'Thêm đầu truyện',
    'UPDATE_TITLE': 'Sửa đầu truyện',
    'DELETE_TITLE': 'Xóa đầu truyện',
    'INVENTORY_VOLUME_CREATED': 'Thêm tập truyện',
    'UPDATE_VOLUME': 'Sửa tập truyện',
    'DELETE_VOLUME': 'Xóa tập truyện',
    'CREATE_ITEM': 'Thêm bản sao',
    'UPDATE_ITEM': 'Sửa bản sao',
    'DELETE_ITEM': 'Xóa bản sao',
    'INVENTORY_TO_RENTAL': 'Chuyển sang thuê',
    'INVENTORY_COVER_IMPORTED': 'Nhập ảnh bìa',
    'INVENTORY_VOLUME_PRICE_UPDATED': 'Cập nhật giá tập',
  };
  return map[action] || action;
};

const getActionClass = (action: string) => {
  if (action.includes('CREATE') || action.includes('IMPORTED')) return 'success';
  if (action.includes('UPDATE') || action.includes('PRICE_UPDATED')) return 'warning';
  if (action.includes('DELETE')) return 'danger';
  if (action.includes('TO_RENTAL')) return 'info';
  return 'secondary';
};

const getEntityLabel = (entityType: string) => {
  const map: Record<string, string> = {
    'title': 'Đầu truyện',
    'volume': 'Tập truyện',
    'item': 'Bản sao',
    'cover': 'Ảnh bìa',
  };
  return map[entityType] || entityType;
};

const formatChange = (before: any, after: any) => {
  if (!before && after) {
    // Thêm mới: chỉ lấy các trường chính
    const keys = Object.keys(after).slice(0, 3);
    return keys.map(k => `${k}: ${after[k]}`).join(', ') + (Object.keys(after).length > 3 ? '…' : '');
  }
  if (before && !after) {
    // Xóa
    const keys = Object.keys(before).slice(0, 3);
    return keys.map(k => `${k}: ${before[k]}`).join(', ') + (Object.keys(before).length > 3 ? '…' : '');
  }
  if (before && after) {
    // Sửa: chỉ hiển thị các trường thay đổi
    const changed = Object.keys(after).filter(key => before[key] !== after[key]);
    if (changed.length === 0) return 'Không thay đổi';
    return changed.map(key => `${key}: ${before[key]} → ${after[key]}`).join(', ');
  }
  return '—';
};

const filteredHistory = computed(() => {
  const query = historySearchQuery.value.toLowerCase();
  if (!query) return inventoryHistory.value;
  return inventoryHistory.value.filter(item =>
    item.action.toLowerCase().includes(query) ||
    item.entity_type.toLowerCase().includes(query) ||
    item.entity_id.toLowerCase().includes(query) ||
    (item.user_name?.toLowerCase().includes(query))
  );
});

const filteredContracts = computed(() => {
  const query = searchQuery.value.toLowerCase();
  if (!query) {
    return contracts.value;
  }
  return contracts.value.filter(
    (contract) =>
      contract.id.toLowerCase().includes(query) ||
      contract.customer.toLowerCase().includes(query),
  );
});

const addStructuredAppointment = () => {
  if (
    !newAppointment.value.customer ||
    !selectedTitleId.value ||
    !selectedVolume.value ||
    !newAppointment.value.date
  ) {
    addNotification(
      "warning",
      "Vui lòng chọn bộ truyện, tập và nhập đầy đủ thông tin khách hàng.",
    );
    return;
  }

  const bookName = `${selectedTitle.value?.name} - Tập ${selectedVolume.value}`;
  const newId = Date.now();

  appointments.value.unshift({
    id: newId,
    customer: newAppointment.value.customer,
    bookName,
    date: newAppointment.value.date,
    note: newAppointment.value.note,
    status: "pending",
  });

  addNotification("success", `Đã tạo lịch hẹn cho bộ truyện: ${bookName}`);

  newAppointment.value = { customer: "", date: "", note: "" };
  selectedTitleId.value = "";
  selectedVolume.value = "";
};

const handleExtend = async (contract: ContractSummary) => {
  const ok = await showConfirm(
    `Bạn có chắc chắn muốn gia hạn hợp đồng ${contract.id} thêm 3 ngày?`,
    "Gia hạn hợp đồng",
  );
  if (ok) {
    addNotification(
      "success",
      `Đã gia hạn thành công cho hợp đồng ${contract.id}`,
    );
  }
};

const deleteAppointment = async (id: number) => {
  const ok = await showConfirm("Bạn có muốn hủy lịch hẹn này?", "Hủy lịch");
  if (ok) {
    appointments.value = appointments.value.filter(
      (appointment) => appointment.id !== id,
    );
    addNotification("success", "Đã hủy lịch hẹn.");
  }
};

const completeAppointment = (id: number) => {
  const appointment = appointments.value.find((entry) => entry.id === id);
  if (appointment) {
    appointment.status = "completed";
  }
};

const isToday = (dateStr: string) =>
  dateStr === new Date().toISOString().slice(0, 10);

const isOverdue = (dateStr: string) =>
  dateStr < new Date().toISOString().slice(0, 10);

const formatDate = (dateStr: string) => {
  if (!dateStr) {
    return "";
  }

  const [year, month, day] = dateStr.split("-");
  return `${day}/${month}/${year}`;
};
</script>

<style scoped>
@import url("https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap");

.management-container {
  padding: 32px;
  background: #fdfdfd;
  background-image: radial-gradient(#e2e8f0 0.5px, transparent 0.5px);
  background-size: 24px 24px;
  min-height: 100vh;
  font-family: "Plus Jakarta Sans", sans-serif;
}

/* Header & Stats */
.header-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 32px;
  animation: fadeInDown 0.6s ease;
}
.page-title {
  font-size: 2rem;
  font-weight: 800;
  color: #0f172a;
  letter-spacing: -0.04em;
  margin: 0;
}

.quick-stats {
  display: flex;
  gap: 20px;
}
.stat-item {
  background: white;
  padding: 16px 24px;
  border-radius: 20px;
  border: 1px solid #f1f5f9;
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.02);
  display: flex;
  flex-direction: column;
  min-width: 160px;
  transition: 0.3s;
}
.stat-item:hover {
  transform: translateY(-3px);
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.05);
}
.stat-item .label {
  font-size: 0.7rem;
  color: #94a3b8;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}
.stat-item .value {
  font-size: 1.75rem;
  font-weight: 800;
  color: #0f172a;
  margin: 4px 0;
}
.stat-item .trend {
  font-size: 0.75rem;
  font-weight: 700;
  color: #059669;
  background: #f0fdf4;
  padding: 2px 8px;
  border-radius: 99px;
  width: fit-content;
}
.stat-item.warning .value {
  color: #ea580c;
}
.stat-item.info .value {
  color: #2563eb;
}

/* Tabs Layout */
.management-tabs {
  display: flex;
  gap: 12px;
  margin-bottom: 32px;
  padding: 6px;
  background: #f1f5f9;
  border-radius: 18px;
  width: fit-content;
  box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.05);
}
.tab-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 24px;
  border-radius: 14px;
  border: none;
  background: transparent;
  color: #64748b;
  cursor: pointer;
  font-weight: 700;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  font-size: 0.95rem;
}
.tab-item:hover {
  color: #1e293b;
  background: rgba(255, 255, 255, 0.5);
}
.tab-item.active {
  background: white;
  color: #2563eb;
  box-shadow:
    0 10px 15px -3px rgba(37, 99, 235, 0.1),
    0 4px 6px -2px rgba(37, 99, 235, 0.05);
}

/* Content Card Glass */
.card {
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(12px);
  padding: 40px;
  border-radius: 32px;
  border: 1px solid rgba(255, 255, 255, 0.3);
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.05);
}

/* Table Style Premium */
.table-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  margin-bottom: 30px;
}
.table-header h3 {
  font-size: 1.5rem;
  font-weight: 800;
  color: #0f172a;
  margin: 0 0 4px 0;
}
.table-header p {
  color: #64748b;
  font-size: 0.9rem;
  margin: 0;
}

.search-box {
  position: relative;
  width: 360px;
}
.search-box .material-icons {
  position: absolute;
  left: 16px;
  top: 50%;
  transform: translateY(-50%);
  color: #2563eb;
  font-size: 20px;
}
.search-box input {
  width: 100%;
  padding: 14px 14px 14px 52px;
  border: 2px solid #f1f5f9;
  border-radius: 18px;
  font-size: 0.95rem;
  outline: none;
  transition: 0.3s;
  background: white;
}
.search-box input:focus {
  border-color: #2563eb;
  box-shadow: 0 0 0 5px rgba(37, 99, 235, 0.1);
}

.table-responsive {
  width: 100%;
}
table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0 12px;
}
th {
  text-align: left;
  padding: 12px 24px;
  color: #94a3b8;
  font-weight: 700;
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.1em;
}
td {
  padding: 20px 24px;
  background: white;
  border-top: 1px solid #f1f5f9;
  border-bottom: 1px solid #f1f5f9;
  color: #1e293b;
  font-size: 0.95rem;
  transition: 0.2s;
}
td:first-child {
  border-left: 1px solid #f1f5f9;
  border-top-left-radius: 16px;
  border-bottom-left-radius: 16px;
}
td:last-child {
  border-right: 1px solid #f1f5f9;
  border-top-right-radius: 16px;
  border-bottom-right-radius: 16px;
}
tr:hover td {
  background: #f8fafc;
  border-color: #e2e8f0;
}

.id-tag {
  background: #f1f5f9;
  color: #475569;
  padding: 4px 12px;
  border-radius: 8px;
  font-family: monospace;
  font-weight: 700;
}
.badge-glass {
  padding: 6px 14px;
  border-radius: 10px;
  font-size: 0.75rem;
  font-weight: 800;
  text-transform: uppercase;
}
.badge-glass.success {
  background: #dcfce7;
  color: #166534;
}
.badge-glass.warning {
  background: #fef3c7;
  color: #92400e;
}
.badge-glass.danger {
  background: #fee2e2;
  color: #991b1b;
}

.btn-icon-bg {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  border: none;
  background: #f1f5f9;
  color: #64748b;
  cursor: pointer;
  transition: 0.3s;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  margin-right: 8px;
}
.btn-icon-bg:hover {
  background: #2563eb;
  color: white;
  transform: rotate(15deg);
}
.btn-icon-bg.info:hover {
  background: #0f172a;
}

/* Refund Section Premium */
.refund-workflow-container {
  max-width: 800px;
  margin: 0 auto;
}
.workflow-header h3 {
  font-size: 2rem;
  font-weight: 900;
  color: #0f172a;
}
.workflow-card-premium {
  background: white;
  border-radius: 40px;
  padding: 48px;
  box-shadow: 0 40px 100px -20px rgba(0, 0, 0, 0.08);
  border: 1px solid #f1f5f9;
  margin-top: 32px;
}

.alert-info-glass {
  background: #eff6ff;
  color: #1e40af;
  padding: 16px 24px;
  border-radius: 20px;
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 32px;
  font-size: 0.95rem;
}

.hotkey-legend {
  margin: -8px 0 20px 0;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 10px 14px;
  color: #475569;
  font-size: 0.82rem;
}

.hotkey-legend kbd {
  padding: 2px 6px;
  border-radius: 6px;
  border: 1px solid #cbd5e1;
  background: white;
  font-family: inherit;
  font-weight: 700;
  color: #1e293b;
}

.mega-search {
  position: relative;
  display: flex;
  gap: 12px;
  margin-top: 12px;
}
.mega-search.scan-highlight {
  border-radius: 24px;
  box-shadow: 0 0 0 3px rgba(22, 163, 74, 0.25);
}
.mega-search input {
  flex: 1;
  padding: 20px 20px 20px 60px;
  border: 2px solid #f1f5f9;
  border-radius: 24px;
  font-size: 1.1rem;
  outline: none;
  transition: 0.3s;
  font-weight: 600;
}
.mega-search input:focus {
  border-color: #2563eb;
  background: #f8fafc;
}
.mega-search .material-icons {
  position: absolute;
  left: 24px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 28px;
  color: #2563eb;
}
.btn-action-primary {
  padding: 0 32px;
  background: #2563eb;
  color: white;
  border: none;
  border-radius: 20px;
  font-weight: 800;
  cursor: pointer;
  transition: 0.3s;
}
.btn-action-primary:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.focused-preview-card {
  margin-top: 40px;
  background: #fafafa;
  border-radius: 28px;
  padding: 32px;
  border: 2px solid #2563eb;
  border-style: dashed;
}
.preview-status {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #059669;
  font-weight: 800;
  font-size: 0.8rem;
  text-transform: uppercase;
  margin-bottom: 24px;
}
.dot-active {
  width: 8px;
  height: 8px;
  background: #059669;
  border-radius: 50%;
  animation: pulse 2s infinite;
}

.customer-preview {
  display: flex;
  align-items: center;
  gap: 20px;
}
.customer-preview .avatar {
  width: 64px;
  height: 64px;
  background: #2563eb;
  color: white;
  border-radius: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  font-weight: 900;
}
.customer-preview h4 {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 800;
  color: #0f172a;
}

.money-preview {
  text-align: right;
  border-left: 1px solid #e2e8f0;
  padding-left: 32px;
  flex: 1;
}
.money-preview .label {
  font-size: 0.8rem;
  font-weight: 700;
  color: #64748b;
}
.money-preview .amount {
  display: block;
  font-size: 2.25rem;
  font-weight: 900;
  color: #059669;
}

.btn-confirm-refund {
  width: 100%;
  margin-top: 32px;
  padding: 20px;
  background: #059669;
  color: white;
  border: none;
  border-radius: 20px;
  font-weight: 800;
  font-size: 1.1rem;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  cursor: pointer;
  transition: 0.3s;
}
.btn-confirm-refund:hover {
  background: #047857;
  transform: translateY(-4px);
  box-shadow: 0 20px 25px -5px rgba(5, 150, 105, 0.4);
}
.btn-confirm-refund:disabled {
  opacity: 0.7;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

/* Appointment Dashboard Lux */
.appointments-dashboard {
  display: grid;
  grid-template-columns: 380px 1fr;
  gap: 32px;
}
.card-glass {
  background: white;
  border-radius: 28px;
  padding: 32px;
  border: 1px solid #f1f5f9;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.03);
  height: 100%;
}
.card-title {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 32px;
}
.card-title .material-icons {
  color: #2563eb;
  font-size: 32px;
}
.card-title h3 {
  margin: 0;
  font-weight: 800;
  color: #0f172a;
}

.appointment-form-premium {
  display: flex;
  flex-direction: column;
  gap: 24px;
}
.field label {
  display: block;
  font-size: 0.8rem;
  font-weight: 800;
  color: #475569;
  margin-bottom: 10px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}
.field input,
.field textarea,
.select-premium {
  width: 100%;
  padding: 14px 18px;
  border: 2px solid #f1f5f9;
  border-radius: 16px;
  outline: none;
  transition: 0.3s;
  font-family: inherit;
  font-weight: 600;
}
.field textarea {
  height: 100px;
  resize: none;
}
.select-premium {
  appearance: none;
  background: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='%232563eb' stroke-width='3' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpolyline points='6 9 12 15 18 9'%3E%3C/polyline%3E%3C/svg%3E")
    no-repeat right 16px center;
  background-size: 20px;
  background-color: white;
}
.field input:focus,
.select-premium:focus {
  border-color: #2563eb;
  background: #f8fafc;
}

.btn-gradient {
  padding: 18px;
  background: linear-gradient(135deg, #2563eb, #7c3aed);
  color: white;
  border: none;
  border-radius: 18px;
  font-weight: 800;
  font-size: 1rem;
  cursor: pointer;
  transition: 0.3s;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
}
.btn-gradient:hover {
  transform: translateY(-3px);
  box-shadow: 0 15px 20px -5px rgba(124, 58, 237, 0.3);
}

/* Appointment Grid lux */
.appointment-grid-premium {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
}
.appointment-tile {
  background: #fdfdfd;
  padding: 24px;
  border-radius: 24px;
  border: 1px solid #f1f5f9;
  transition: 0.3s;
  position: relative;
}
.appointment-tile:hover {
  background: white;
  border-color: #2563eb;
  transform: scale(1.02);
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05);
}

.tile-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.tile-header .date {
  font-size: 0.8rem;
  font-weight: 800;
  color: #94a3b8;
}
.overdue-tag {
  background: #fee2e2;
  color: #ef4444;
  padding: 4px 10px;
  border-radius: 8px;
  font-size: 0.7rem;
  font-weight: 800;
  text-transform: uppercase;
}

.customer-name {
  margin: 0 0 10px 0;
  font-size: 1.15rem;
  font-weight: 800;
  color: #0f172a;
}
.book-info {
  background: #eff6ff;
  color: #2563eb;
  padding: 8px 14px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.85rem;
  font-weight: 700;
}
.book-info .material-icons {
  font-size: 18px;
}

.tile-footer {
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid #f1f5f9;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.btn-mini-success {
  background: #dcfce7;
  color: #059669;
  border: none;
  width: 36px;
  height: 36px;
  border-radius: 10px;
  cursor: pointer;
  transition: 0.2s;
}
.btn-mini-danger {
  background: #fee2e2;
  color: #ef4444;
  border: none;
  width: 36px;
  height: 36px;
  border-radius: 10px;
  cursor: pointer;
  transition: 0.2s;
}
.btn-mini-success:hover {
  background: #059669;
  color: white;
}
.btn-mini-danger:hover {
  background: #ef4444;
  color: white;
}

.appointment-tile.completed {
  opacity: 0.6;
  background: #f8fafc;
}
.done-label {
  font-size: 0.8rem;
  font-weight: 700;
  color: #059669;
  font-style: italic;
}

/* History Styles */
.type-indicator-wrapper {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 700;
  color: #475569;
}
.type-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  opacity: 0.8;
}
.type-dot.rental {
  background: #2563eb;
  box-shadow: 0 0 10px rgba(37, 99, 235, 0.4);
}
.type-dot.refund {
  background: #ea580c;
  box-shadow: 0 0 10px rgba(234, 88, 12, 0.4);
}
.type-dot.extend {
  background: #059669;
  box-shadow: 0 0 10px rgba(5, 150, 105, 0.4);
}
.type-dot.default {
  background: #94a3b8;
}

/* Transitions */
.tab-fade-enter-active {
  animation: fadeIn 0.4s ease;
}
.tab-fade-leave-active {
  animation: fadeOut 0.3s ease;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
@keyframes fadeOut {
  from {
    opacity: 1;
    transform: translateY(0);
  }
  to {
    opacity: 0;
    transform: translateY(-10px);
  }
}
@keyframes pulse {
  0% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.5;
    transform: scale(1.5);
  }
  100% {
    opacity: 1;
    transform: scale(1);
  }
}
@keyframes fadeInDown {
  from {
    opacity: 0;
    transform: translateY(-20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Responsive */
@media (max-width: 1200px) {
  .appointments-dashboard {
    grid-template-columns: 1fr;
  }
  .header-section {
    flex-direction: column;
    gap: 20px;
    align-items: flex-start;
  }
}
.text-success { color: #059669 !important; }
.text-danger { color: #ef4444 !important; }
.text-warning { color: #d97706 !important; }

.italic {
  font-style: italic;
  font-size: 0.9rem;
}

/* Tùy chỉnh Badge cho kho */
.badge-glass.success { background: rgba(5, 150, 105, 0.1); color: #059669; }
.badge-glass.danger { background: rgba(239, 68, 68, 0.1); color: #ef4444; }
.badge-glass.warning { background: rgba(217, 119, 6, 0.1); color: #d97706; }

.history-table th, .history-table td {
  text-align: left;
  vertical-align: top;
}
.change-detail {
  max-width: 350px;
  word-break: break-word;
}
.change-preview {
  font-size: 0.75rem;
  font-family: 'Courier New', monospace;
  background: #f1f5f9;
  padding: 4px 8px;
  border-radius: 6px;
  white-space: pre-wrap;
}
.badge-glass.info {
  background: #e0f2fe;
  color: #0369a1;
}
.badge-glass.secondary {
  background: #e2e8f0;
  color: #475569;
}
.header-right {
  display: flex;
  gap: 12px;
  align-items: center;
}
.loading-state {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 60px;
  gap: 16px;
  color: #2563eb;
  font-weight: 600;
  background: white;
  border-radius: 20px;
  border: 1px solid #f1f5f9;
}
.load-more-section {
  display: flex;
  justify-content: center;
  padding: 32px 0;
  border-top: 1px solid #f1f5f9;
  background: linear-gradient(to bottom, rgba(255,255,255,0), rgba(255,255,255,1));
}
.btn-outline-premium {
  background: white;
  color: #0f172a;
  border: 1px solid #e2e8f0;
  padding: 10px 32px;
  border-radius: 12px;
  font-weight: 700;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 10px;
  transition: 0.3s;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
}
.btn-outline-premium:hover:not(:disabled) {
  border-color: #2563eb;
  color: #2563eb;
  transform: translateY(-2px);
  box-shadow: 0 10px 15px -3px rgba(37, 99, 235, 0.1);
}
.spinner-mini {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(37, 99, 235, 0.2);
  border-top-color: #2563eb;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
.user-cell {
  display: flex;
  flex-direction: column;
}
.user-name {
  font-weight: 700;
  color: #1e293b;
}
.ip-addr {
  font-size: 0.7rem;
  color: #94a3b8;
  font-family: 'Courier New', monospace;
}
.entity-type {
  font-weight: 600;
  color: #64748b;
  font-size: 0.85rem;
}
.table-container {
  background: white;
  border-radius: 20px;
  border: 1px solid #f1f5f9;
  overflow: hidden;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
}
.history-table th {
  background: #f8fafc;
  color: #475569;
  font-weight: 700;
  text-transform: uppercase;
  font-size: 0.75rem;
  letter-spacing: 0.05em;
  padding: 16px 24px;
  border-bottom: 2px solid #f1f5f9;
}
.history-table td {
  padding: 16px 24px;
  border-bottom: 1px solid #f1f5f9;
}
.spinner {
  width: 24px;
  height: 24px;
  border: 3px solid #e2e8f0;
  border-top-color: #2563eb;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
