<script setup lang="ts">
import { ref, computed, inject, onMounted } from 'vue';
import { 
  fetchTitlesWithVolumes, 
  createTitle as apiCreateTitle,
  updateTitle as apiUpdateTitle,
  deleteTitle as apiDeleteTitle,
  createVolume as apiCreateVolume,
  updateVolume as apiUpdateVolume,
  deleteVolume as apiDeleteVolume,
  createItem as apiCreateItem,
  updateItem as apiUpdateItem,
  deleteItem as apiDeleteItem,
  convertToRental,
  buildRequestId,
} from '../services/storyhubApi';
import { useAuthStore } from '../stores/auth';

const addNotification = inject('addNotification') as any;
const showConfirm = inject('showConfirm') as any;
import DefaultLayout from '../components/layout/defaultLayout.vue'
import BaseModal from '../components/layout/BaseModal.vue'

const authStore = useAuthStore();
const token = computed(() => authStore.token ?? 'manager-demo');

// ─── Modal state ─────────────────────────────────────────────────────────────
const isModalOpen = ref(false);
const isItemsModalOpen = ref(false);
const isAddBookModalOpen = ref(false);
const isEditBookModalOpen = ref(false);
const isAddVolumeModalOpen = ref(false);
const isEditVolumeModalOpen = ref(false);
const isAddItemModalOpen = ref(false);
const isEditItemModalOpen = ref(false);
const isConvertRentalModalOpen = ref(false);

const selectedBook = ref<any>(null);
const selectedVolume = ref<any>(null);

// ─── Form state ───────────────────────────────────────────────────────────────
const formBook = ref({ id: 0, code: '', name: '', description: '', author: '', genre: '', publisher: '', image: '', volumes: [] as any[] });
const formVolume = ref({ id: 0, volume: 0, isbn: '', so_luong: 0, price: 0 as string | number, rent_price: 0 as string | number });
const formItem = ref({ id: '', status: 'Có sẵn', condition: 'Mới', note: '' });
const formConvert = ref({ quantity: 1 });

// ─── API data & loading ───────────────────────────────────────────────────────
const isLoading = ref(false);
const apiError = ref('');

// books = danh sách đầu truyện từ API
const books = ref<any[]>([]);

async function loadTitles(q?: string) {
  isLoading.value = true;
  apiError.value = '';
  try {
    const data = await fetchTitlesWithVolumes(q, token.value);
    books.value = data.map(title => ({
      id: title.id,
      code: `TR${String(title.id).padStart(3, '0')}`,
      name: title.name,
      description: title.description ?? '',
      author: title.author ?? '',
      genre: title.genre ?? '',
      publisher: title.publisher ?? '',
      image: title.cover_url ? `http://127.0.0.1:8000${title.cover_url}` : 'https://via.placeholder.com/50x70',
      _raw: title,
      volumes: title.volumes.map(vol => ({
        id: vol.id,
        code: vol.isbn ?? `VOL-${vol.id}`,
        name: title.name,
        volume: String(vol.volume_number),
        isbn: vol.isbn ?? '',
        so_luong: vol.items ? vol.items.length : 0, // Cập nhật theo tổng items
        retail_stock: vol.retail_stock,
        price: vol.p_sell_new,
        rent_price: vol.price_rental,
        deposit: vol.price_deposit,
        items: vol.items.map(it => ({
          id: it.id,
          volume: String(vol.volume_number),
          status: it.status,
          condition: it.condition_level >= 80 ? 'Tốt' : it.condition_level >= 50 ? 'Trung bình' : 'Kém',
          note: it.notes ?? '',
          has_barcode: it.has_barcode,
          can_rent: it.has_barcode, 
          version: `Bản in lần ${it.version_no}`,
          start_date: it.reserved_at ? new Date(it.reserved_at).toLocaleDateString() : '—',
          end_date: it.reservation_expire_at ? new Date(it.reservation_expire_at).toLocaleDateString() : '—',
        })),
      })),
    }));
  } catch (e: any) {
    apiError.value = e?.message ?? 'Không tải được danh sách truyện.';
    addNotification?.('error', apiError.value);
  } finally {
    isLoading.value = false;
  }
}

onMounted(() => loadTitles());

// ─── Search & Filter ──────────────────────────────────────────────────────────
const searchQuery = ref('');
const filterAuthor = ref('');
const filterPublisher = ref('');
const filterGenre = ref('');

