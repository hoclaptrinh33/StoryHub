<script setup lang="ts">
import { ref, computed, inject } from 'vue';

const addNotification = inject('addNotification') as any;
const showConfirm = inject('showConfirm') as any;
import DefaultLayout from '../components/layout/defaultLayout.vue'
import BaseModal from '../components/layout/BaseModal.vue'
const isModalOpen = ref(false);
const isItemsModalOpen = ref(false);

const isAddBookModalOpen = ref(false);
const isEditBookModalOpen = ref(false);
const isAddVolumeModalOpen = ref(false);
const isEditVolumeModalOpen = ref(false);
const isAddItemModalOpen = ref(false);
const isEditItemModalOpen = ref(false);

const selectedBook = ref<any>(null);
const selectedVolume = ref<any>(null);

const formBook = ref({ id: 0, code: '', name: '', description: '', author: '', genre: '', publisher: '', image: 'https://via.placeholder.com/50x70', volumes: [] });
const formVolume = ref({ id: 0, code: '', name: '', volume: '', isbn: '', so_luong: 0, items: [] });
const formItem = ref({ id: '', volume: '', status: 'Có sẵn', condition: 'Mới', price: '', rent_price: '', start_date: '', end_date: '', note: '', version: 'Bản thường' });

// Search & Filter state
const searchQuery = ref('');
const filterAuthor = ref('');
const filterPublisher = ref('');
const filterGenre = ref('');

// Unique options for filters
const authors = computed(() => [...new Set(books.value.map(b => b.author))]);
const publishers = computed(() => [...new Set(books.value.map(b => b.publisher))]);
const genres = computed(() => [...new Set(books.value.map(b => b.genre))]);

// Filtered data
const filteredBooks = computed(() => {
  return books.value.filter(book => {
    const matchesSearch = book.name.toLowerCase().includes(searchQuery.value.toLowerCase()) || 
                         book.code.toLowerCase().includes(searchQuery.value.toLowerCase());
    const matchesAuthor = !filterAuthor.value || book.author === filterAuthor.value;
    const matchesPublisher = !filterPublisher.value || book.publisher === filterPublisher.value;
    const matchesGenre = !filterGenre.value || book.genre === filterGenre.value;
    
    return matchesSearch && matchesAuthor && matchesPublisher && matchesGenre;
  });
});


const openVolumeModal = (book: any) => {
  selectedBook.value = book;
  isModalOpen.value = true;
};
const openItemsModal = (vol: any) => {
  selectedVolume.value = vol; 
  isItemsModalOpen.value = true;
};

// CRUD Books
const openAddBook = () => {
  formBook.value = { id: Date.now(), code: '', name: '', description: '', author: '', genre: '', publisher: '', image: 'https://via.placeholder.com/50x70', volumes: [] };
  isAddBookModalOpen.value = true;
};
const openEditBook = (book: any) => {
  formBook.value = { ...book };
  isEditBookModalOpen.value = true;
};
const saveBook = () => {
  if (isEditBookModalOpen.value) {
    const index = books.value.findIndex(b => b.id === formBook.value.id);
    if (index !== -1) books.value[index] = { ...formBook.value };
    addNotification('success', 'Đã cập nhật thông tin truyện');
  } else {
    books.value.unshift({ ...formBook.value, id: Date.now(), volumes: [] });
    addNotification('success', 'Đã thêm truyện mới thành công');
  }
  isAddBookModalOpen.value = false;
  isEditBookModalOpen.value = false;
};
const deleteBook = async (id: number) => {
  if (await showConfirm('Bạn có chắc chắn muốn xóa truyện này không?')) {
    books.value = books.value.filter(b => b.id !== id);
    addNotification('success', 'Đã xóa truyện khỏi hệ thống');
  }
};

// CRUD Volumes
const openAddVolume = () => {
  formVolume.value = { id: Date.now(), code: '', name: selectedBook.value?.name, volume: '', isbn: '', so_luong: 0, items: [] };
  isAddVolumeModalOpen.value = true;
};
const openEditVolume = (vol: any) => {
  formVolume.value = { ...vol };
  isEditVolumeModalOpen.value = true;
};
const saveVolume = () => {
  if (!selectedBook.value) return;
  if (isEditVolumeModalOpen.value) {
    const index = selectedBook.value.volumes.findIndex((v: any) => v.id === formVolume.value.id);
    if (index !== -1) selectedBook.value.volumes[index] = { ...formVolume.value };
  } else {
    selectedBook.value.volumes.push({ ...formVolume.value });
  }
  isAddVolumeModalOpen.value = false;
  isEditVolumeModalOpen.value = false;
};
const deleteVolume = (book: any, volId: number) => {
  if (confirm('Bạn có chắc chắn muốn xóa tập này không?')) {
    book.volumes = book.volumes.filter((v: any) => v.id !== volId);
  }
}

