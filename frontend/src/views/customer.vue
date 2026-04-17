<template>
  <DefaultLayout>
    <div class="management-container">
      <!-- Header Section -->
      <div class="header-section">
        <div class="title-meta">
          <h2 class="page-title">👥 Quản lý Khách hàng</h2>
          <p class="subtitle">Danh sách hội viên, dư nợ và chính sách khách hàng</p>
        </div>
        <button class="btn-primary-lux" @click="openCreateModal">
          <span class="material-icons">person_add</span>
          Thêm khách hàng mới
        </button>
      </div>

      <!-- Filter & Search Bar -->
      <div class="filter-glass-bar">
        <div class="search-box-premium">
          <span class="material-icons">search</span>
          <input type="text" v-model="searchKeyword" placeholder="Tìm kiếm theo tên hoặc số điện thoại..." />
        </div>
        
        <div class="filters-group">
          <div class="select-wrapper">
             <select v-model="filterMembership" class="select-lux">
                <option value="">Tất cả hạng hội viên</option>
                <option v-for="level in ['Bronze', 'Silver', 'Gold', 'Platinum']" :key="level" :value="level">{{ level }} Member</option>
             </select>
          </div>
          
          <div class="select-wrapper">
             <select v-model="filterBlacklist" class="select-lux">
                <option value="">Tất cả trạng thái</option>
                <option value="true">⛔ Blacklist</option>
                <option value="false">✅ Bình thường</option>
             </select>
          </div>

          <button class="btn-icon-refresh" @click="resetFilters" title="Làm mới bộ lọc">
            <span class="material-icons">refresh</span>
          </button>
        </div>
      </div>

      <!-- Main Table Card -->
      <div class="card-glass content-table-card">
        <div class="table-lux">
          <table>
            <thead>
              <tr>
                <th style="width: 80px">ID</th>
                <th>Khách hàng</th>
                <th>Thông tin liên hệ</th>
                <th>Hạng thành viên</th>
                <th class="text-right">Dư nợ / Tiền cọc</th>
                <th class="text-center">Trạng thái</th>
                <th class="text-right">Thao tác</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="c in filteredCustomers" :key="c.id" :class="{ 'row-blocked': c.blacklist_flag }">
                <td class="text-muted font-mono">#{{ c.id }}</td>
                <td>
                  <div class="customer-info-cell">
                    <div class="avatar-mini">{{ c.name[0] }}</div>
                    <div class="details">
                      <span class="name">{{ c.name }}</span>
                      <span class="address">{{ c.address || 'Chưa cập nhật địa chỉ' }}</span>
                    </div>
                  </div>
                </td>
                <td>
                  <div class="contact-info">
                    <span class="phone"><span class="material-icons">phone</span> {{ c.phone }}</span>
                  </div>
                </td>
                <td>
                  <span :class="['membership-badge', c.membership_level.toLowerCase()]">
                    {{ c.membership_level }}
                  </span>
                </td>
                <td class="text-right">
                  <div class="money-status">
                    <span class="deposit">{{ formatCurrency(c.deposit_balance) }}</span>
                    <span v-if="c.debt > 0" class="debt text-danger">- {{ formatCurrency(c.debt) }}</span>
                  </div>
                </td>
                <td class="text-center">
                   <div :class="['status-pill', c.blacklist_flag ? 'blocked' : 'active']">
                      <span class="dot"></span>
                      {{ c.blacklist_flag ? 'Blacklist' : 'Hoạt động' }}
                   </div>
                </td>
                <td class="text-right">
                  <div class="action-btns">
                    <button class="btn-action edit" @click="openEditModal(c)" title="Sửa thông tin">
                      <span class="material-icons">edit</span>
                    </button>
                    <button class="btn-action delete" @click="deleteCustomer(c.id)" title="Xóa khách hàng">
                      <span class="material-icons">delete</span>
                    </button>
                    <button 
                      class="btn-action block" 
                      :class="{ 'is-blocked': c.blacklist_flag }"
                      @click="toggleBlacklist(c.id, !c.blacklist_flag)"
                      :title="c.blacklist_flag ? 'Gỡ khỏi danh sách đen' : 'Đưa vào danh sách đen'"
                    >
                      <span class="material-icons">{{ c.blacklist_flag ? 'check_circle' : 'block' }}</span>
                    </button>
                  </div>
                </td>
              </tr>
              <tr v-if="filteredCustomers.length === 0">
                <td colspan="7">
                   <div class="empty-state">
                      <span class="material-icons">person_search</span>
                      <p>Không tìm thấy khách hàng phù hợp với điều kiện lọc</p>
                   </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- Modal Form -->
    <BaseModal :is-open="isModalOpen" :title="modalTitle" @close="closeModal">
      <div class="customer-form-lux">
        <div class="form-row">
          <div class="form-group flex-2">
            <label>Họ và tên khách hàng</label>
            <div class="input-with-icon">
              <span class="material-icons">person</span>
              <input v-model="formData.name" type="text" placeholder="Nhập tên khách hàng..." />
            </div>
          </div>
          <div class="form-group flex-1">
            <label>Số điện thoại</label>
            <div class="input-with-icon">
              <span class="material-icons">phone</span>
              <input v-model="formData.phone" type="tel" placeholder="09xxx..." />
            </div>
          </div>
        </div>

        <div class="form-group">
          <label>Địa chỉ liên lạc</label>
          <div class="input-with-icon">
            <span class="material-icons">place</span>
            <input v-model="formData.address" type="text" placeholder="Địa chỉ thường trú..." />
          </div>
        </div>

        <div class="form-row mt-4">
          <div class="form-group">
            <label>Hạng thành viên</label>
            <select v-model="formData.membership_level" class="form-select-lux">
              <option value="Bronze">Bronze Member</option>
              <option value="Silver">Silver Member</option>
              <option value="Gold">Gold Member</option>
              <option value="Platinum">Platinum Member</option>
            </select>
          </div>
          <div class="form-group">
            <label>Số dư cọc (VNĐ)</label>
            <input v-model.number="formData.deposit_balance" type="number" class="form-input-lux" />
          </div>
          <div class="form-group">
            <label>Dư nợ (VNĐ)</label>
            <input v-model.number="formData.debt" type="number" class="form-input-lux" />
          </div>
        </div>

        <div class="form-group toggle-group">
           <label class="toggle-label">
             <input type="checkbox" v-model="formData.blacklist_flag" />
             <span class="toggle-slider"></span>
             Đưa vào danh sách đen (Tạm khóa tài khoản)
           </label>
        </div>
      </div>
      <template #footer>
        <div class="modal-footer-lux">
           <button class="btn-ghost" @click="closeModal">Hủy bỏ</button>
           <button class="btn-save-lux" @click="saveCustomer">
             <span class="material-icons">save</span>
             {{ isEditing ? 'Cập nhật' : 'Lưu khách hàng' }}
           </button>
        </div>
      </template>
    </BaseModal>
  </DefaultLayout>