const authors = computed(() => [...new Set(books.value.map(b => b.author).filter(Boolean))]);
const publishers = computed(() => [...new Set(books.value.map(b => b.publisher).filter(Boolean))]);
const genres = computed(() => [...new Set(books.value.map(b => b.genre).filter(Boolean))]);

const filteredBooks = computed(() => {
  return books.value.filter(book => {
    const matchesSearch = (book.name || '').toLowerCase().includes((searchQuery.value || '').toLowerCase()) || 
                          (book.code || '').toLowerCase().includes((searchQuery.value || '').toLowerCase());
    const matchesAuthor = !filterAuthor.value || book.author === filterAuthor.value;
    const matchesPublisher = !filterPublisher.value || book.publisher === filterPublisher.value;
    const matchesGenre = !filterGenre.value || book.genre === filterGenre.value;
    return matchesSearch && matchesAuthor && matchesPublisher && matchesGenre;
  });
});

<<<<<<< HEAD

=======
// ─── Modal helpers ────────────────────────────────────────────────────────────
>>>>>>> 814fe260b1a73aa42624df817c78f33c24eb3a1e
const openVolumeModal = (book: any) => {
  selectedBook.value = book;
  isModalOpen.value = true;
};
const openItemsModal = (vol: any) => {
  selectedVolume.value = vol; 
  isItemsModalOpen.value = true;
};

// ─── CRUD Books ──────────────────
const openAddBook = () => {
  formBook.value = { id: 0, code: '', name: '', description: '', author: '', genre: '', publisher: '', image: '', volumes: [] };
  isAddBookModalOpen.value = true;
};
const openEditBook = (book: any) => {
  formBook.value = { ...book };
  isEditBookModalOpen.value = true;
};
const saveBook = async () => {
  try {
    const payload = {
      name: formBook.value.name,
      description: formBook.value.description,
      author: formBook.value.author,
      genre: formBook.value.genre,
      publisher: formBook.value.publisher,
      request_id: buildRequestId('book'),
    };
    if (formBook.value.id) {
       await apiUpdateTitle(formBook.value.id, payload);
       addNotification('success', 'Đã cập nhật Truyện!');
    } else {
       await apiCreateTitle(payload);
       addNotification('success', 'Đã tạo Truyện mới!');
    }
    isAddBookModalOpen.value = false;
    isEditBookModalOpen.value = false;
    await loadTitles();
  } catch (err: any) {
    addNotification('error', err.message || 'Lỗi lưu sách');
  }
};
const deleteBook = async (id: number) => {
  if (await showConfirm('Bạn có chắc muốn xóa đầu truyện này? Tất cả các tập và bản sao bên trong sẽ bị xóa theo.')) {
    try {
      await apiDeleteTitle(id);
      addNotification('success', 'Đã xóa đầu truyện thành công!');
      await loadTitles();
    } catch(err: any) {
      addNotification('error', 'Lỗi: ' + err.message);
    }
  }
};

// ─── CRUD Volumes ──────────────────────────────────────────────────────────────
const openAddVolume = () => {
  formVolume.value = { id: 0, volume: 0, isbn: '', so_luong: 0, price: '', rent_price: '' };
  isAddVolumeModalOpen.value = true;
};
const openEditVolume = (vol: any) => {
  formVolume.value = {
    id: vol.id,
    volume: Number(vol.volume),
    isbn: vol.isbn,
    so_luong: vol.retail_stock,
    price: vol.price,
    rent_price: vol.rent_price,
  };
  isEditVolumeModalOpen.value = true;
};
const isSavingVolume = ref(false);
const saveVolume = async () => {
  if (!selectedBook.value) return;
  if (!formVolume.value.isbn || !formVolume.value.volume) {
    addNotification('error', 'Vui lòng nhập ISBN và số tập.');
    return;
  }
  isSavingVolume.value = true;
  try {
    if (formVolume.value.id) {
        await apiUpdateVolume(formVolume.value.id, {
            volume_number: Number(String(formVolume.value.volume).replace(/\D/g, '')),
            isbn: formVolume.value.isbn,
            retail_stock: Number(formVolume.value.so_luong),
            p_sell_new: Number(String(formVolume.value.price).replace(/\D/g, '')),
            request_id: buildRequestId('update-vol')
        });
        addNotification('success', 'Đã cập nhật tập truyện!');
    } else {
        await apiCreateVolume(
          {
            title_name: selectedBook.value.name,
            author: selectedBook.value.author ?? '',
            volume_number: Number(String(formVolume.value.volume).replace(/\D/g, '')),
            isbn: formVolume.value.isbn,
            retail_stock: Number(formVolume.value.so_luong),
            p_sell_new: Number(String(formVolume.value.price).replace(/\D/g, '')),
            description: selectedBook.value.description || '',
            cover_url: null,
            categories: selectedBook.value.genre ? [selectedBook.value.genre] : [],
            page_count: null,
            published_date: null,
            request_id: buildRequestId('add-volume'),
          },
          token.value,
        );
        addNotification('success', 'Đã tạo tập truyện thành công!');
    }
    isAddVolumeModalOpen.value = false;
    isEditVolumeModalOpen.value = false;
    await loadTitles();
    const updatedBook = books.value.find(b => b.id === selectedBook.value?.id);
    if (updatedBook) selectedBook.value = updatedBook;
  } catch (e: any) {
    addNotification('error', e?.message ?? 'Lưu tập thất bại.');
  } finally {
    isSavingVolume.value = false;
  }
};
const deleteVolume = async (book: any, volId: number) => {
  if (await showConfirm('Xóa tập này khỏi hệ thống?')) {
    try {
      await apiDeleteVolume(volId);
      addNotification('success', 'Thành công!');
      await loadTitles();
      const updatedBook = books.value.find(b => b.id === book.id);
      if (updatedBook) selectedBook.value = updatedBook;
    } catch(err: any) {
      addNotification('error', 'Lỗi: ' + err.message);
    }
  }
};