// CRUD Items
const openAddItem = () => {
  formItem.value = { id: 'BC-' + Math.floor(Math.random() * 1000), volume: selectedVolume.value?.volume, status: 'Có sẵn', condition: 'Mới', price: '', rent_price: '', start_date: '', end_date: '', note: '', version: 'Bản thường' };
  isAddItemModalOpen.value = true;
};
const openEditItem = (item: any) => {
  formItem.value = { ...item };
  isEditItemModalOpen.value = true;
};
const saveItem = () => {
  if (!selectedVolume.value) return;
  if (isEditItemModalOpen.value) {
    const index = selectedVolume.value.items.findIndex((i: any) => i.id === formItem.value.id);
    if (index !== -1) selectedVolume.value.items[index] = { ...formItem.value };
  } else {
    selectedVolume.value.items.push({ ...formItem.value });
  }
  isAddItemModalOpen.value = false;
  isEditItemModalOpen.value = false;
};
const deleteItem = (volume: any, itemId: string) => {
  if (confirm('Bạn có chắc chắn muốn xóa bản sao này không?')) {
    volume.items = volume.items.filter((i: any) => i.id !== itemId);
  }
}
</script>

<template>
  <DefaultLayout>
    <div class="main-content">
      <div class="actions-bar">
        <h2 class="page-title">Danh sách truyện</h2>
        <div class="search-actions">
            <div class="filter-group">
                <select v-model="filterAuthor" class="filter-select">
                    <option value="">Tất cả tác giả</option>
                    <option v-for="a in authors" :key="a" :value="a">{{ a }}</option>
                </select>
                <select v-model="filterGenre" class="filter-select">
                    <option value="">Tất cả thể loại</option>
                    <option v-for="g in genres" :key="g" :value="g">{{ g }}</option>
                </select>
                <select v-model="filterPublisher" class="filter-select">
                    <option value="">Tất cả NXB</option>
                    <option v-for="p in publishers" :key="p" :value="p">{{ p }}</option>
                </select>
            </div>
            <input v-model="searchQuery" type="text" placeholder="Tìm kiếm truyện..." class="search-input" />
            <button class="btn-add" @click="openAddBook">+ Thêm truyện mới</button>
        </div>
      </div>

      <div class="table-container">
        <table>
          <thead>
            <tr>
              <th>Mã</th>
              <th>Ảnh</th>
              <th>Tên Truyện</th>
              <th>Mô tả</th>
              <th>Tác giả</th>
              <th>Thể loại</th>
              <th>NXB</th>
              <th class="text-center">Hành động</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="book in filteredBooks" :key="book.id" @click="openVolumeModal(book)" class="clickable-row">
              <td class="code-text">{{ book.code }}</td>
              <td><img :src="book.image" class="book-thumbnail" /></td>
              <td class="font-medium">{{ book.name }}</td>
              <td class="description-cell">{{ book.description }}</td>
              <td>{{ book.author }}</td>
              <td><span class="badge">{{ book.genre }}</span></td>
              <td>{{ book.publisher }}</td>
              <td>
                <div class="action-buttons">
                  <button class="btn-icon edit" title="Sửa" @click.stop="openEditBook(book)">✏️</button>
                  <button class="btn-icon delete" title="Xóa" @click.stop="deleteBook(book.id)">🗑️</button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <BaseModal 
        :is-open="isModalOpen" 
        :title="  selectedBook?.name" 
        @close="isModalOpen = false"
      >
        <table class="volume-table">
          <thead>
            <tr>
              <th>Mã Tập</th>
              <th>Tên Truyện</th>
              <th>Tập số</th>
              <th>ISBN</th>
              <th>Số lượng</th>
              <th class="text-center">Hành động</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="vol in selectedBook?.volumes" :key="vol.id" @click="openItemsModal(vol)" class="clickable-row">
              <td>{{ vol.code }}</td>
              <td>{{ vol.name }}</td>
              <td>{{ vol.volume }}</td>
              <td>{{ vol.isbn }}</td>
              <td>{{ vol.so_luong }}</td>
              <td class="text-center">
                <button class="btn-action edit" @click.stop="openEditVolume(vol)">✏️</button>
                <button class="btn-action delete" @click.stop="deleteVolume(selectedBook, vol.id)">🗑️</button>
              </td>
            </tr>
          </tbody>
        </table>

        <template #footer>
          <button class="btn-secondary" @click="isModalOpen = false">Đóng</button>
          <button class="btn-primary" @click="openAddVolume">+ Thêm tập mới</button>
        </template>
      </BaseModal>
      <BaseModal 
        :is-open="isItemsModalOpen" 
        :title="selectedBook?.name + ' - Tập ' + selectedVolume?.volume" 
        @close="isItemsModalOpen = false"
      >
        <table class="volume-table">
          <thead>
            <tr>
              <th>Mã Vạch</th>
              <th>Tập truyện</th>
              <th>Trạng thái</th>
              <th>Tình trạng</th>
              <th>Giá</th>
              <th>Giá thuê</th>
              <th>Bắt Đầu</th>
              <th>Hết hạn</th>
              <th>Ghi chú</th>
              <th>Phiên bản</th>
              <th class="text-center">Hành động</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="items in selectedVolume?.items" :key="items.id" class="clickable-row">
              <td>{{ items.id }}</td>
              <td>{{ items.volume }}</td>
              <td>{{ items.status }}</td>
              <td>{{ items.condition }}</td>
              <td>{{ items.price }}</td>
              <td>{{ items.rent_price }}</td>
              <td>{{ items.start_date }}</td>
              <td>{{ items.end_date }}</td>
              <td>{{ items.note }}</td>
              <td>{{ items.version }}</td>
              <td class="text-center">
                <button class="btn-action edit" @click.stop="openEditItem(items)">✏️</button>
                <button class="btn-action delete" @click.stop="deleteItem(selectedVolume, items.id)">🗑️</button>
              </td>
            </tr>
          </tbody>
        </table>

        <template #footer>
          <button class="btn-secondary" @click="isItemsModalOpen = false">Đóng</button>
          <button class="btn-primary" @click="openAddItem">+ Thêm bản sao mới</button>
        </template>
      </BaseModal>

      <!-- Edit/Add Book Modal -->
      <BaseModal 
        :is-open="isAddBookModalOpen || isEditBookModalOpen" 
        :title="isEditBookModalOpen ? 'Sửa thông tin truyện' : 'Thêm truyện mới'"
        @close="isAddBookModalOpen = false; isEditBookModalOpen = false"
      >
        <div class="form-grid">
          <div class="form-group">
            <label>Mã truyện</label>
            <input v-model="formBook.code" type="text" placeholder="TR001" />
          </div>
          <div class="form-group">
            <label>Tên truyện</label>
            <input v-model="formBook.name" type="text" placeholder="Nhập tên truyện..." />
          </div>
          <div class="form-group">
            <label>Tác giả</label>
            <input v-model="formBook.author" type="text" placeholder="Nhập tên tác giả..." />
          </div>
          <div class="form-group">
            <label>Thể loại</label>
            <input v-model="formBook.genre" type="text" placeholder="Shonen, Drama..." />
          </div>
          <div class="form-group">
            <label>Nhà xuất bản</label>
            <input v-model="formBook.publisher" type="text" placeholder="Nhập tên NXB..." />
          </div>
          <div class="form-group full-width">
            <label>Mô tả</label>
            <textarea v-model="formBook.description" rows="3"></textarea>
          </div>
        </div>
        <template #footer>
          <button class="btn-secondary" @click="isAddBookModalOpen = false; isEditBookModalOpen = false">Hủy</button>
          <button class="btn-primary" @click="saveBook">{{ isEditBookModalOpen ? 'Cập nhật' : 'Thêm mới' }}</button>
        </template>
      </BaseModal>

      <!-- Edit/Add Volume Modal -->
      <BaseModal 
        :is-open="isAddVolumeModalOpen || isEditVolumeModalOpen" 
        :title="isEditVolumeModalOpen ? 'Sửa tập truyện' : 'Thêm tập mới'"
        @close="isAddVolumeModalOpen = false; isEditVolumeModalOpen = false"
      >
        <div class="form-grid">
          <div class="form-group">
            <label>Mã tập</label>
            <input v-model="formVolume.code" type="text" placeholder="VOL-01" />
          </div>
          <div class="form-group">
            <label>Tập số</label>
            <input v-model="formVolume.volume" type="text" placeholder="105" />
          </div>
          <div class="form-group">
            <label>ISBN</label>
            <input v-model="formVolume.isbn" type="text" placeholder="978-..." />
          </div>
          <div class="form-group">
            <label>Số lượng</label>
            <input v-model="formVolume.so_luong" type="number" />
          </div>
        </div>
        <template #footer>
          <button class="btn-secondary" @click="isAddVolumeModalOpen = false; isEditVolumeModalOpen = false">Hủy</button>
          <button class="btn-primary" @click="saveVolume">{{ isEditVolumeModalOpen ? 'Cập nhật' : 'Thêm mới' }}</button>
        </template>
      </BaseModal>

      <!-- Edit/Add Item Modal -->
      <BaseModal 
        :is-open="isAddItemModalOpen || isEditItemModalOpen" 
        :title="isEditItemModalOpen ? 'Sửa bản sao' : 'Thêm bản sao mới'"
        @close="isAddItemModalOpen = false; isEditItemModalOpen = false"
      >
        <div class="form-grid">
          <div class="form-group">
            <label>Mã vạch</label>
            <input v-model="formItem.id" type="text" :disabled="isEditItemModalOpen" />
          </div>
          <div class="form-group">
            <label>Trạng thái</label>
            <select v-model="formItem.status">
              <option>Có sẵn</option>
              <option>Đã thuê</option>
              <option>Bảo trì</option>
            </select>
          </div>
          <div class="form-group">
            <label>Tình trạng</label>
            <input v-model="formItem.condition" type="text" placeholder="Mới, Cũ..." />
          </div>
          <div class="form-group">
            <label>Giá</label>
            <input v-model="formItem.price" type="text" placeholder="20.000đ" />
          </div>
          <div class="form-group">
            <label>Giá thuê</label>
            <input v-model="formItem.rent_price" type="text" placeholder="5.000đ" />
          </div>
          <div class="form-group">
            <label>Phiên bản</label>
            <input v-model="formItem.version" type="text" placeholder="Tái bản..." />
          </div>
          <div class="form-group full-width">
            <label>Ghi chú</label>
            <input v-model="formItem.note" type="text" />
          </div>
        </div>
        <template #footer>
          <button class="btn-secondary" @click="isAddItemModalOpen = false; isEditItemModalOpen = false">Hủy</button>
          <button class="btn-primary" @click="saveItem">{{ isEditItemModalOpen ? 'Cập nhật' : 'Thêm mới' }}</button>
        </template>
      </BaseModal>
      </div>
  </DefaultLayout>