</template>

<script setup lang="ts">
import { ref, computed, inject } from 'vue';
import DefaultLayout from '../components/layout/defaultLayout.vue';
import BaseModal from '../components/layout/BaseModal.vue';

// Services
const addNotification = inject('addNotification') as (type: string, msg: string) => void;
const showConfirm = inject('showConfirm') as (msg: string, title?: string) => Promise<boolean>;

// ================== DATA & STATE ==================

interface Customer {
  id: number;
  name: string;
  phone: string;
  address: string;
  membership_level: 'Bronze' | 'Silver' | 'Gold' | 'Platinum';
  deposit_balance: number;
  debt: number;
  blacklist_flag: boolean;
}

const customers = ref<Customer[]>([
  { id: 1, name: 'Nguyễn Văn A', phone: '0909123456', address: 'Hải Châu, Đà Nẵng', membership_level: 'Gold', deposit_balance: 500000, debt: 0, blacklist_flag: false },
  { id: 2, name: 'Trần Thị B', phone: '0918989898', address: 'Quận 1, TP.HCM', membership_level: 'Silver', deposit_balance: 200000, debt: 50000, blacklist_flag: false },
  { id: 3, name: 'Lê Văn C', phone: '0977778888', address: 'Hoàn Kiếm, Hà Nội', membership_level: 'Bronze', deposit_balance: 0, debt: 150000, blacklist_flag: true },
]);

