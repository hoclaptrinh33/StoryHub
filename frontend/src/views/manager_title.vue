<script setup lang="ts">
import { ref } from 'vue';
import DefaultLayout from '../components/layout/defaultLayout.vue'
import BaseModal from '../components/layout/BaseModal.vue'
const isModalOpen = ref(false);
const isItemsModalOpen = ref(false);

const selectedBook = ref<any>(null);
const selectedVolume = ref<any>(null);
// Dữ liệu giả lập
const books = ref([
  { 
    id: 1, code: 'TR001', name: 'One Piece - Tập 105', description: 'Hành trình hải tặc...', author: 'Oda Eiichiro', genre: 'Shonen', publisher: 'Kim Đồng', image: 'https://via.placeholder.com/50x70',
    volumes: [{ id: 1, code: 'VOL-01', name: 'One Piece', volume: '105', isbn: '978-604-123',so_luong:10,
        items: [{ id: 'BC-001', name: 'One Piece', volume: '105', status: 'Có sẵn', 
            condition: 'Mới', price: '20.000đ', rent_price: '5.000đ', 
            start_date: '2026-04-01', end_date: '2026-05-01', note: 'Không', version: 'Tái bản' }]
     }]
  },
  { 
    id: 2, code: 'TR002', name: 'Thám Tử Lừng Danh Conan', description: 'Thám tử bị teo nhỏ...', author: 'Aoyama Gosho', genre: 'Trinh thám', publisher: 'Kim Đồng', image: 'https://via.placeholder.com/50x70',
    volumes: [{ id: 2, code: 'VOL-02', name: 'Conan', volume: '98', isbn: '978-604-456',so_luong:10 
        ,items: [{ id: 'BC-001', name: 'One Piece', volume: '105', status: 'Có sẵn', 
            condition: 'Mới', price: '20.000đ', rent_price: '5.000đ', 
            start_date: '2026-04-01', end_date: '2026-05-01', note: 'Không', version: 'Tái bản' }]
    }]
  },
]);
const openVolumeModal = (book: any) => {
  selectedBook.value = book;
  isModalOpen.value = true;
};
const openItemsModal = (vol: any) => {
  selectedVolume.value = vol; 
  isItemsModalOpen.value = true;
};
</script>

<template>
  <DefaultLayout>
    <div class="main-content">
      <div class="actions-bar">
        <h2 class="page-title">Danh sách truyện</h2>
        <div class="search-actions">
            <input type="text" placeholder="Tìm kiếm truyện..." class="search-input" />
            <button class="btn-add">+ Thêm truyện mới</button>
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
            <tr v-for="book in books" :key="book.id" @click="openVolumeModal(book)" class="clickable-row">
              <td class="code-text">{{ book.code }}</td>
              <td><img :src="book.image" class="book-thumbnail" /></td>
              <td class="font-medium">{{ book.name }}</td>
              <td class="description-cell">{{ book.description }}</td>
              <td>{{ book.author }}</td>
              <td><span class="badge">{{ book.genre }}</span></td>
              <td>{{ book.publisher }}</td>
              <td>
                <div class="action-buttons">
                  <button class="btn-icon edit" title="Sửa">✏️</button>
                  <button class="btn-icon delete" title="Xóa">🗑️</button>
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
                <button class="btn-action edit">✏️</button>
                <button class="btn-action delete">🗑️</button>
              </td>
            </tr>
          </tbody>
        </table>

        <template #footer>
          <button class="btn-secondary" @click="isModalOpen = false">Đóng</button>
          <button class="btn-primary">+ Thêm tập mới</button>
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
                <button class="btn-action edit">✏️</button>
                <button class="btn-action delete">🗑️</button>
              </td>
            </tr>
          </tbody>
        </table>

        <template #footer>
          <button class="btn-secondary" @click="isItemsModalOpen = false">Đóng</button>
          <button class="btn-primary">+ Thêm truyện mới</button>
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
</style>