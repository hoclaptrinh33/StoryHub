<template>
  <DefaultLayout>
    <div class="management-container">
      <!-- Header Section -->
      <div class="header-section">
        <div class="title-meta">
          <h2 class="page-title">Tạo Phiếu Thuê Mới</h2>
          <p class="subtitle">Thiết lập hợp đồng thuê truyện và quản lý tiền cọc</p>
        </div>
        <div class="header-date-badge">
          <span class="material-icons">event</span>
          {{ currentDate }}
        </div>
      </div>

      <div class="rental-grid-layout">
        <!-- Main Content Area (Left) -->
        <div class="rental-main-form">
          <!-- Customer Selection Card -->
          <div class="card-glass shadow-premium mb-6">
            <div class="card-header-lux">
              <h3><span class="material-icons">person_search</span> Thông tin Khách hàng</h3>
              <button class="btn-text-action" @click="openAddCustomerModal">
                 <span class="material-icons">add_circle</span> Thêm khách hàng mới
              </button>
            </div>
            
            <div class="form-row-lux">
              <div class="form-group flex-2">
                <label>Chọn hội viên</label>
                <div class="select-lux-wrapper">
                  <select v-model="selectedCustomerId" class="select-lux-input">
                    <option value="">-- Tìm kiếm & chọn khách hàng --</option>
                    <option v-for="c in customers" :key="c.id" :value="c.id">
                      {{ c.name }} • {{ c.phone }}
                    </option>
                  </select>
                </div>
              </div>
              
              <transition name="fade-slide">
                <div v-if="selectedCustomer" class="customer-preview-box">
                   <div class="avatar">{{ selectedCustomer.name[0] }}</div>
                   <div class="info">
                      <span class="lbl">Hội viên:</span>
                      <span class="val">{{ selectedCustomer.name }}</span>
                   </div>
                   <div class="info">
                      <span class="lbl">SĐT:</span>
                      <span class="val">{{ selectedCustomer.phone }}</span>
                   </div>
                </div>
              </transition>
            </div>
          </div>

          <!-- Rental Items Card -->
          <div class="card-glass shadow-premium">
            <div class="card-header-lux">
              <h3><span class="material-icons">library_books</span> Danh sách Truyện thuê</h3>
              <button class="btn-add-item-lux" @click="addRentalItem">
                <span class="material-icons">add</span> Thêm đầu truyện
              </button>
            </div>

            <div class="rental-dates-config">
              <div class="date-input-lux">
                <label>Ngày bắt đầu</label>
                <input type="date" v-model="rentalDate" />
              </div>
              <div class="date-connect-icon"><span class="material-icons">east</span></div>
              <div class="date-input-lux">
                <label>Ngày trả dự kiến</label>
                <input type="date" v-model="expectedReturnDate" @change="calculateAllItems" />
              </div>
              <div class="days-summary">
                 <span class="val">{{ calculateDays() }}</span>
                 <span class="lbl">Ngày thuê</span>
              </div>
            </div>

            <div class="table-lux-mini">
              <table>
                <thead>
                  <tr>
                    <th>Đầu truyện</th>
                    <th style="width: 100px">Số lượng</th>
                    <th style="width: 150px">Giá (Ngày)</th>
                    <th style="width: 150px">Thành tiền</th>
                    <th style="width: 60px"></th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(item, idx) in rentalItems" :key="idx" class="item-row">
                    <td>
                      <div class="select-lux-wrapper table-select">
                        <select v-model="item.productId" @change="updateItemPrice(idx)">
                          <option value="">-- Chọn đầu truyện --</option>
                          <option v-for="p in products" :key="p.id" :value="p.id">
                            {{ p.name }} ({{ p.code }})
                          </option>
                        </select>
                      </div>
                    </td>
                    <td>
                      <input type="number" v-model.number="item.quantity" min="1" class="qty-input-lux" @change="calculateItemTotal(idx)" />
                    </td>
                    <td>
                      <div class="price-input-wrap">
                        <input type="number" v-model.number="item.dailyRate" class="price-input-lux" @change="calculateItemTotal(idx)" />
                        <span class="unit">đ</span>
                      </div>
                    </td>
                    <td class="total-col-lux">{{ formatCurrency(item.total) }}</td>
                    <td>
                      <button class="btn-remove-lux" @click="removeRentalItem(idx)">
                        <span class="material-icons">delete_outline</span>
                      </button>
                    </td>
                  </tr>
                </tbody>
              </table>
              <div v-if="rentalItems.length === 0" class="empty-items">
                <span class="material-icons">auto_stories</span>
                <p>Chưa có truyện nào trong danh sách thuê</p>
              </div>
            </div>

            <div class="policy-note-lux">
              <span class="material-icons">warning_amber</span>
              <p>Quy định: Phí trễ hạn được tính <strong>5.000đ/ngày/quyển</strong>. Vui lòng nhắc khách hàng hoàn trả đúng hạn.</p>
            </div>
          </div>
        </div>

        <!-- Sidebar Summary Area (Right) -->
        <div class="rental-sidebar">
           <div class="card-glass summary-card shadow-lux sticky-summary">
              <div class="card-header-lux">
                <h3>🔖 Tổng kết Phiếu</h3>
              </div>

              <div class="summary-details">
                <div class="summary-line">
                  <span class="lbl">Tiền thuê gốc</span>
                  <span class="val">{{ formatCurrency(totalRentalFee) }}</span>
                </div>
                <div class="summary-line highlight-blue">
                   <div class="lbl-group">
                      <span class="lbl">Tiền cọc quy định</span>
                      <span class="badge">30%</span>
                   </div>
                  <span class="val">{{ formatCurrency(depositAmount) }}</span>
                </div>
                
                <div class="divider"></div>
                
                <div class="total-big-section">
                   <span class="lbl">TỔNG THANH TOÁN</span>
                   <span class="val">{{ formatCurrency(totalPayment) }}</span>
                </div>
              </div>

              <div class="action-stack">
                <button class="btn-confirm-lux" @click="saveRental">
                  <span class="material-icons">task_alt</span>
                  Xác nhận & Lưu phiếu
                </button>
                <div class="secondary-btns">
                  <button class="btn-outline-lux flex-1" @click="printRentalSlip">
                    <span class="material-icons">print</span> In phiếu
                  </button>
                  <button class="btn-ghost-danger flex-1" @click="cancelRental">
                    <span class="material-icons">close</span> Hủy bỏ
                  </button>
                </div>
              </div>
           </div>
        </div>
      </div>
    </div>

    <!-- Modals -->
    <BaseModal :is-open="isCustomerModalOpen" title="👤 Thêm Khách hàng Mới" @close="closeCustomerModal">
      <div class="form-lux-container">
        <div class="form-row-lux">
          <div class="form-group flex-1">
            <label>Họ tên khách hàng *</label>
            <input v-model="newCustomer.name" type="text" class="input-lux" placeholder="Nhập tên..." />
          </div>
          <div class="form-group flex-1">
            <label>Số điện thoại *</label>
            <input v-model="newCustomer.phone" type="text" class="input-lux" placeholder="09xxxx..." />
          </div>
        </div>
        <div class="form-group">
          <label>Email liên hệ</label>
          <input v-model="newCustomer.email" type="email" class="input-lux" placeholder="example@mail.com" />
        </div>
        <div class="form-group">
          <label>Địa chỉ thường trú</label>
          <input v-model="newCustomer.address" type="text" class="input-lux" placeholder="Nhập địa chỉ..." />
        </div>
      </div>
      <template #footer>
        <div class="modal-footer-lux">
          <button class="btn-ghost" @click="closeCustomerModal">Bỏ qua</button>
          <button class="btn-save-lux" @click="saveNewCustomer">Lưu thông tin</button>
        </div>
      </template>
    </BaseModal>

    <BaseModal :is-open="isPaymentModalOpen" title="💳 Thanh toán Cọc" @close="closePaymentModal">
      <div class="payment-premium-box">
        <div class="payment-header">
           <span class="material-icons big">account_balance_wallet</span>
           <div class="text">
              <p class="lbl">Số tiền cọc cần thu</p>
              <h2 class="val">{{ formatCurrency(depositAmount) }}</h2>
           </div>
        </div>

        <div class="payment-options">
           <label class="payment-radio" :class="{ active: depositPaymentMethod === 'cash' }">
              <input type="radio" value="cash" v-model="depositPaymentMethod" />
              <span class="material-icons">payments</span>
              <span class="text">Tiền mặt</span>
           </label>
           <label class="payment-radio" :class="{ active: depositPaymentMethod === 'transfer' }">
              <input type="radio" value="transfer" v-model="depositPaymentMethod" />
              <span class="material-icons">qr_code_2</span>
              <span class="text">Chuyển khoản / QR</span>
           </label>
        </div>

        <div v-if="depositPaymentMethod === 'cash'" class="cash-input-config">
           <label>Số tiền khách đưa (VNĐ)</label>
           <input type="number" v-model.number="receivedAmount" class="payment-input-lux" />
           <div v-if="receivedAmount > depositAmount" class="change-display">
              <span class="lbl">Tiền thừa trả khách:</span>
              <span class="val">{{ formatCurrency(receivedAmount - depositAmount) }}</span>
           </div>
        </div>
      </div>
      <template #footer>
        <div class="modal-footer-lux">
          <button class="btn-ghost" @click="closePaymentModal">Quay lại</button>
          <button class="btn-confirm-lux wide" @click="confirmPaymentAndSave">
             Xác nhận thanh toán & Hoàn tất
          </button>
        </div>
      </template>
    </BaseModal>
  </DefaultLayout>
