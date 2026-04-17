<script setup lang="ts">
import DefaultLayout from '../components/layout/defaultLayout.vue'
import BaseModal from '../components/layout/BaseModal.vue'
import { ref, computed, inject } from 'vue';

const addNotification = inject('addNotification') as any;
const showConfirm = inject('showConfirm') as any;

// Mocked books data (should come from store in real app)
const allBooks = [
  { id: 1, name: 'One Piece - Tập 105', code: 'TR001', author: 'Oda Eiichiro' },
  { id: 2, name: 'Conan - Tập 98', code: 'TR002', author: 'Aoyama Gosho' },
  { id: 3, name: 'Spy x Family - Tập 10', code: 'TR003', author: 'Tatsuya Endo' },
  { id: 4, name: 'Jujutsu Kaisen - Tập 20', code: 'TR004', author: 'Gege Akutami' },
];

const promos = ref([
  { 
    id: 1, 
    name: 'Lễ hội Hải tặc 2026', 
    occasion: 'Dịp Hè', 
    startDate: '2026-06-01', 
    endDate: '2026-08-31', 
    status: 'Upcoming',
    appliedBooks: [
      { id: 1, name: 'One Piece - Tập 105', discount: 20 }
    ]
  },
  { 
    id: 2, 
    name: 'Tuần lễ Trinh thám', 
    occasion: 'Sự kiện tháng 4', 
    startDate: '2026-04-10', 
    endDate: '2026-04-20', 
    status: 'Active',
    appliedBooks: [
      { id: 2, name: 'Conan - Tập 98', discount: 15 }
    ]
  },
]);

const isModalOpen = ref(false);
const isEditing = ref(false);
const searchQuery = ref('');
const formPromo = ref({
  id: 0,
  name: '',
  occasion: '',
  startDate: '',
  endDate: '',
  appliedBooks: [] as { id: number, name: string, discount: number }[]
});

const filteredBooksSearch = computed(() => {
  let list = allBooks;
  if (searchQuery.value) {
    list = allBooks.filter(b => 
      b.name.toLowerCase().includes(searchQuery.value.toLowerCase()) || 
      b.code.toLowerCase().includes(searchQuery.value.toLowerCase())
    );
  }
  return list.filter(b => !formPromo.value.appliedBooks.some(ab => ab.id === b.id));
});

const openCreateModal = () => {
  isEditing.value = false;
  formPromo.value = {
    id: Date.now(),
    name: '',
    occasion: '',
    startDate: '',
    endDate: '',
    appliedBooks: []
  };
  searchQuery.value = '';
  isModalOpen.value = true;
};

const openEditModal = (promo: any) => {
  isEditing.value = true;
  formPromo.value = JSON.parse(JSON.stringify(promo)); // Deep copy
  searchQuery.value = '';
  isModalOpen.value = true;
};

const addBookToPromo = (book: any) => {
  formPromo.value.appliedBooks.push({
    id: book.id,
    name: book.name,
    discount: 10 // Default 10%
  });
  searchQuery.value = '';
};

const removeBookFromPromo = (bookId: number) => {
  formPromo.value.appliedBooks = formPromo.value.appliedBooks.filter(b => b.id !== bookId);
};

const savePromo = () => {
  // Simple validation
  if (!formPromo.value.name || !formPromo.value.startDate || !formPromo.value.endDate) {
    addNotification('warning', 'Vui lòng điền đầy đủ thông tin!');
    return;
  }

  // Calculate status (simplified for demo)
  const now = new Date();
  const start = new Date(formPromo.value.startDate);
  const end = new Date(formPromo.value.endDate);
  let status = 'Upcoming';
  if (now >= start && now <= end) status = 'Active';
  else if (now > end) status = 'Expired';

  const promoData = { ...formPromo.value, status };

  if (isEditing.value) {
    const index = promos.value.findIndex(p => p.id === promoData.id);
    if (index !== -1) promos.value[index] = promoData;
  } else {
    promos.value.unshift(promoData);
  }
  
  addNotification('success', isEditing.value ? 'Đã cập nhật chương trình!' : 'Đã tạo chương trình mới!');
  isModalOpen.value = false;
};

