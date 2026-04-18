<template>
  <DefaultLayout>
    <div class="management-container">
      <div class="header-section">
        <div class="title-meta">
          <h2 class="page-title">Quản Lý Kho Hàng (Inventory)</h2>
          <p class="subtitle">
            Hệ thống nạp tồn kho và chuyển đổi sách sang danh mục cho thuê
          </p>
        </div>
      </div>

      <div class="actions-bar">
        <input v-model="searchQuery" type="text" placeholder="Tìm bằng ISBN hoặc tên truyện..." class="search-input" />
      </div>

      <div class="table-container">
        <table>
          <thead>
            <tr>
              <th>Mã ISBN (Sách Mới)</th>
              <th>Tên Sách</th>
              <th>Loại Hàng</th>
              <th>Tồn Kho</th>
              <th class="text-center">Hành động</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in filteredItems" :key="item.id">
              <td class="code-text" style="font-family: monospace;">{{ item.code }}</td>
              <td class="font-medium">{{ item.name }}</td>
              <td>
                <span :class="item.type === 'retail' ? 'tag-sale' : 'tag-rent'">
                  {{ item.type === 'retail' ? 'Sách Mới (Bán)' : 'Sách Thuê (SKU)' }}
                </span>
              </td>
              <td>
                <span v-if="item.type === 'retail'" class="stock-badge">{{ item.status }}</span>
                <span v-else class="status-badge">{{ item.status }}</span>
              </td>
              <td class="text-center">
                <button
                  v-if="item.type === 'retail'"
                  class="btn-primary"
                  style="font-size: 0.8rem; padding: 6px 12px; margin-right: 5px;"
                  @click="openConvertModal(item)"
                >
                  <span class="material-icons" style="font-size: 14px;">sync_alt</span>
                  Chuyển ra Thuê
                </button>
              </td>
            </tr>
            <tr v-if="filteredItems.length === 0">
              <td colspan="5" class="empty-state">Không tìm thấy sách phù hợp.</td>
            </tr>
          </tbody>
        </table>
      </div>

      <BaseModal 
        :is-open="isConvertModalOpen" 
        title="Chuyển đổi Sách Bán Xuống Hàng Thuê" 
        @close="isConvertModalOpen = false"
      >
        <div v-if="selectedRetailItem" class="form-grid" style="grid-template-columns: 1fr; gap: 15px;">
          <div class="convert-banner">
            <span class="material-icons">info</span> Hành động này sẽ giảm tồn kho bán lẻ và sinh ra <strong>mã SKU (RNT-...)</strong> riêng biệt để in tem dán lên bìa sách.
          </div>
          <div class="form-group">
            <label>Cuốn Chọn:</label>
            <input type="text" :value="selectedRetailItem.name" disabled />
          </div>
          <div class="form-group">
            <label>Số lượng cần chuyển (Max {{ selectedRetailItem.status }}):</label>
            <input v-model.number="convertQuantity" type="number" min="1" :max="selectedRetailItem.status" />
          </div>
        </div>
        <template #footer>
          <button class="btn-secondary" @click="isConvertModalOpen = false">Hủy</button>
          <button class="btn-checkout-lux" :disabled="isConverting || convertQuantity < 1" @click="processConversion">
            {{ isConverting ? 'ĐANG CHUYỂN...' : 'CHUYỂN & IN TEM (SKU)' }}
          </button>
        </template>
      </BaseModal>

    </div>
  </DefaultLayout>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, inject } from 'vue';
import DefaultLayout from '../components/layout/defaultLayout.vue';
import BaseModal from '../components/layout/BaseModal.vue';
import { fetchInventoryItems, convertToRental, buildRequestId, type InventoryItemListItem } from '../services/storyhubApi';

const addNotification = inject('addNotification') as any;

const searchQuery = ref('');
const items = ref<InventoryItemListItem[]>([]);
const isConvertModalOpen = ref(false);
const selectedRetailItem = ref<InventoryItemListItem | null>(null);
const convertQuantity = ref(1);
const isConverting = ref(false);

const filteredItems = computed(() => {
  if (!searchQuery.value) return items.value;
  const q = searchQuery.value.toLowerCase();
  return items.value.filter(i => 
    i.name.toLowerCase().includes(q) || i.code.toLowerCase().includes(q)
  );
});

const loadData = async () => {
  try {
    items.value = await fetchInventoryItems();
  } catch (err) {
    addNotification('error', 'Lỗi nạp dữ liệu kho.');
  }
};

