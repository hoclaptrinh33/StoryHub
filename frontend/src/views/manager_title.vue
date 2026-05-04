<script setup lang="ts">
// ⚠️ PHẦN SCRIPT GIỮ NGUYÊN TUYỆT ĐỐI – KHÔNG THAY ĐỔI BẤT KỲ LOGIC NÀO
import { ref, computed, inject, onMounted,onBeforeUnmount, watch } from 'vue';
import { 
  API_BASE_URL,
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
  autofillTitleMetadata,
  StoryHubApiError,
  importCoverImage,
} from '../services/storyhubApi';
import { useAuthStore } from '../stores/auth';
import { useScannerStore } from '../stores/scanner';

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
const isRestockModalOpen = ref(false);
const restockVolume = ref<any>(null);
const restockQuantity = ref(1);

const selectedBook = ref<any>(null);
const selectedVolume = ref<any>(null);
const scannerStore = useScannerStore();
let stopScannerWatch: (() => void) | null = null;

// ─── Form state ───────────────────────────────────────────────────────────────
const formBook = ref({ id: 0, code: '', name: '', description: '', author: '', genre: '', publisher: '', image: '', volumes: [] as any[] });
const formVolume = ref({ id: 0, volume: 0, isbn: '', so_luong: 0, price: 0 as string | number, rent_price: 0 as string | number });
const formItem = ref({ id: '', status: 'Có sẵn', condition: 'Mới', note: '', item_type: 'rental' });
const formConvert = ref({ quantity: 1 });

// ─── Scan state ───────────────────────────────────────────────────────────────
const isScanModalOpen = ref(false);
const isScanning = ref(false);
const scanError = ref('');
const scanForm = ref({ isbn: '', name: '', author: '', description: '', cover_url: '', genre: '', publisher: '', volume: 1, price: 0, retail_stock: 1 });

const openScanModal = (initialIsbn = '') => {
  scanForm.value = { 
    isbn: initialIsbn, 
    name: '', author: '', description: '', cover_url: '', 
    genre: '', publisher: '', volume: 1, price: 0, retail_stock: 1 
  };
  scanError.value = '';
  isScanModalOpen.value = true;
  if (initialIsbn) {
    lookupMetadataByIsbn();
  }
};