const deletePromo = async (id: number) => {
  if (await showConfirm('Bạn có chắc chắn muốn xóa chương trình này?')) {
    promos.value = promos.value.filter(p => p.id !== id);
    addNotification('success', 'Đã xóa chương trình khuyến mãi');
  }
};
</script>

<template>
  <DefaultLayout>
    <div class="promo-page">
      <div class="main-header">
        <div class="header-info">
          <h2 class="title">Chương trình khuyến mãi</h2>
          <p class="subtitle">Quản lý các sự kiện giảm giá và ưu đãi theo bộ truyện</p>
        </div>
        <button class="btn-primary" @click="openCreateModal">
          <span class="icon">✨</span> Tạo khuyến mãi mới
        </button>
      </div>

      <div class="promo-grid">
        <div v-for="promo in promos" :key="promo.id" class="promo-card">
          <div class="card-header">
            <span class="occasion-badge">{{ promo.occasion || 'Sự kiện' }}</span>
            <div class="status-indicator" :class="promo.status.toLowerCase()">
              {{ promo.status === 'Active' ? 'Đang diễn ra' : promo.status === 'Upcoming' ? 'Sắp diễn ra' : 'Đã kết thúc' }}
            </div>
          </div>
          
          <div class="card-body">
            <h3 class="promo-name">{{ promo.name }}</h3>
            <div class="promo-dates">
              <span class="date-icon">📅</span>
              {{ promo.startDate }} — {{ promo.endDate }}
            </div>
            
            <div class="applied-info">
              <div class="applied-header">
                <span class="count">Áp dụng: {{ promo.appliedBooks.length }} bộ truyện</span>
              </div>
              <div class="applied-list">
                <div v-for="ab in promo.appliedBooks.slice(0, 3)" :key="ab.id" class="ab-tag">
                  {{ ab.name }} <span class="disc">-{{ ab.discount }}%</span>
                </div>
                <div v-if="promo.appliedBooks.length > 3" class="more">
                  + {{ promo.appliedBooks.length - 3 }} bộ khác...
                </div>
              </div>
            </div>
          </div>

          <div class="card-footer">
            <button class="btn-text edit" @click="openEditModal(promo)">Sửa chi tiết</button>
            <button class="btn-text delete" @click="deletePromo(promo.id)">Xóa</button>
          </div>
        </div>
      </div>

      <!-- Add/Edit Promotion Modal -->
      <BaseModal 
  :is-open="isModalOpen" 
  :title="isEditing ? 'Sửa chương trình khuyến mãi' : 'Tạo khuyến mãi mới'"
  @close="isModalOpen = false"