// ─── CRUD Items ────────────────────────────────────────────────────────────────
const openAddItem = () => {
  formItem.value = { id: '', status: 'available', condition: 'Mới', note: '' };
  isAddItemModalOpen.value = true;
};
const openEditItem = (item: any) => {
  formItem.value = { ...item };
  formItem.value.status = reverseStatusMap[item.status] || 'available';
  isEditItemModalOpen.value = true;
};
const saveItem = async () => {
  try {
    const conditionVal = formItem.value.condition === 'Tốt' ? 100 : formItem.value.condition === 'Trung bình' ? 50 : 20;
    const statusToSend = reverseStatusMap[formItem.value.status] || formItem.value.status;

   if (formItem.value.id && !isAddItemModalOpen.value) {
       await apiUpdateItem(formItem.value.id, {
           status: statusToSend,
           condition_level: conditionVal,
           notes: formItem.value.note || null,
           request_id: buildRequestId('update-item')
       });
       addNotification('success', 'Cập nhật bản sao thành công!');
    } else {
       await apiCreateItem({
           volume_id: selectedVolume.value.id,
           id: formItem.value.id || null, 
           condition_level: conditionVal,
           notes: formItem.value.note || null,
           version_no: 1,
           request_id: buildRequestId('create-item')
       });
       addNotification('success', 'Tạo bản sao thành công!');
    }
    isAddItemModalOpen.value = false;
    isEditItemModalOpen.value = false;
    await loadTitles();
    const updatedBook = books.value.find(b => b.id === selectedBook.value?.id);
    if (updatedBook) selectedVolume.value = updatedBook.volumes.find((v: any) => v.id === selectedVolume.value?.id);
  } catch (err: any) {
    addNotification('error', err.message || 'Lỗi lưu bản sao');
  }
};
const deleteItem = async (volume: any, itemId: string) => {
  if (await showConfirm('Xóa bản sao này khỏi hệ thống?')) {
     try {
       await apiDeleteItem(itemId);
       addNotification('success', 'Thành công!');
       await loadTitles();
       const updatedBook = books.value.find(b => b.id === selectedBook.value?.id);
       if (updatedBook) selectedVolume.value = updatedBook.volumes.find((v: any) => v.id === volume.id);
     } catch(e: any) {
       addNotification('error', 'Lỗi: ' + e.message);
     }
  }
};

const openConvertRental = () => {
  formConvert.value.quantity = 1;
  isConvertRentalModalOpen.value = true;
};

const saveConvertRental = async () => {
  if (!selectedVolume.value) return;
  try {
    await convertToRental({
      volume_id: selectedVolume.value.id,
      quantity: formConvert.value.quantity,
      request_id: buildRequestId('convert'),
      token: token.value,
    }, token.value);
    addNotification('success', 'Chuyển truyện thuê thành công!');
    isConvertRentalModalOpen.value = false;
    await loadTitles();
    const updatedBook = books.value.find(b => b.id === selectedBook.value?.id);
    if (updatedBook) selectedVolume.value = updatedBook.volumes.find((v: any) => v.id === selectedVolume.value?.id);
  } catch(err: any) {
    addNotification('error', err.message || 'Lỗi lưu bản sao');
  }
};