const extractTitleAndVolume = (rawTitle: string) => {
  const cleaned = rawTitle.trim();
  const volumeMatch = cleaned.match(/(?:\b(?:t\.?|tap|tập|vol(?:ume)?\.?)[\s#:.-]*)(\d{1,4})/i);
  if (!volumeMatch) return { title: cleaned, volume: 1 };
  const volume = Number(volumeMatch[1]) || 1;
  const title = cleaned.replace(volumeMatch[0], "").replace(/[-:()\s]+$/g, "").trim();
  return { title: title || cleaned, volume };
};

const lookupMetadataByIsbn = async () => {
  const isbn = scanForm.value.isbn.replace(/[^0-9Xx]/g, "").toUpperCase();
  if (isbn.length < 10) {
    scanError.value = "ISBN quá ngắn để tra metadata.";
    return;
  }
  isScanning.value = true;
  scanError.value = "Đang tra cứu từ backend...";
  try {
    const response = await autofillTitleMetadata({
      isbn,
      request_id: buildRequestId("scan-metadata"),
    });
    const parsed = extractTitleAndVolume(response.metadata.name);
    scanForm.value.name = parsed.title;
    scanForm.value.volume = parsed.volume;
    scanForm.value.author = response.metadata.author;
    scanForm.value.genre = response.metadata.genre;
    scanForm.value.description = response.metadata.description;
    scanForm.value.publisher = response.metadata.publisher;

    if (response.metadata.cover_url && /^https?:\/\//i.test(response.metadata.cover_url)) {
      scanError.value = "Đạng tải ảnh bìa...";
      try {
        const coverPayload = await importCoverImage({
          isbn,
          image_url: response.metadata.cover_url,
          request_id: buildRequestId("import-cover")
        });
        scanForm.value.cover_url = coverPayload.cover_url;
      } catch (e: any) {}
    }
    scanError.value = "Thành công!";
  } catch (error: unknown) {
    scanError.value = "Không tìm thấy thông tin tự động, vui lòng nhập tay.";
  } finally {
    isScanning.value = false;
  }
};

const saveScannedVolume = async () => {
   isScanning.value = true;
   try {
     await apiCreateVolume(
       {
         title_name: scanForm.value.name || "Unknown Title",
         author: scanForm.value.author || "Unknown",
         volume_number: scanForm.value.volume || 1,
         isbn: scanForm.value.isbn,
         retail_stock: scanForm.value.retail_stock || 1,
         p_sell_new: scanForm.value.price || 0,
         description: scanForm.value.description || '',
         cover_url: scanForm.value.cover_url || null,
         categories: scanForm.value.genre ? scanForm.value.genre.split(',').map(s => s.trim()) : [],
         published_date: null,
         request_id: buildRequestId('add-volume-scan'),
       },
       token.value,
     );
     addNotification('success', 'Đã lưu truyện quét mã thành công!');
     isScanModalOpen.value = false;
     await loadTitles();
   } catch(e: any) {
     scanError.value = e?.message || 'Lỗi lưu thông tin';
   } finally {
     isScanning.value = false;
   }
};

// ─── API data & loading ───────────────────────────────────────────────────────
const isLoading = ref(false);
const apiError = ref('');
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
      image: (() => {
        if (!title.cover_url) return 'https://via.placeholder.com/50x70';
        if (title.cover_url.startsWith('http')) return title.cover_url;
        return `${API_BASE_URL}${title.cover_url}`;
      })(),
      _raw: title,
      volumes: title.volumes.map(vol => ({
        id: vol.id,
        code: vol.isbn ?? `VOL-${vol.id}`,
        name: title.name,
        volume: String(vol.volume_number),
        isbn: vol.isbn ?? '',
        so_luong: vol.retail_stock,
       rental_item_count: vol.rental_item_count,
        retail_stock: vol.retail_stock,
        price: vol.p_sell_new,
        rent_price: vol.price_rental,
        deposit: vol.price_deposit,
        items: vol.items.filter(it => it.status === 'available' || it.status === 'maintenance').map(it => ({
          id: it.id,
          volume: String(vol.volume_number),
          status: it.status,
          item_type: it.item_type || 'rental',
          type_label: it.item_type === 'retail' ? 'Sách Bán' : 'Sách Thuê',
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

onMounted(() => {
  loadTitles();
  stopScannerWatch = watch(
    () => scannerStore.scanEventCounter,
    () => {
      const scanned = scannerStore.lastScannedCode;
      if (!scanned) return;
      if (scanned.toUpperCase().startsWith('RNT-')) {
        scannerStore.lastScannedCode = '';
        return;
      }
      openScanModal(scanned);
      scannerStore.lastScannedCode = '';
    },
    { immediate: true }
  );
});
onBeforeUnmount(() => {
  if (stopScannerWatch) stopScannerWatch();
});

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

const openRestockVolume = (vol: any) => {
  restockVolume.value = vol;
  restockQuantity.value = 1;
  isRestockModalOpen.value = true;
};

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
       await apiUpdateTitle(formBook.value.id, payload, token.value);
       addNotification('success', 'Đã cập nhật Truyện!');
    } else {
       await apiCreateTitle(payload, token.value);
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
      await apiDeleteTitle(id, token.value);
      addNotification('success', 'Đã xóa đầu truyện thành công!');
      await loadTitles();
    } catch(err: any) {
      addNotification('error', 'Lỗi: ' + err.message);
    }
  }
};

const saveRestock = async () => {
  if (!restockVolume.value || !selectedBook.value) return;
  try {
    await apiCreateVolume(
      {
        title_name: selectedBook.value.name,
        author: selectedBook.value.author ?? '',
        volume_number: restockVolume.value.volume_number,
        isbn: restockVolume.value.isbn,
        retail_stock: restockQuantity.value,
        p_sell_new: restockVolume.value.price,
        description: selectedBook.value.description || '',
        cover_url: null,
        categories: selectedBook.value.genre ? [selectedBook.value.genre] : [],
        page_count: null,
        published_date: null,
        request_id: buildRequestId('restock-volume'),
      },
      token.value,
    );
    addNotification('success', `Đã bổ sung ${restockQuantity.value} bản cho tập ${restockVolume.value.volume_number}`);
    isRestockModalOpen.value = false;
    await loadTitles();
    const updatedBook = books.value.find(b => b.id === selectedBook.value?.id);
    if (updatedBook) selectedBook.value = updatedBook;
  } catch(e: any) {
    addNotification('error', e?.message ?? 'Bổ sung thất bại');
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
        }, token.value);
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
  if(!selectedVolume.value) return;
  const defaultType = selectedVolume.value.retail_stock > 0 ? 'retail' : 'rental';
  formItem.value = { id: '', status: 'Có sẵn', condition: 'Mới', note: '', item_type: defaultType };
  isAddItemModalOpen.value = true;
};
const openEditItem = (item: any) => {
  if(!selectedVolume.value) return;
  formItem.value = { id: item.id, status: item.status, condition: item.condition, note: item.note, item_type: item.item_type };
  isEditItemModalOpen.value = true;
};

const convertItemToRental = async (item: any) => {
  if (!confirm(`Bạn chắc chắn muốn chuyển bản sao ${item.id} thành sách thuê?`)) return;
  try {
    await apiUpdateItem(item.id, {
      status: 'available',
      condition_level: 100,
      item_type: 'rental',
      notes: item.note,
    }, token.value);
    addNotification('success', `Đã chuyển ${item.id} sang sách thuê.`);
    await loadTitles();
    if(selectedBook.value) {
        selectedBook.value = books.value.find(b => b.id === selectedBook.value.id) || null;
        if(selectedVolume.value) {
            selectedVolume.value = selectedBook.value?.volumes.find((v:any) => v.id === selectedVolume.value.id) || null;
        }
    }
  } catch(e:any) {
    addNotification('error', e?.message || 'Lỗi chuyển đổi.');
  }
};

const saveItem = async () => {
  try {
    const payload = {
      status: reverseStatusMap[formItem.value.status] || formItem.value.status,
      item_type: formItem.value.item_type,
      condition_level: formItem.value.condition === 'Mới' ? 100 : formItem.value.condition === 'Tốt' ? 80 : formItem.value.condition === 'Trung bình' ? 50 : 20,
      notes: formItem.value.note,
    };
    if (isEditItemModalOpen.value) {
       await apiUpdateItem(formItem.value.id, payload, token.value);
       addNotification('success', 'Cập nhật bản sao thành công!');
    } else {
       await apiCreateItem({ ...payload, volume_id: selectedVolume.value.id, id: null, version_no: 1 }, token.value);
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
       await apiDeleteItem(itemId, token.value);
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
  'rented': 'Đang thuê',
  'maintenance': 'Bảo trì',
  'lost': 'Bị mất',
  'damaged': 'Hư hỏng',
  'sold': 'Đã bán'
};
const reverseStatusMap: Record<string, string> = {
  'Có sẵn': 'available',
  'Đã thuê': 'rented',
  'Bảo trì': 'maintenance'
};
const getStatusText = (status: string): string => statusMap[status] || status;
const formatVND = (val: number) => {
  if (typeof val !== 'number') return '—';
  return val.toLocaleString('vi-VN') + 'đ';
};
</script>

<template>
  <DefaultLayout>
    <div class="manager-container">
      <!-- Loading overlay -->
      <div v-if="isLoading" class="loading-overlay">
        <div class="spinner"></div>
        <span>Đang tải dữ liệu...</span>
      </div>

      <!-- Header Card -->
      <div class="header-card">
        <div class="header-left">
          <h1 class="page-title">📚 Quản lý đầu truyện</h1>
          <p class="page-subtitle">Danh mục sách, tập, bản sao và chuyển đổi kho</p>
        </div>
        <div class="header-actions">
          <div class="search-group">
            <input v-model="searchQuery" type="text" placeholder="🔍 Tìm kiếm truyện, ISBN..." class="search-input" />
          </div>
          <div class="filters">
            <select v-model="filterAuthor" class="filter-select"><option value="">Tác giả</option><option v-for="a in authors" :key="a" :value="a">{{ a }}</option></select>
            <select v-model="filterGenre" class="filter-select"><option value="">Thể loại</option><option v-for="g in genres" :key="g" :value="g">{{ g }}</option></select>
            <select v-model="filterPublisher" class="filter-select"><option value="">Nhà xuất bản</option><option v-for="p in publishers" :key="p" :value="p">{{ p }}</option></select>
          </div>
          <div class="action-buttons">
            <button class="btn-icon" @click="() => loadTitles()" title="Làm mới"><span class="material-icons">refresh</span></button>
            <button class="btn-primary" @click="openAddBook"><span class="material-icons">library_add</span> Đầu truyện mới</button>
            <button class="btn-secondary" @click="openScanModal()"><span class="material-icons">qr_code_scanner</span> Quét ISBN</button>
          </div>
        </div>
      </div>

      <!-- Books Grid -->
      <div class="books-grid">
        <div v-for="book in filteredBooks" :key="book.id" class="book-card" @click="openVolumeModal(book)">
          <div class="book-cover"><img :src="book.image" :alt="book.name" /></div>
          <div class="book-info">
            <div class="book-title">{{ book.name }}</div>
            <div class="book-meta"><span class="badge-author">✍️ {{ book.author || '?' }}</span><span class="badge-genre">{{ book.genre || 'Chưa phân loại' }}</span></div>
            <div class="book-publisher">{{ book.publisher }}</div>
            <div class="book-code">Mã: {{ book.code }}</div>
            <div class="book-desc">{{ book.description.slice(0, 80) }}...</div>
          </div>
          <div class="book-actions" @click.stop>
            <button class="icon-btn edit" @click="openEditBook(book)"><span class="material-icons">edit</span></button>
            <button class="icon-btn delete" @click="deleteBook(book.id)"><span class="material-icons">delete</span></button>
          </div>
        </div>
        <div v-if="filteredBooks.length === 0" class="empty-state"><span class="material-icons">book_stack</span><p>Không tìm thấy đầu truyện nào.</p></div>
      </div>

      <!-- MODAL: Volumes -->
      <BaseModal :is-open="isModalOpen" :title="selectedBook?.name" @close="isModalOpen = false" custom-class="modal-large">
        <div class="volume-table-wrapper">
          <table class="volume-table">
            <thead><tr><th>Tập</th><th>ISBN</th><th>Giá bán</th><th>Giá thuê</th><th>Tồn kho</th><th>Số lượng thuê</th></tr></thead>
            <tbody>
              <tr v-for="vol in selectedBook?.volumes" :key="vol.id" @click="openItemsModal(vol)">
                <td>Tập {{ vol.volume }}</td><td>{{ vol.isbn || '—' }}</td><td>{{ formatVND(vol.price) }}</td><td>{{ formatVND(vol.rent_price) }}</td><td>{{ vol.so_luong }}</td><td>{{ vol.rental_item_count }}</td>
                <td class="actions" @click.stop>
                  <button class="icon-small restock" @click="openRestockVolume(vol)" title="Bổ sung"><span class="material-icons">add_box</span></button>
                  <button class="icon-small edit" @click="openEditVolume(vol)"><span class="material-icons">edit</span></button>
                  <button class="icon-small delete" @click="deleteVolume(selectedBook, vol.id)"><span class="material-icons">delete</span></button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <template #footer><button class="btn-secondary" @click="isModalOpen = false">Đóng</button><button class="btn-primary" @click="openAddVolume">+ Thêm tập mới</button></template>
      </BaseModal>

      <!-- MODAL: Items -->
      <BaseModal :is-open="isItemsModalOpen" :title="`${selectedBook?.name} - Tập ${selectedVolume?.volume}`" @close="isItemsModalOpen = false" custom-class="modal-extra-large">
        <div class="items-table-wrapper">
          <table class="items-table">
            <thead><tr><th>Mã vạch</th><th>Loại</th><th>Trạng thái</th><th>Tình trạng</th><th>Ghi chú</th><th>Phiên bản</th><th></th></tr></thead>
            <tbody>
              <tr v-for="it in selectedVolume?.items" :key="it.id">
                <td class="code-cell">{{ it.id }}</td>
                <td><span :class="['type-badge', it.item_type === 'retail' ? 'retail' : 'rental']">{{ it.type_label }}</span></td>
                <td>{{ getStatusText(it.status) }}</td><td>{{ it.condition }}</td><td>{{ it.note || '—' }}</td><td>{{ it.version }}</td>
                <td class="actions">
                  <button class="icon-small edit" @click="openEditItem(it)"><span class="material-icons">edit</span></button>
                  <button class="icon-small delete" @click="deleteItem(selectedVolume, it.id)"><span class="material-icons">delete</span></button>
                  <button v-if="it.item_type === 'retail'" class="icon-small convert" @click="convertItemToRental(it)" title="Chuyển thuê"><span class="material-icons">sync_alt</span></button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <template #footer>
          <button class="btn-secondary" @click="isItemsModalOpen = false">Đóng</button>
          <button class="btn-primary" @click="openConvertRental" v-if="selectedVolume?.retail_stock > 0">Chuyển thuê (tồn: {{ selectedVolume?.retail_stock }})</button>
          <button class="btn-primary" @click="openAddItem">+ Thêm bản sao mới</button>
        </template>
      </BaseModal>

      <!-- MODAL: Book (Add/Edit) -->
      <BaseModal :is-open="isAddBookModalOpen || isEditBookModalOpen" :title="isEditBookModalOpen ? 'Sửa thông tin truyện' : 'Thêm truyện mới'" @close="isAddBookModalOpen = false; isEditBookModalOpen = false">
        <div class="form-grid">
          <div class="form-group"><label>Mã truyện</label><input v-model="formBook.code" type="text" placeholder="TR001" /></div>
          <div class="form-group"><label>Tên truyện *</label><input v-model="formBook.name" type="text" placeholder="Nhập tên truyện..." /></div>
          <div class="form-group"><label>Tác giả</label><input v-model="formBook.author" type="text" placeholder="Nhập tên tác giả..." /></div>
          <div class="form-group"><label>Thể loại</label><input v-model="formBook.genre" type="text" placeholder="Shonen, Drama..." /></div>
          <div class="form-group"><label>Nhà xuất bản</label><input v-model="formBook.publisher" type="text" placeholder="Nhập tên NXB..." /></div>
          <div class="form-group full-width"><label>Mô tả</label><textarea v-model="formBook.description" rows="3"></textarea></div>
        </div>
        <template #footer><button class="btn-secondary" @click="isAddBookModalOpen = false; isEditBookModalOpen = false">Hủy</button><button class="btn-primary" @click="saveBook">{{ isEditBookModalOpen ? 'Cập nhật' : 'Thêm mới' }}</button></template>
      </BaseModal>

      <!-- MODAL: Volume (Add/Edit) -->
      <BaseModal :is-open="isAddVolumeModalOpen || isEditVolumeModalOpen" :title="isEditVolumeModalOpen ? 'Sửa tập truyện' : 'Thêm tập mới'" @close="isAddVolumeModalOpen = false; isEditVolumeModalOpen = false">
        <div class="form-grid">
          <div class="form-group"><label>ISBN</label><input v-model="formVolume.isbn" type="text" placeholder="978-..." /></div>
          <div class="form-group"><label>Tập số</label><input v-model="formVolume.volume" type="text" placeholder="105" /></div>
          <div class="form-group"><label>Số lượng</label><input v-model="formVolume.so_luong" type="number" /></div>
          <div class="form-group"><label>Giá bán (VND)</label><input v-model="formVolume.price" type="text" placeholder="20.000đ" /></div>
          <div class="form-group"><label>Giá thuê (VND/ngày)</label><input v-model="formVolume.rent_price" type="text" placeholder="5.000đ" /></div>
        </div>
        <template #footer><button class="btn-secondary" @click="isAddVolumeModalOpen = false; isEditVolumeModalOpen = false">Hủy</button><button class="btn-primary" @click="saveVolume">{{ isEditVolumeModalOpen ? 'Cập nhật' : 'Thêm mới' }}</button></template>
      </BaseModal>

      <!-- MODAL: Item (Add/Edit) -->
      <BaseModal :is-open="isAddItemModalOpen || isEditItemModalOpen" :title="isEditItemModalOpen ? 'Sửa bản sao' : 'Thêm bản sao mới'" @close="isAddItemModalOpen = false; isEditItemModalOpen = false">
        <div class="form-grid">
          <div class="form-group" v-if="isEditItemModalOpen"><label>Mã vạch</label><input v-model="formItem.id" type="text" disabled /></div>
          <div class="form-group"><label>Loại hàng</label><select v-model="formItem.item_type"><option value="rental">Sách Thuê</option><option value="retail">Sách Bán</option></select></div>
          <div class="form-group"><label>Trạng thái</label><select v-model="formItem.status"><option>Có sẵn</option><option>Đã thuê</option><option>Bảo trì</option></select></div>
          <div class="form-group"><label>Tình trạng</label><input v-model="formItem.condition" type="text" placeholder="Mới, Cũ..." /></div>
          <div class="form-group full-width"><label>Ghi chú</label><input v-model="formItem.note" type="text" /></div>
        </div>
        <template #footer><button class="btn-secondary" @click="isAddItemModalOpen = false; isEditItemModalOpen = false">Hủy</button><button class="btn-primary" @click="saveItem">{{ isEditItemModalOpen ? 'Cập nhật' : 'Thêm mới' }}</button></template>
      </BaseModal>

      <!-- MODAL: Convert to Rental -->
      <BaseModal :is-open="isConvertRentalModalOpen" title="Chuyển sang truyện thuê" @close="isConvertRentalModalOpen = false">
        <div class="form-grid"><div class="form-group full-width"><label>Số lượng muốn chuyển từ kho bán</label><input v-model.number="formConvert.quantity" type="number" min="1" :max="selectedVolume?.retail_stock" /><small class="hint">Hành động này sẽ trừ hàng tồn bán và tạo mã vạch bản sao mới.</small></div></div>
        <template #footer><button class="btn-secondary" @click="isConvertRentalModalOpen = false">Hủy</button><button class="btn-primary" @click="saveConvertRental">Xác nhận chuyển</button></template>
      </BaseModal>

      <!-- MODAL: Scan ISBN -->
      <BaseModal :is-open="isScanModalOpen" title="Nhập nhanh qua ISBN" @close="isScanModalOpen = false">
        <div class="form-grid">
          <div class="form-group full-width"><label>Mã ISBN</label><div class="isbn-input-group"><input v-model="scanForm.isbn" type="text" placeholder="Quét hoặc nhập ISBN" @keydown.enter="lookupMetadataByIsbn" /><button class="btn-secondary" @click="lookupMetadataByIsbn" :disabled="isScanning">Tra cứu</button></div><small :class="['scan-status', { success: scanError.includes('Thành công'), error: scanError.includes('lỗi') || scanError.includes('Không') }]">{{ scanError }}</small></div>
          <div class="form-group"><label>Tên truyện</label><input v-model="scanForm.name" type="text" /></div>
          <div class="form-group"><label>Tập số</label><input v-model.number="scanForm.volume" type="number" min="1" /></div>
          <div class="form-group"><label>Tác giả</label><input v-model="scanForm.author" type="text" /></div>
          <div class="form-group"><label>Thể loại</label><input v-model="scanForm.genre" type="text" /></div>
          <div class="form-group"><label>Giá bán mới</label><input v-model.number="scanForm.price" type="number" step="1000" min="0" /></div>
          <div class="form-group"><label>Số lượng kho bán</label><input v-model.number="scanForm.retail_stock" type="number" min="1" /></div>
          <div class="form-group full-width" v-if="scanForm.cover_url"><img :src="scanForm.cover_url && !scanForm.cover_url.startsWith('http') ? `${API_BASE_URL}${scanForm.cover_url}` : scanForm.cover_url" class="cover-preview" /></div>
        </div>
        <template #footer><button class="btn-secondary" @click="isScanModalOpen = false">Hủy</button><button class="btn-primary" @click="saveScannedVolume" :disabled="isScanning || !scanForm.isbn || !scanForm.name">Lưu vào kho</button></template>
      </BaseModal>

      <!-- MODAL: Restock -->
      <BaseModal :is-open="isRestockModalOpen" title="Bổ sung tồn kho" @close="isRestockModalOpen = false">
        <div class="form-grid"><div class="form-group full-width"><label>Số lượng bổ sung</label><input v-model.number="restockQuantity" type="number" min="1" /><small class="hint">Số sách bán thêm vào kho.</small></div></div>
        <template #footer><button class="btn-secondary" @click="isRestockModalOpen = false">Hủy</button><button class="btn-primary" @click="saveRestock">Xác nhận</button></template>
      </BaseModal>
    </div>
  </DefaultLayout>
</template>

<style scoped>
/* ----- RESET & CONTAINER ----- */
.manager-container {
  padding: 20px 24px;
  background: #f8fafc;
  min-height: 100vh;
  font-family: 'Inter', system-ui, -apple-system, sans-serif;
}
.loading-overlay {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(255,255,255,0.8);
  backdrop-filter: blur(4px);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  z-index: 1000;
  font-weight: 600;
  color: #1e293b;
}
.spinner {
  width: 40px; height: 40px;
  border: 4px solid #e2e8f0;
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* ----- HEADER CARD ----- */
.header-card {
  background: white;
  border-radius: 28px;
  padding: 20px 28px;
  margin-bottom: 32px;
  border: 1px solid #eef2f6;
  box-shadow: 0 4px 12px rgba(0,0,0,0.02);
}
.header-left { margin-bottom: 16px; }
.page-title { font-size: 1.9rem; font-weight: 700; color: #0f172a; margin: 0 0 4px; }
.page-subtitle { color: #5b6e8c; margin: 0; font-size: 0.9rem; }
.header-actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}
.search-group { flex: 2; min-width: 240px; }
.search-input {
  width: 100%;
  padding: 12px 16px;
  border: 1px solid #e2e8f0;
  border-radius: 40px;
  font-size: 0.9rem;
  background: #fefefe;
  transition: 0.2s;
}
.search-input:focus { outline: none; border-color: #3b82f6; box-shadow: 0 0 0 3px rgba(59,130,246,0.1); }
.filters { display: flex; gap: 12px; flex-wrap: wrap; }
.filter-select {
  padding: 10px 14px;
  border: 1px solid #e2e8f0;
  border-radius: 40px;
  background: white;
  font-size: 0.85rem;
  cursor: pointer;
}
.action-buttons { display: flex; gap: 12px; }
.btn-icon {
  background: #f1f5f9;
  border: none;
  border-radius: 40px;
  width: 46px;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  transition: 0.2s;
}
.btn-icon:hover { background: #e2e8f0; }
.btn-primary, .btn-secondary {
  border: none;
  border-radius: 40px;
  padding: 10px 20px;
  font-weight: 600;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  transition: 0.2s;
}
.btn-primary { background: #3b82f6; color: white; box-shadow: 0 2px 4px rgba(59,130,246,0.2); }
.btn-secondary { background: white; border: 1px solid #cbd5e1; color: #334155; }
.btn-primary:hover, .btn-secondary:hover { opacity: 0.9; transform: translateY(-1px); }

/* ----- BOOKS GRID ----- */
.books-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  gap: 24px;
}
.book-card {
  background: white;
  border-radius: 20px;
  border: 1px solid #eef2f8;
  padding: 16px;
  display: flex;
  gap: 16px;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 2px 5px rgba(0,0,0,0.02);
}
.book-card:hover { transform: translateY(-4px); box-shadow: 0 16px 28px -12px rgba(0,0,0,0.12); border-color: #d9e2ef; }
.book-cover { flex-shrink: 0; width: 85px; height: 120px; border-radius: 12px; overflow: hidden; background: #f8fafc; }
.book-cover img { width: 100%; height: 100%; object-fit: cover; }
.book-info { flex: 1; }
.book-title { font-weight: 700; font-size: 1.1rem; color: #0f172a; margin-bottom: 6px; }
.book-meta { display: flex; gap: 12px; margin-bottom: 6px; font-size: 0.75rem; }
.badge-author, .badge-genre { background: #f1f5f9; padding: 2px 10px; border-radius: 40px; color: #334155; }
.book-publisher { font-size: 0.8rem; color: #5b6e8c; margin-bottom: 4px; }
.book-code { font-family: monospace; font-size: 0.7rem; color: #3b82f6; margin-bottom: 8px; }
.book-desc { font-size: 0.8rem; color: #475569; line-height: 1.4; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.book-actions { display: flex; flex-direction: column; gap: 8px; justify-content: flex-start; }
.icon-btn { background: none; border: none; cursor: pointer; font-size: 1.2rem; padding: 6px; border-radius: 12px; }
.icon-btn.edit:hover { background: #e0f2fe; color: #0284c7; }
.icon-btn.delete:hover { background: #fee2e2; color: #dc2626; }
.empty-state { grid-column: 1/-1; text-align: center; padding: 60px 20px; color: #94a3b8; background: white; border-radius: 32px; }

/* ----- TABLES (Volume & Items) ----- */
.volume-table-wrapper, .items-table-wrapper { overflow-x: auto; width: 100%; }
.volume-table, .items-table { width: 100%; border-collapse: collapse; font-size: 0.85rem; min-width: 600px; }
.volume-table th, .items-table th { text-align: left; padding: 12px 8px; background: #f8fafc; color: #475569; font-weight: 600; }
.volume-table td, .items-table td { padding: 12px 8px; border-bottom: 1px solid #eef2f8; }
.actions { display: flex; gap: 6px; justify-content: flex-end; }
.icon-small {
  background: none; border: none; cursor: pointer; padding: 4px; border-radius: 8px;
  display: inline-flex; font-size: 1.1rem;
}
.icon-small.edit:hover { background: #e0f2fe; }
.icon-small.delete:hover { background: #fee2e2; }
.icon-small.restock:hover { background: #dcfce7; }
.icon-small.convert:hover { background: #fef3c7; }
.type-badge { display: inline-block; padding: 4px 10px; border-radius: 30px; font-size: 0.7rem; font-weight: 600; }
.type-badge.retail { background: #dbeafe; color: #1e40af; }
.type-badge.rental { background: #fef3c7; color: #b45309; }
.code-cell { font-family: monospace; font-weight: 500; }

/* ----- FORMS ----- */
.form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
.form-group.full-width { grid-column: span 2; }
.form-group label { display: block; font-weight: 600; font-size: 0.8rem; color: #334155; margin-bottom: 6px; }
.form-group input, .form-group textarea, .form-group select {
  width: 100%; padding: 10px 12px; border: 1px solid #e2e8f0; border-radius: 14px;
  font-family: inherit; background: white;
}
.isbn-input-group { display: flex; gap: 10px; }
.scan-status.success { color: #15803d; }
.scan-status.error { color: #b91c1c; }
.hint { display: block; font-size: 0.7rem; color: #6c757d; margin-top: 4px; }
.cover-preview { max-width: 120px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }

/* ----- RESPONSIVE ----- */
@media (max-width: 768px) {
  .manager-container { padding: 16px; }
  .header-card { padding: 16px; }
  .header-actions { flex-direction: column; align-items: stretch; }
  .filters { justify-content: space-between; }
  .action-buttons { justify-content: flex-end; }
  .books-grid { grid-template-columns: 1fr; }
  .book-card { flex-direction: column; align-items: center; text-align: center; }
  .book-cover { width: 120px; height: 160px; }
  .book-actions { flex-direction: row; justify-content: center; }
  .form-grid { grid-template-columns: 1fr; }
  .form-group.full-width { grid-column: span 1; }
}
.modal-large :deep(.modal-content) { width: 720px; max-width: 90vw; }
.modal-extra-large :deep(.modal-content) { width: 1100px; max-width: 95vw; }
@media (max-width: 640px) {
  .modal-large :deep(.modal-content), .modal-extra-large :deep(.modal-content) { width: 95vw; }
}
</style>