const searchKeyword = ref('');
const filterMembership = ref('');
const filterBlacklist = ref('');

const filteredCustomers = computed(() => {
  let result = customers.value;
  if (searchKeyword.value) {
    const kw = searchKeyword.value.toLowerCase();
    result = result.filter(c => c.name.toLowerCase().includes(kw) || c.phone.includes(kw));
  }
  if (filterMembership.value) {
    result = result.filter(c => c.membership_level === filterMembership.value);
  }
  if (filterBlacklist.value !== '') {
    const isBlacklist = filterBlacklist.value === 'true';
    result = result.filter(c => c.blacklist_flag === isBlacklist);
  }
  return result;
});

const resetFilters = () => {
  searchKeyword.value = '';
  filterMembership.value = '';
  filterBlacklist.value = '';
};

// Modal logic
const isModalOpen = ref(false);
const isEditing = ref(false);
const editingId = ref<number | null>(null);
const modalTitle = computed(() => isEditing.value ? '📝 Chỉnh sửa Thông tin Hội viên' : '🆕 Thêm Hội viên Mới');

const formData = ref<Omit<Customer, 'id'>>({
  name: '',
  phone: '',
  address: '',
  membership_level: 'Bronze',
  deposit_balance: 0,
  debt: 0,
  blacklist_flag: false,
});

const openCreateModal = () => {
  isEditing.value = false;
  editingId.value = null;
  formData.value = {
    name: '', phone: '', address: '', membership_level: 'Bronze',
    deposit_balance: 0, debt: 0, blacklist_flag: false,
  };
  isModalOpen.value = true;
};

const openEditModal = (customer: Customer) => {
  isEditing.value = true;
  editingId.value = customer.id;
  formData.value = { ...customer };
  isModalOpen.value = true;
};

const closeModal = () => { isModalOpen.value = false; };

const saveCustomer = async () => {
  if (!formData.value.name || !formData.value.phone) {
    addNotification('warning', 'Vui lòng cung cấp ít nhất Tên và Số điện thoại');
    return;
  }
  
  const exist = customers.value.find(c => c.phone === formData.value.phone && c.id !== editingId.value);
  if (exist) {
    addNotification('error', 'Số điện thoại này đã được đăng ký trong hệ thống');
    return;
  }

  if (isEditing.value && editingId.value) {
    const index = customers.value.findIndex(c => c.id === editingId.value);
    if (index !== -1) {
      customers.value[index] = { id: editingId.value, ...formData.value };
      addNotification('success', 'Đã cập nhật thông tin khách hàng');
    }
  } else {
    const newId = Math.max(...customers.value.map(c => c.id), 0) + 1;
    customers.value.push({ id: newId, ...formData.value });
    addNotification('success', 'Đã thêm khách hàng mới thành công');
  }
  closeModal();
};

const deleteCustomer = async (id: number) => {
  const customer = customers.value.find(c => c.id === id);
  if (!customer) return;
  const confirmed = await showConfirm(`Bạn có chắc chắn muốn xóa hội viên "${customer.name}"?`, 'Xác nhận xóa');
  if (confirmed) {
    customers.value = customers.value.filter(c => c.id !== id);
    addNotification('success', 'Đã xóa hội viên khỏi hệ thống');
  }
};

const toggleBlacklist = async (id: number, flag: boolean) => {
  const customer = customers.value.find(c => c.id === id);
  if (!customer) return;
  const action = flag ? 'khóa' : 'mở khóa';
  const confirmed = await showConfirm(`Xác nhận ${action} tài khoản hội viên "${customer.name}"?`, 'Cập nhật trạng thái');
  if (confirmed) {
    customer.blacklist_flag = flag;
    addNotification(flag ? 'warning' : 'success', `Đã ${action} hội viên thành công`);
  }
};

const formatCurrency = (value: number) => {
  return new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(value);
};
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