</template>

<script setup lang="ts">
import { ref, computed, inject, onMounted } from 'vue';
import DefaultLayout from '../components/layout/defaultLayout.vue';
import BaseModal from '../components/layout/BaseModal.vue';

// Inject services
const addNotification = inject('addNotification') as (type: string, msg: string) => void;
const showConfirm = inject('showConfirm') as (msg: string, title?: string) => Promise<boolean>;

// Date helpers
const currentDate = new Date().toLocaleDateString('vi-VN', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' });
const rentalDate = ref(new Date().toISOString().slice(0, 10));
const expectedReturnDate = ref(new Date(Date.now() + 7 * 86400000).toISOString().slice(0, 10));

// Customers
const customers = ref([
  { id: 1, name: 'Nguyễn Văn A', phone: '0912345678', email: 'a@example.com', address: 'Quận Hải Châu, Đà Nẵng' },
  { id: 2, name: 'Trần Thị B', phone: '0987654321', email: 'b@example.com', address: 'Quận 1, TP.HCM' },
]);
const selectedCustomerId = ref('');
const selectedCustomer = computed(() => customers.value.find(c => c.id === Number(selectedCustomerId.value)));

// Products
const products = ref([
  { id: 1, name: 'One Piece - Tập 105', code: 'OP105', dailyRate: 3000 },
  { id: 2, name: 'Thám Tử Lừng Danh Conan - Tập 98', code: 'CON98', dailyRate: 2500 },
  { id: 3, name: 'Jujutsu Kaisen - Tập 20', code: 'JK20', dailyRate: 3500 },
  { id: 4, name: 'Spy x Family - Tập 10', code: 'SPY10', dailyRate: 2800 },
]);

// Rental items
interface RentalItem {
  productId: number | string;
  productName?: string;
  quantity: number;
  dailyRate: number;
  days: number;
  total: number;
}
const rentalItems = ref<RentalItem[]>([
  { productId: 1, quantity: 2, dailyRate: 3000, days: 7, total: 42000 },
]);

// Computed totals
const totalRentalFee = computed(() => rentalItems.value.reduce((sum, item) => sum + (item.total || 0), 0));
const depositAmount = computed(() => Math.round(totalRentalFee.value * 0.3 / 1000) * 1000); // Làm tròn 1000đ
const totalPayment = computed(() => totalRentalFee.value + depositAmount.value);

// Modals state
const isCustomerModalOpen = ref(false);
const newCustomer = ref({ name: '', phone: '', email: '', address: '' });
const isPaymentModalOpen = ref(false);
const depositPaymentMethod = ref('cash');
const receivedAmount = ref(0);

// Methods
const formatCurrency = (value: number) => new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(value);

const calculateDays = () => {
  if (!rentalDate.value || !expectedReturnDate.value) return 1;
  const start = new Date(rentalDate.value);
  const end = new Date(expectedReturnDate.value);
  const diffTime = end.getTime() - start.getTime();
  return Math.max(1, Math.ceil(diffTime / (1000 * 60 * 60 * 24)));
};

const calculateItemTotal = (idx: number) => {
  const item = rentalItems.value[idx];
  item.total = (item.quantity || 0) * (item.dailyRate || 0) * (item.days || 1);
};

const calculateAllItems = () => {
  const days = calculateDays();
  rentalItems.value.forEach((item, idx) => {
    item.days = days;
    calculateItemTotal(idx);
  });
};

const updateItemPrice = (idx: number) => {
  const item = rentalItems.value[idx];
  const product = products.value.find(p => p.id === Number(item.productId));
  if (product) {
    item.dailyRate = product.dailyRate;
    calculateItemTotal(idx);
  }
};

const addRentalItem = () => {
  rentalItems.value.push({ productId: '', quantity: 1, dailyRate: 0, days: calculateDays(), total: 0 });
};

const removeRentalItem = (idx: number) => rentalItems.value.splice(idx, 1);

const openAddCustomerModal = () => {
  newCustomer.value = { name: '', phone: '', email: '', address: '' };
  isCustomerModalOpen.value = true;
};
const closeCustomerModal = () => isCustomerModalOpen.value = false;
const saveNewCustomer = () => {
  if (!newCustomer.value.name || !newCustomer.value.phone) {
    addNotification('warning', 'Tên và Số điện thoại là bắt buộc');
    return;
  }
  const newId = Math.max(...customers.value.map(c => c.id), 0) + 1;
  customers.value.push({ id: newId, ...newCustomer.value });
  selectedCustomerId.value = newId.toString();
  addNotification('success', 'Đã thêm khách hàng mới');
  closeCustomerModal();
};

const saveRental = () => {
  if (!selectedCustomerId.value) return addNotification('warning', 'Vui lòng chọn khách hàng');
  if (rentalItems.value.length === 0 || rentalItems.value.some(i => !i.productId)) return addNotification('warning', 'Danh sách truyện không hợp lệ');
  
  if (depositAmount.value > 0) {
    receivedAmount.value = depositAmount.value;
    isPaymentModalOpen.value = true;
  } else {
    resetForm();
    addNotification('success', 'Phiếu thuê đã được lưu thành công');
  }
};

const closePaymentModal = () => isPaymentModalOpen.value = false;
const confirmPaymentAndSave = () => {
  if (depositPaymentMethod.value === 'cash' && receivedAmount.value < depositAmount.value) {
    return addNotification('error', 'Số tiền khách đưa không đủ thanh toán cọc');
  }
  addNotification('success', 'Thanh toán cọc thành công. Phiếu thuê đã được lưu vào hệ thống.');
  isPaymentModalOpen.value = false;
  resetForm();
};

const printRentalSlip = () => addNotification('info', 'Chức năng in đang được chuẩn bị');

const cancelRental = async () => {
  if (await showConfirm('Dữ liệu đang nhập sẽ bị mất. Bạn chắc chứ?', 'Hủy tạo phiếu')) {
    resetForm();
    addNotification('info', 'Đã hủy phiếu thuê');
  }
};

const resetForm = () => {
  selectedCustomerId.value = '';
  rentalItems.value = [];
  addRentalItem();
  calculateAllItems();
};

onMounted(() => calculateAllItems());
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

.management-container { 
  padding: 32px; 
  background: #f8fafc; 
  min-height: 100vh;
  font-family: 'Plus Jakarta Sans', sans-serif;
}

.header-section { display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 32px; }
.page-title { font-size: 2rem; font-weight: 800; color: #0f172a; margin: 0; letter-spacing: -0.04em; }
.subtitle { color: #64748b; font-size: 0.95rem; margin-top: 4px; }
.header-date-badge { background: white; padding: 10px 18px; border-radius: 14px; font-weight: 700; color: #2563eb; display: flex; align-items: center; gap: 8px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); }

/* Grid Layout */
.rental-grid-layout { display: grid; grid-template-columns: 1fr 380px; gap: 32px; align-items: start; }

.card-glass { 
  background: white; border-radius: 24px; padding: 28px; border: 1px solid #f1f5f9;
  box-shadow: 0 10px 15px -3px rgba(0,0,0,0.03);
}
.shadow-premium { box-shadow: 0 20px 25px -5px rgba(0,0,0,0.05); }
.mb-6 { margin-bottom: 24px; }

.card-header-lux { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; }
.card-header-lux h3 { font-size: 1.15rem; font-weight: 800; color: #1e293b; margin: 0; display: flex; align-items: center; gap: 10px; }
.card-header-lux h3 .material-icons { color: #2563eb; }

/* Sub-components */
.btn-text-action { background: none; border: none; color: #2563eb; font-weight: 700; display: flex; align-items: center; gap: 6px; cursor: pointer; padding: 6px; border-radius: 8px; transition: 0.2s; }
.btn-text-action:hover { background: #eff6ff; }

.select-lux-wrapper { position: relative; background: #f8fafc; border-radius: 14px; border: 2px solid #f1f5f9; transition: 0.3s; }
.select-lux-input { width: 100%; padding: 14px; border: none; background: transparent; outline: none; font-weight: 700; color: #1e293b; font-family: inherit; }
.select-lux-wrapper:focus-within { border-color: #2563eb; background: white; }

.customer-preview-box { flex: 1; background: #f0f9ff; border-radius: 18px; padding: 14px 20px; display: flex; align-items: center; gap: 16px; border: 1px solid #bae6fd; }
.customer-preview-box .avatar { width: 44px; height: 44px; border-radius: 12px; background: #2563eb; color: white; display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 1.2rem; }
.customer-preview-box .info { display: flex; flex-direction: column; }
.customer-preview-box .lbl { font-size: 0.65rem; font-weight: 800; color: #0369a1; text-transform: uppercase; }
.customer-preview-box .val { font-size: 0.95rem; font-weight: 700; color: #0c4a6e; }

/* Rental Items Table */
.rental-dates-config { display: flex; align-items: center; gap: 16px; margin-bottom: 28px; padding: 20px; background: #f8fafc; border-radius: 20px; border: 1px dashed #e2e8f0; }
.date-input-lux { flex: 1; display: flex; flex-direction: column; gap: 6px; }
.date-input-lux label { font-size: 0.75rem; font-weight: 800; color: #64748b; text-transform: uppercase; padding-left: 4px; }
.date-input-lux input { padding: 12px; border-radius: 12px; border: 1px solid #e2e8f0; font-weight: 700; color: #1e293b; font-family: inherit; }
.date-connect-icon { color: #94a3b8; }
.days-summary { padding: 0 16px; text-align: center; border-left: 2px solid #e2e8f0; }
.days-summary .val { display: block; font-size: 1.5rem; font-weight: 900; color: #2563eb; line-height: 1; }
.days-summary .lbl { font-size: 0.7rem; font-weight: 800; color: #94a3b8; text-transform: uppercase; }

.table-lux-mini table { width: 100%; border-collapse: separate; border-spacing: 0 12px; }
.table-lux-mini th { padding: 0 12px; font-size: 0.75rem; font-weight: 800; color: #94a3b8; text-transform: uppercase; text-align: left; }
.table-lux-mini td { padding: 0; vertical-align: middle; }

.qty-input-lux { width: 100%; padding: 12px; border-radius: 12px; border: 2px solid #f1f5f9; background: #f8fafc; font-weight: 800; text-align: center; outline: none; }
.price-input-wrap { display: flex; align-items: center; position: relative; }
.price-input-lux { width: 100%; padding: 12px 24px 12px 12px; border-radius: 12px; border: 2px solid #f1f5f9; background: #f8fafc; font-weight: 800; outline: none; }
.price-input-wrap .unit { position: absolute; right: 12px; font-size: 0.8rem; font-weight: 800; color: #94a3b8; }

.total-col-lux { font-weight: 800; color: #1e293b; font-size: 1rem; padding-left: 12px !important; }
.btn-remove-lux { width: 40px; height: 40px; border-radius: 12px; border: none; background: #fee2e2; color: #ef4444; cursor: pointer; transition: 0.2s; }
.btn-remove-lux:hover { background: #ef4444; color: white; transform: rotate(8deg); }

.empty-items { text-align: center; padding: 40px; color: #94a3b8; }
.empty-items .material-icons { font-size: 3rem; opacity: 0.2; margin-bottom: 12px; }

/* Sidebar Summary */
.sticky-summary { position: sticky; top: 32px; }
.summary-details { margin-top: 12px; }
.summary-line { display: flex; justify-content: space-between; align-items: center; padding: 14px 0; }
.summary-line .lbl { font-weight: 600; color: #64748b; }
.summary-line .val { font-weight: 800; color: #1e293b; }

.highlight-blue { background: #eff6ff; margin: 8px -28px; padding: 16px 28px; }
.highlight-blue .lbl { color: #2563eb; }
.highlight-blue .val { color: #1d4ed8; font-size: 1.1rem; }
.lbl-group { display: flex; align-items: center; gap: 8px; }
.lbl-group .badge { background: #2563eb; color: white; font-size: 0.65rem; padding: 2px 6px; border-radius: 6px; }

.total-big-section { padding-top: 24px; text-align: right; }
.total-big-section .lbl { display: block; font-size: 0.8rem; font-weight: 800; color: #94a3b8; margin-bottom: 4px; }
.total-big-section .val { font-size: 2rem; font-weight: 900; color: #0f172a; letter-spacing: -0.02em; }

.action-stack { margin-top: 32px; display: flex; flex-direction: column; gap: 12px; }
.btn-confirm-lux { background: #2563eb; color: white; border: none; padding: 18px; border-radius: 18px; font-weight: 700; font-family: inherit; font-size: 1rem; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 10px; transition: 0.3s; box-shadow: 0 10px 15px -3px rgba(37, 99, 235, 0.3); }
.btn-confirm-lux:hover { background: #1d4ed8; transform: translateY(-2px); box-shadow: 0 20px 25px -5px rgba(37, 99, 235, 0.4); }

.secondary-btns { display: flex; gap: 12px; }
.btn-outline-lux { background: white; border: 2px solid #e2e8f0; color: #475569; padding: 12px; border-radius: 14px; font-weight: 700; cursor: pointer; transition: 0.2s; display: flex; align-items: center; justify-content: center; gap: 6px; }
.btn-outline-lux:hover { background: #f8fafc; border-color: #cbd5e1; }
.btn-ghost-danger { background: transparent; border: none; color: #94a3b8; padding: 12px; border-radius: 14px; font-weight: 700; cursor: pointer; transition: 0.2s; display: flex; align-items: center; justify-content: center; gap: 6px; }
.btn-ghost-danger:hover { background: #fee2e2; color: #ef4444; }

/* Modal Elements */
.payment-premium-box { padding: 10px 0; }
.payment-header { display: flex; align-items: center; gap: 20px; background: #f8fafc; padding: 24px; border-radius: 20px; margin-bottom: 24px; border: 1px solid #e2e8f0; }
.payment-header .material-icons.big { font-size: 3rem; color: #2563eb; }
.payment-header .lbl { font-size: 0.85rem; font-weight: 700; color: #64748b; margin: 0; }
.payment-header .val { font-size: 1.75rem; font-weight: 900; color: #0f172a; margin: 0; }

.payment-options { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 24px; }
.payment-radio { display: flex; flex-direction: column; align-items: center; gap: 12px; padding: 20px; border-radius: 20px; border: 2px solid #f1f5f9; cursor: pointer; transition: 0.2s; }
.payment-radio input { display: none; }
.payment-radio .material-icons { font-size: 1.5rem; color: #94a3b8; }
.payment-radio .text { font-weight: 700; color: #64748b; }
.payment-radio.active { border-color: #2563eb; background: #eff6ff; }
.payment-radio.active .material-icons, .payment-radio.active .text { color: #2563eb; }

.cash-input-config { padding-top: 12px; }
.cash-input-config label { display: block; font-size: 0.85rem; font-weight: 800; color: #475569; margin-bottom: 10px; }
.payment-input-lux { width: 100%; padding: 16px; border-radius: 16px; border: 2px solid #e2e8f0; font-size: 1.25rem; font-weight: 800; outline: none; }
.payment-input-lux:focus { border-color: #2563eb; }

.change-display { margin-top: 16px; padding: 16px; background: #dcfce7; border-radius: 14px; display: flex; justify-content: space-between; font-weight: 800; }
.change-display .lbl { color: #166534; }
.change-display .val { color: #15803d; }

.wide { width: 100%; }

@media (max-width: 1100px) {
  .rental-grid-layout { grid-template-columns: 1fr; }
}
</style>