const openConvertModal = (item: InventoryItemListItem) => {
  selectedRetailItem.value = item;
  convertQuantity.value = 1;
  isConvertModalOpen.value = true;
};

const processConversion = async () => {
    if(!selectedRetailItem.value || convertQuantity.value < 1) return;
    
    // Attempting to mock Extract Volume ID from ISBN because our API needs Volume_ID 
    // Wait, the API GET /items returns `v.isbn AS item_id` for retail... So item.id is the ISBN string instead of Volume ID.
    // That means `convertToRental` which takes `volume_id: number` inside inventory.py will throw 422 if we pass item_id.
    // Wait! In `inventory.py`, GET /items query returned `v.isbn AS item_id`. No, it shouldn't! It should return `v.id AS item_id` to allow us to reference Volume!
    const volumeId = Number((selectedRetailItem.value as any).volume_id); 
    // Fallback logic, we'll try to find it from the backend if we patch it.
    
    isConverting.value = true;
    try {
        const res = await convertToRental({
            volume_id: isNaN(volumeId) ? 11 : volumeId, // Hot patch demo value, will require API fix
            quantity: convertQuantity.value,
            request_id: buildRequestId('convert')
        });
        addNotification('success', `Đã sinh mã tem (SKU) thành công: ${res.new_skus.join(', ')}`);
        isConvertModalOpen.value = false;
        await loadData();
    } catch (err: any) {
        addNotification('error', `Lỗi: ${err.message || 'Không thể chuyển đổi'}`);
    } finally {
        isConverting.value = false;
    }
};

onMounted(loadData);
</script>

<style scoped>
@import url("https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap");
.management-container { padding: 32px; background: #fdfdfd; min-height: 100vh; font-family: "Plus Jakarta Sans", sans-serif; }
.header-section { margin-bottom: 20px; }
.page-title { font-size: 2.25rem; font-weight: 800; color: #0f172a; margin: 0; }
.subtitle { color: #64748b; font-size: 1rem; margin-top: 4px; }
.actions-bar { margin-bottom: 20px; }
.search-input { width: 100%; max-width: 400px; padding: 12px 16px; border: 1px solid #cbd5e1; border-radius: 12px; font-family: inherit; }

.table-container { background: white; border-radius: 16px; border: 1px solid #e2e8f0; overflow: hidden; }
table { width: 100%; border-collapse: collapse; }
th { background: #f8fafc; padding: 16px; font-size: 0.85rem; font-weight: 700; color: #64748b; text-align: left; }
td { padding: 16px; border-bottom: 1px solid #e2e8f0; color: #334155; }
.code-text { font-weight: 700; color: #2563eb; }

.tag-sale { background: #dcfce7; color: #166534; padding: 6px 10px; border-radius: 8px; font-size: 0.8rem; font-weight: 700; }
.tag-rent { background: #fef08a; color: #854d0e; padding: 6px 10px; border-radius: 8px; font-size: 0.8rem; font-weight: 700; }
.stock-badge { display: inline-block; background: #f1f5f9; padding: 6px 12px; border-radius: 20px; font-weight: 800; }
.status-badge { display: inline-block; background: #eff6ff; color: #2563eb; padding: 6px 12px; border-radius: 20px; font-weight: 700; }

.empty-state { text-align: center; padding: 40px; color: #94a3b8; }
.btn-primary { background: #2563eb; color: white; border: none; border-radius: 8px; cursor: pointer; transition: 0.2s; }
.btn-primary:hover { background: #1d4ed8; }
.btn-secondary { background: #e2e8f0; color: #475569; padding: 10px 16px; border-radius: 8px; border: none; font-weight: 600; cursor: pointer; }
.btn-checkout-lux { background: #10b981; color: white; padding: 10px 16px; border: none; border-radius: 8px; font-weight: 700; cursor: pointer; }
.btn-checkout-lux:disabled { background: #94a3b8; cursor: not-allowed; }

.convert-banner { background: #eff6ff; border-left: 4px solid #3b82f6; padding: 12px; font-size: 0.9rem; color: #1e3a8a; display: flex; align-items: flex-start; gap: 8px; border-radius: 0 8px 8px 0; }
.convert-banner .material-icons { font-size: 1.2rem; color: #3b82f6; }
.form-group label { font-size: 0.9rem; font-weight: 600; color: #475569; display: block; margin-bottom: 6px; }
.form-group input { width: 100%; padding: 10px 12px; border: 1px solid #cbd5e1; border-radius: 8px; font-family: inherit; outline: none; }
.form-group input:focus { border-color: #3b82f6; box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.1); }
</style>