>
  <div class="promo-form">
    <!-- Thông tin chung -->
    <div class="form-card">
      <div class="card-title">
        <span class="title-icon">📋</span>
        Thông tin chung
      </div>
      <div class="form-row two-cols">
        <div class="input-group full-width">
          <label>Tên chương trình <span class="required">*</span></label>
          <input v-model="formPromo.name" type="text" placeholder="VD: Giảm giá mùa hè 2026" />
        </div>
        <div class="input-group">
          <label>Dịp / Sự kiện</label>
          <input v-model="formPromo.occasion" type="text" placeholder="VD: Lễ 30/4" />
        </div>
        <div class="input-group">
          <label>Ngày bắt đầu <span class="required">*</span></label>
          <input v-model="formPromo.startDate" type="date" />
        </div>
        <div class="input-group">
          <label>Ngày kết thúc <span class="required">*</span></label>
          <input v-model="formPromo.endDate" type="date" />
        </div>
      </div>
    </div>

    <!-- Chọn truyện -->
    <div class="form-card">
      <div class="card-title">
        <span class="title-icon">📚</span>
        Áp dụng cho bộ truyện
      </div>
      <div class="book-picker-layout">
        <!-- Cột bên trái: danh sách có sẵn -->
        <div class="picker-panel">
          <div class="panel-header">
            <span> Danh sách truyện</span>
            <div class="search-mini">
              <input 
                v-model="searchQuery" 
                type="text" 
                placeholder="Tìm theo tên hoặc mã..."
              />
            </div>
          </div>
          <div class="book-list">
            <div v-if="filteredBooksSearch.length === 0" class="empty-state">
               Không còn truyện để chọn
            </div>
            <div 
              v-for="b in filteredBooksSearch" 
              :key="b.id" 
              class="book-item"
              @click="addBookToPromo(b)"
            >
              <div class="book-info">
                <div class="book-name">{{ b.name }}</div>
                <div class="book-code">{{ b.code }}</div>
              </div>
              <button class="add-btn">+ Thêm</button>
            </div>
          </div>
        </div>

        <!-- Cột bên phải: truyện đã chọn + giảm giá -->
        <div class="picker-panel">
          <div class="panel-header">
            <span>Đã chọn ({{ formPromo.appliedBooks.length }})</span>
          </div>
          <div class="selected-list">
            <div v-if="formPromo.appliedBooks.length === 0" class="empty-state">
              Chưa có truyện nào được chọn
            </div>
            <div v-for="ab in formPromo.appliedBooks" :key="ab.id" class="selected-item">
              <div class="selected-info">
                <div class="selected-name">{{ ab.name }}</div>
                <div class="discount-control">
                  <input v-model.number="ab.discount" type="number" min="1" max="100" />
                  <span>%</span>
                </div>
              </div>
              <button class="remove-btn" @click="removeBookFromPromo(ab.id)">✕</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <template #footer>
    <div class="modal-footer">
      <button class="btn-secondary" @click="isModalOpen = false">Hủy bỏ</button>
      <button class="btn-primary" @click="savePromo">Lưu chương trình</button>
    </div>
  </template>
</BaseModal>
    </div>
  </DefaultLayout>
</template>

<style scoped>
.promo-page {
  padding: 32px;
  background: #f1f5f9;
  min-height: 100vh;
  font-family: 'Inter', system-ui, -apple-system, sans-serif;
}

/* Header */
.main-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 32px;
}

.title {
  font-size: 1.75rem;
  font-weight: 800;
  color: #0f172a;
  margin-bottom: 4px;
}

.subtitle {
  color: #64748b;
  font-size: 0.95rem;
}

.btn-primary {
  background: linear-gradient(135deg, #2563eb, #1d4ed8);
  color: white;
  border: none;
  padding: 12px 24px;
  border-radius: 12px;
  font-weight: 700;
  cursor: pointer;
  transition: 0.3s;
  box-shadow: 0 4px 6px -1px rgba(37, 99, 235, 0.2);
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 15px -3px rgba(37, 99, 235, 0.3);
}

/* Grid & Cards */
.promo-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  gap: 24px;
}

.promo-card {
  background: white;
  border-radius: 20px;
  padding: 24px;
  border: 1px solid #e2e8f0;
  display: flex;
  flex-direction: column;
  transition: 0.3s;
  position: relative;
  overflow: hidden;
}

.promo-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 20px -5px rgba(0, 0, 0, 0.05);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.occasion-badge {
  background: #f1f5f9;
  color: #475569;
  padding: 4px 12px;
  border-radius: 8px;
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
}

.status-indicator {
  font-size: 0.75rem;
  font-weight: 800;
  padding: 4px 10px;
  border-radius: 100px;
}