</template>

<style scoped>
.main-content { padding: 24px; background: #f9fafb; min-height: 100vh; }

.actions-bar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; }
.page-title { font-size: 1.5rem; color: #111827; margin: 0; }

.search-input { padding: 10px 16px; border: 1px solid #e5e7eb; border-radius: 8px; width: 250px; outline: none; }
.filter-group { display:inline; gap: 8px; }
.filter-select { padding: 10px; border: 1px solid #e5e7eb; border-radius: 8px; outline: none; min-width: 150px; cursor: pointer; background: white; margin-right: 10px;}
.filter-select:focus { border-color: #2563eb; }
.btn-add { background: #2563eb; color: white; border: none; padding: 10px 20px; border-radius: 8px; font-weight: 600; cursor: pointer; transition: 0.3s;margin-left: 10px; }
.btn-add:hover { background: #1d4ed8; }

.table-container { background: white; border-radius: 12px; border: 1px solid #e5e7eb; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
table { width: 100%; border-collapse: collapse; }
th { background: #f3f4f6; padding: 16px; font-size: 0.85rem; color: #374151; text-transform: uppercase; }
td { padding: 16px; border-bottom: 1px solid #f3f4f6; color: #4b5563; align-items: center; text-align: center; }

.code-text { font-weight: 600; color: #2563eb; }
.book-thumbnail { width: 45px; height: 60px; border-radius: 4px; object-fit: cover; }
.badge { background: #e0e7ff; color: #4338ca; padding: 4px 8px; border-radius: 6px; font-size: 0.75rem; font-weight: 600; }

.action-buttons { display: flex; gap: 8px; justify-content: center; }
.btn-icon { background: none; border: none; cursor: pointer; padding: 5px; font-size: 1.1rem; }
.btn-icon:hover { opacity: 0.7; }

/* Các button */
.btn-action { padding: 4px 8px; border: none; background: none; cursor: pointer; }
.btn-action:hover { transform: scale(1.2); }

.btn-primary { background: #2563eb; color: white; padding: 8px 16px; border-radius: 6px; border: none; cursor: pointer; }
.btn-primary:hover { background: #1d4ed8; }

.btn-secondary { background: #e2e8f0; color: #475569; padding: 8px 16px; border-radius: 6px; border: none; cursor: pointer; }

/* Form Styles */
.form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-top: 10px; }
.form-group { display: flex; flex-direction: column; gap: 6px; }
.form-group.full-width { grid-column: span 2; }
.form-group label { font-size: 0.85rem; font-weight: 600; color: #4b5563; }
.form-group input, .form-group textarea, .form-group select { 
  padding: 8px 12px; border: 1px solid #e5e7eb; border-radius: 6px; font-size: 0.9rem; outline: none; transition: 0.2s;
}
.form-group input:focus, .form-group textarea:focus, .form-group select:focus { border-color: #2563eb; box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.1); }
</style>