.management-container { 
  padding: 32px; 
  background: #fdfdfd; 
  background-image: radial-gradient(#e2e8f0 0.5px, transparent 0.5px);
  background-size: 24px 24px;
  min-height: 100vh; 
  font-family: 'Plus Jakarta Sans', sans-serif; 
}

/* Header UI Box */
.header-section { display: flex; justify-content: space-between; align-items: center; margin-bottom: 32px; }
.page-title { font-size: 2.25rem; font-weight: 800; color: #0f172a; letter-spacing: -0.04em; margin: 0; }
.subtitle { color: #64748b; font-size: 1rem; margin-top: 4px; }

.btn-primary-lux { 
  background: #2563eb; color: white; border: none; padding: 14px 28px; border-radius: 20px;
  font-weight: 700; display: flex; align-items: center; gap: 10px; cursor: pointer; transition: 0.3s;
  box-shadow: 0 10px 15px -3px rgba(37, 99, 235, 0.2);
}
.btn-primary-lux:hover { transform: translateY(-2px); box-shadow: 0 20px 25px -5px rgba(37, 99, 235, 0.3); }

/* Filter Bar Glassmorphism */
.filter-glass-bar {
  background: rgba(255, 255, 255, 0.6);
  backdrop-filter: blur(10px);
  padding: 12px;
  border-radius: 24px;
  border: 1px solid rgba(255, 255, 255, 0.3);
  display: flex;
  gap: 16px;
  margin-bottom: 32px;
  box-shadow: 0 10px 15px -3px rgba(0,0,0,0.03);
}

.search-box-premium { 
  flex: 1; position: relative; 
  background: white; border-radius: 18px; border: 1px solid #f1f5f9;
}
.search-box-premium .material-icons { position: absolute; left: 16px; top: 50%; transform: translateY(-50%); color: #2563eb; }
.search-box-premium input { 
  width: 100%; padding: 14px 14px 14px 52px; border: none; background: transparent; 
  outline: none; font-weight: 600; font-family: inherit; font-size: 0.95rem;
}

.filters-group { display: flex; gap: 12px; }
.select-wrapper { 
  background: white; border-radius: 18px; border: 1px solid #f1f5f9; padding: 0 16px;
  display: flex; align-items: center;
}
.select-lux { border: none; padding: 12px 0; outline: none; font-weight: 700; color: #475569; font-size: 0.85rem; cursor: pointer; }

.btn-icon-refresh {
  width: 48px; height: 48px; border-radius: 18px; border: none; background: white; color: #64748b;
  cursor: pointer; transition: 0.3s;
}
.btn-icon-refresh:hover { background: #f1f5f9; color: #2563eb; transform: rotate(180deg); }

/* Table Lux */
.card-glass { 
  background: rgba(255, 255, 255, 0.8); backdrop-filter: blur(12px);
  padding: 0; border-radius: 32px; border: 1px solid rgba(255, 255, 255, 0.3); 
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.05); overflow: hidden;
}

.table-lux table { width: 100%; border-collapse: separate; border-spacing: 0; }
.table-lux th { padding: 20px 24px; text-align: left; color: #94a3b8; font-weight: 800; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.1em; background: rgba(248, 250, 252, 0.5); }
.table-lux td { padding: 20px 24px; vertical-align: middle; border-bottom: 1px solid #f1f5f9; }
.table-lux tr:last-child td { border-bottom: none; }
.table-lux tr:hover td { background: rgba(248, 250, 252, 0.8); }

.customer-info-cell { display: flex; align-items: center; gap: 16px; }
.avatar-mini { width: 44px; height: 44px; border-radius: 14px; background: #eff6ff; color: #2563eb; display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 1.25rem; }
.customer-info-cell .name { display: block; font-weight: 800; color: #1e293b; font-size: 1rem; }
.customer-info-cell .address { display: block; font-size: 0.8rem; color: #94a3b8; font-weight: 500; }

.contact-info .phone { font-weight: 700; color: #475569; display: flex; align-items: center; gap: 6px; font-size: 0.9rem; }
.contact-info .material-icons { font-size: 18px; color: #cbd5e1; }

.membership-badge { padding: 6px 14px; border-radius: 12px; font-size: 0.75rem; font-weight: 800; text-transform: uppercase; }
.membership-badge.bronze { background: #ffedd5; color: #9a3412; }
.membership-badge.silver { background: #f1f5f9; color: #475569; }
.membership-badge.gold { background: #fef9c3; color: #a16207; }
.membership-badge.platinum { background: #ecfeff; color: #0891b2; }

.money-status { display: flex; flex-direction: column; }
.money-status .deposit { font-weight: 800; color: #059669; font-size: 1rem; }
.money-status .debt { font-size: 0.75rem; font-weight: 700; }

.status-pill { display: inline-flex; align-items: center; gap: 8px; padding: 6px 12px; border-radius: 20px; font-size: 0.75rem; font-weight: 800; }
.status-pill.active { background: #dcfce7; color: #166534; }
.status-pill.blocked { background: #fee2e2; color: #b91c1c; }
.status-pill .dot { width: 6px; height: 6px; border-radius: 50%; background: currentColor; }

.action-btns { display: flex; gap: 8px; justify-content: flex-end; }
.btn-action { width: 40px; height: 40px; border-radius: 12px; border: none; background: #f1f5f9; color: #64748b; cursor: pointer; transition: 0.3s; display: flex; align-items: center; justify-content: center; }
.btn-action:hover { background: #2563eb; color: white; transform: translateY(-2px); }
.btn-action.delete:hover { background: #ef4444; }
.btn-action.block.is-blocked { background: #fee2e2; color: #ef4444; }
.btn-action.block.is-blocked:hover { background: #ef4444; color: white; }

/* Empty state */
.empty-state { text-align: center; padding: 60px 0; color: #94a3b8; }
.empty-state .material-icons { font-size: 4rem; margin-bottom: 16px; opacity: 0.3; }

/* Form Lux */
.customer-form-lux { padding: 10px 0; }
.form-row { display: flex; gap: 20px; margin-bottom: 20px; }
.flex-2 { flex: 2; } .flex-1 { flex: 1; }
.form-group label { display: block; font-size: 0.8rem; font-weight: 800; color: #475569; margin-bottom: 10px; text-transform: uppercase; letter-spacing: 0.05em; }
.input-with-icon { position: relative; }
.input-with-icon .material-icons { position: absolute; left: 16px; top: 50%; transform: translateY(-50%); color: #2563eb; font-size: 20px; }
.input-with-icon input { width: 100%; padding: 16px 16px 16px 52px; border-radius: 18px; border: 2px solid #f1f5f9; background: #f8fafc; outline: none; transition: 0.3s; font-weight: 600; font-family: inherit; }
.input-with-icon input:focus { border-color: #2563eb; background: white; box-shadow: 0 0 0 5px rgba(37, 99, 235, 0.05); }

.form-select-lux, .form-input-lux { width: 100%; padding: 16px; border-radius: 18px; border: 2px solid #f1f5f9; background: #f8fafc; outline: none; transition: 0.3s; font-weight: 700; }
.form-select-lux:focus, .form-input-lux:focus { border-color: #2563eb; background: white; }

.toggle-group { margin-top: 32px; padding: 20px; background: #fef2f2; border-radius: 20px; }
.toggle-label { display: flex; align-items: center; gap: 16px; font-weight: 700; color: #991b1b; cursor: pointer; }

.modal-footer-lux { display: flex; justify-content: flex-end; gap: 16px; width: 100%; }
.btn-ghost { padding: 14px 28px; border-radius: 18px; border: none; background: #f1f5f9; color: #64748b; font-weight: 700; cursor: pointer; transition: 0.3s; }
.btn-save-lux { padding: 14px 32px; border-radius: 18px; border: none; background: #2563eb; color: white; font-weight: 700; cursor: pointer; transition: 0.3s; display: flex; align-items: center; gap: 8px; box-shadow: 0 10px 15px -3px rgba(37, 99, 235, 0.2); }
.btn-save-lux:hover { background: #1d4ed8; transform: translateY(-2px); }

@media (max-width: 1000px) {
  .header-section { flex-direction: column; align-items: flex-start; gap: 20px; }
  .filter-glass-bar { flex-direction: column; }
  .form-row { flex-direction: column; }
}
</style>