// ─── Format helpers ───────────────────────────────────────────────────────────
const statusMap: Record<string, string> = {
  'available': 'Có sẵn',
  'rented': 'Đã thuê',
  'maintenance': 'Bảo trì'
};

const reverseStatusMap: Record<string, string> = {
  'Có sẵn': 'available',
  'Đã thuê': 'rented',
  'Bảo trì': 'maintenance'
};

// Hàm chuyển đổi hiển thị
const getStatusText = (status: string): string => {
  return statusMap[status] || status;
};
// Format tiền VND
const formatVND = (val: number) => {
  if (typeof val !== 'number') return '—';
  return val.toLocaleString('vi-VN') + 'đ';
};
</script>

<template>
  <DefaultLayout>
    <div class="main-content">
      <div v-if="isLoading" class="loading-overlay">Đang tải dữ liệu...</div>
      
      <div class="actions-bar">
        <h2 class="page-title">Quản lý đầu truyện</h2>
        <div class="search-actions">
            <div class="filter-group">
                <select v-model="filterAuthor" class="filter-select">
                    <option value="">Tác giả</option>
                    <option v-for="a in authors" :key="a" :value="a">{{ a }}</option>
                </select>
                <select v-model="filterGenre" class="filter-select">
                    <option value="">Thể loại</option>
                    <option v-for="g in genres" :key="g" :value="g">{{ g }}</option>
                </select>
                <select v-model="filterPublisher" class="filter-select">
                    <option value="">Tất cả NXB</option>
                    <option v-for="p in publishers" :key="p" :value="p">{{ p }}</option>
                </select>
            </div>
            <input v-model="searchQuery" type="text" placeholder="Tìm kiếm truyện..." class="search-input" />
            <button class="btn-add" @click="openAddBook">+ Đầu truyện</button>
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
              <th>Tên Truyện</th>
              <th>Tập số</th>
              <th>ISBN</th>
              <th>Giá bán</th>
              <th>Giá thuê</th>
              <th>Số lượng</th>
              <th class="text-center">Hành động</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="vol in selectedBook?.volumes" :key="vol.id" @click="openItemsModal(vol)" class="clickable-row">
              <td>{{ vol.name }}</td>
              <td>{{ vol.volume }}</td>
              <td>{{ vol.isbn }}</td>
              <td class="font-bold text-gray-700">{{ formatVND(vol.price) }}</td>
              <td class="font-bold text-blue-600">{{ formatVND(vol.rent_price) }}</td>
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
    <td>{{ getStatusText(items.status) }}</td>   <!-- Sửa dòng này -->
    <td>{{ items.condition }}</td>
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
          <button class="btn-primary" @click="openConvertRental" v-if="selectedVolume?.so_luong > 0">Chuyển truyện thuê (Tồn: {{ selectedVolume?.so_luong }})</button>
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
            <label>ISBN</label>
            <input v-model="formVolume.isbn" type="text" placeholder="978-..." />
          </div>
          <div class="form-group">
            <label>Tập số</label>
            <input v-model="formVolume.volume" type="text" placeholder="105" />
          </div>
          <div class="form-group">
            <label>Số lượng</label>
            <input v-model="formVolume.so_luong" type="number" />
          </div>
          <div class="form-group">
            <label>Giá</label>
            <input v-model="formVolume.price" type="text" placeholder="20.000đ" />
          </div>
          <div class="form-group">
            <label>Giá thuê</label>
            <input v-model="formVolume.rent_price" type="text" placeholder="5.000đ" />
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
          <div class="form-group" v-if="isEditItemModalOpen">
            <label>Mã vạch</label>
            <input v-model="formItem.id" type="text" disabled />
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

      <!-- Convert to rental Modal -->
      <BaseModal 
        :is-open="isConvertRentalModalOpen" 
        title="Chuyển sang truyện thuê"
        @close="isConvertRentalModalOpen = false"
      >
        <div class="form-grid">
          <div class="form-group full-width">
            <label>Số lượng muốn chuyển từ kho bán</label>
            <input v-model.number="formConvert.quantity" type="number" min="1" :max="selectedVolume?.so_luong" />
            <small style="color: grey;">Lưu ý: Hành động này sẽ trừ hàng tồn bán và tạo mã vạch bản sao mới.</small>
          </div>
        </div>
        <template #footer>
          <button class="btn-secondary" @click="isConvertRentalModalOpen = false">Hủy</button>
          <button class="btn-primary" @click="saveConvertRental">Xác nhận chuyển</button>
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