.status-indicator.active { background: #dcfce7; color: #166534; }
.status-indicator.upcoming { background: #fef9c3; color: #854d0e; }
.status-indicator.expired { background: #fee2e2; color: #991b1b; }

.promo-name {
  font-size: 1.25rem;
  font-weight: 700;
  color: #1e293b;
  margin-bottom: 8px;
}

.promo-dates {
  font-size: 0.85rem;
  color: #64748b;
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 20px;
}

.applied-info {
  background: #f8fafc;
  border-radius: 12px;
  padding: 16px;
  flex: 1;
}

.applied-header {
  font-size: 0.8rem;
  font-weight: 700;
  color: #475569;
  margin-bottom: 12px;
  text-transform: uppercase;
}

.applied-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.ab-tag {
  background: white;
  border: 1px solid #e2e8f0;
  padding: 4px 10px;
  border-radius: 8px;
  font-size: 0.8rem;
  color: #334155;
  display: flex;
  gap: 6px;
}

.ab-tag .disc {
  font-weight: 800;
  color: #ef4444;
}

.more {
  font-size: 0.8rem;
  color: #94a3b8;
  padding: 4px;
}

.card-footer {
  margin-top: 24px;
  display: flex;
  gap: 12px;
}

.btn-text {
  background: none;
  border: none;
  padding: 8px;
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
  transition: 0.2s;
}

.btn-text.edit { color: #2563eb; }
.btn-text.delete { color: #ef4444; }
.btn-text:hover { opacity: 0.7; }

/* Modal Form */
.form-container {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.section-title {
  font-size: 0.95rem;
  font-weight: 700;
  color: #334155;
  margin-bottom: 16px;
  padding-bottom: 8px;
  border-bottom: 1px solid #f1f5f9;
}

.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.form-group.full { grid-column: span 2; }

.form-group label {
  display: block;
  font-size: 0.85rem;
  font-weight: 600;
  color: #64748b;
  margin-bottom: 6px;
}

.form-group input {
  width: 100%;
  padding: 10px 14px;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  outline: none;
  transition: 0.2s;
}

.form-group input:focus {
  border-color: #2563eb;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
}

/* Book Selection New Layout */
.selection-layout {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  background: #f8fafc;
  padding: 16px;
  border-radius: 16px;
  border: 1px solid #e2e8f0;
}

.sub-title {
  font-size: 0.8rem;
  font-weight: 700;
  color: #64748b;
  margin-bottom: 12px;
  text-transform: uppercase;
}

.books-list-scroll, .selected-books-list {
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  height: 250px;
  overflow-y: auto;
  padding: 8px;
}

.book-pick-item, .ab-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px;
  border-bottom: 1px solid #f1f5f9;
  border-radius: 8px;
  transition: 0.2s;
}

.book-pick-item:hover { background: #f8fafc; cursor: pointer; }
.book-pick-item .b-info { display: flex; flex-direction: column; }
.book-pick-item .b-name { font-size: 0.85rem; font-weight: 600; color: #1e293b; }
.book-pick-item .b-code { font-size: 0.75rem; color: #94a3b8; }

.btn-add-small {
  background: #eff6ff;
  color: #2563eb;
  border: none;
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 0.75rem;
  font-weight: 700;
  cursor: pointer;
}

.ab-item .ab-name { font-size: 0.85rem; font-weight: 500; color: #1e293b; flex: 1; margin-right: 10px; }
.ab-actions { display: flex; align-items: center; gap: 8px; }

.discount-box {
  display: flex;
  align-items: center;
  gap: 4px;
}

.discount-box input {
  width: 50px;
  padding: 4px;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  text-align: center;
  font-size: 0.85rem;
}

.discount-box span { font-weight: 700; color: #94a3b8; font-size: 0.8rem; }
.btn-remove { background: none; border: none; color: #cbd5e1; cursor: pointer; padding: 4px; }
.btn-remove:hover { color: #ef4444; }

.no-books, .empty-selection {
  display: flex;
  height: 100%;
  align-items: center;
  justify-content: center;
  color: #94a3b8;
  font-size: 0.85rem;
  text-align: center;
}
/* Modal form styles */
.promo-form {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.form-card {
  background: #ffffff;
  border-radius: 20px;
  padding: 20px 24px;
  box-shadow: 0 1px 2px rgba(0,0,0,0.03), 0 4px 8px rgba(0,0,0,0.02);
  border: 1px solid #eef2f6;
}

.card-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 700;
  font-size: 1rem;
  color: #1e293b;
  margin-bottom: 20px;
  padding-bottom: 12px;
  border-bottom: 2px solid #f1f5f9;
}

.title-icon {
  font-size: 1.2rem;
}

.form-row {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.form-row.two-cols {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.input-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.input-group.full-width {
  grid-column: span 2;
}

.input-group label {
  font-size: 0.8rem;
  font-weight: 600;
  color: #475569;
  letter-spacing: 0.3px;
}

.required {
  color: #ef4444;
  margin-left: 2px;
}

.input-group input {
  padding: 10px 14px;
  border: 1px solid #e2e8f0;
  border-radius: 14px;
  font-size: 0.9rem;
  transition: all 0.2s ease;
  background: #fefefe;
}

.input-group input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59,130,246,0.15);
}

/* Book picker layout */
.book-picker-layout {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.picker-panel {
  background: #fafcff;
  border-radius: 18px;
  border: 1px solid #eef2f8;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.panel-header {
  padding: 14px 16px;
  background: #ffffff;
  border-bottom: 1px solid #edf2f7;
  font-weight: 600;
  color: #334155;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.search-mini input {
  padding: 6px 12px;
  border-radius: 30px;
  border: 1px solid #e2e8f0;
  font-size: 0.75rem;
  width: 160px;
  transition: 0.2s;
}

.search-mini input:focus {
  border-color: #3b82f6;
  outline: none;
  width: 200px;
}

.book-list, .selected-list {
  height: 280px;
  overflow-y: auto;
  padding: 8px;
}

.book-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 12px;
  margin-bottom: 6px;
  background: white;
  border-radius: 14px;
  border: 1px solid transparent;
  transition: all 0.2s;
  cursor: pointer;
}

.book-item:hover {
  border-color: #cbdff2;
  background: #f8fafd;
  transform: translateX(2px);
}

.book-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.book-name {
  font-weight: 600;
  font-size: 0.85rem;
  color: #0f172a;
}

.book-code {
  font-size: 0.7rem;
  color: #94a3b8;
}

.add-btn {
  background: #eef2ff;
  border: none;
  padding: 4px 12px;
  border-radius: 40px;
  font-size: 0.7rem;
  font-weight: 600;
  color: #2563eb;
  cursor: pointer;
  transition: 0.2s;
}

.add-btn:hover {
  background: #2563eb;
  color: white;
}

.selected-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: white;
  padding: 10px 12px;
  margin-bottom: 8px;
  border-radius: 14px;
  border: 1px solid #eef2f8;
}

.selected-info {
  display: flex;
  align-items: center;
  gap: 16px;
  flex: 1;
  flex-wrap: wrap;
}

.selected-name {
  font-size: 0.85rem;
  font-weight: 500;
  color: #1e293b;
  flex: 1;
}

.discount-control {
  display: flex;
  align-items: center;
  gap: 6px;
  background: #f8fafc;
  padding: 4px 10px;
  border-radius: 30px;
}

.discount-control input {
  width: 48px;
  padding: 4px 6px;
  border: 1px solid #e2e8f0;
  border-radius: 20px;
  text-align: center;
  font-size: 0.8rem;
  font-weight: 500;
}

.discount-control span {
  font-weight: 600;
  color: #ef4444;
  font-size: 0.8rem;
}

.remove-btn {
  background: none;
  border: none;
  font-size: 1.1rem;
  color: #cbd5e1;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 30px;
  transition: 0.2s;
}

.remove-btn:hover {
  color: #ef4444;
  background: #fff1f0;
}

.empty-state {
  text-align: center;
  padding: 40px 20px;
  color: #94a3b8;
  font-size: 0.8rem;
}

/* Scrollbar tinh chỉnh */
.book-list::-webkit-scrollbar,
.selected-list::-webkit-scrollbar {
  width: 4px;
}

.book-list::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 10px;
}

.book-list::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 10px;
}

/* Modal footer */
.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding-top: 8px;
}

.btn-secondary {
  background: #f1f5f9;
  border: none;
  padding: 10px 20px;
  border-radius: 40px;
  font-weight: 600;
  color: #334155;
  cursor: pointer;
  transition: 0.2s;
}

.btn-secondary:hover {
  background: #e2e8f0;
}

.btn-primary {
  background: linear-gradient(105deg, #2563eb, #1e40af);
  border: none;
  padding: 10px 24px;
  border-radius: 40px;
  font-weight: 600;
  color: white;
  cursor: pointer;
  box-shadow: 0 2px 6px rgba(37,99,235,0.3);
  transition: 0.2s;
}

.btn-primary:hover {
  transform: translateY(-1px);
  box-shadow: 0 8px 18px rgba(37,99,235,0.25);
}
</style>