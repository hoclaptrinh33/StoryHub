<template>
  <DefaultLayout>
    <div class="inventory-page">
      <header class="header-section">
        <div class="title-meta">
          <h2 class="page-title">Quản Lý Kho (Mode-first Intake)</h2>
          <p class="subtitle">Nhập nhanh theo ISBN, tự điền metadata, và chuyển SKU thuê có preview rõ ràng.</p>
        </div>
      </header>

      <section class="actions-bar">
        <input
          ref="searchInputRef"
          v-model="searchQuery"
          type="text"
          placeholder="Tìm bằng ISBN hoặc tên truyện..."
          class="search-input"
        />
        <div class="action-buttons">
          <button class="btn-primary" @click="openCreateModal('new')">
            <span class="material-icons">library_add</span>
            Nhập sách mới
          </button>
          <button class="btn-secondary" @click="openCreateModal('restock')">
            <span class="material-icons">add_box</span>
            Bổ sung tồn kho
          </button>
        </div>
      </section>

      <section class="inventory-filter-bar">
        <div class="filter-group">
          <span class="filter-group-title">Loại hàng</span>
          <button
            type="button"
            :class="['filter-btn', { active: inventoryTypeFilter === 'all' }]"
            @click="inventoryTypeFilter = 'all'"
          >
            Tất cả hàng
          </button>
          <button
            type="button"
            :class="['filter-btn', { active: inventoryTypeFilter === 'rental' }]"
            @click="inventoryTypeFilter = 'rental'"
          >
            Chỉ hàng thuê
          </button>
          <button
            type="button"
            :class="['filter-btn', { active: inventoryTypeFilter === 'retail' }]"
            @click="inventoryTypeFilter = 'retail'"
          >
            Chỉ hàng bán
          </button>
        </div>

        <div class="filter-group">
          <span class="filter-group-title">Trạng thái</span>
          <button
            v-for="option in inventoryStatusFilterOptions"
            :key="option.value"
            type="button"
            :class="['filter-btn', 'compact', { active: inventoryStatusFilter === option.value }]"
            @click="inventoryStatusFilter = option.value"
          >
            {{ option.label }}
          </button>
        </div>
      </section>

      <div v-if="isLoading" class="screen-loading-state">
        <span class="material-icons spin">autorenew</span>
        Đang nạp dữ liệu kho...
      </div>

      <div v-else class="table-container">
        <table>
          <thead>
            <tr>
              <th>Mã ISBN / SKU</th>
              <th>Tên Sách</th>
              <th>Loại Hàng</th>
              <th>Giá hiện tại</th>
              <th>Tồn Kho</th>
              <th>Trạng thái</th>
              <th class="text-center">Hành động</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in filteredItems" :key="item.id">
              <td class="code-text">{{ item.code }}</td>
              <td class="font-medium">{{ item.name }}</td>
              <td>
                <span :class="item.type === 'retail' ? 'tag-sale' : 'tag-rent'">
                  {{ item.type === "retail" ? "Sách mới (Bán)" : "Sách thuê (SKU)" }}
                </span>
              </td>
              <td class="price-text">{{ formatCurrency(item.price) }}</td>
              <td class="stock-qty-text">{{ formatStockQuantity(item) }}</td>
              <td>
                <span :class="item.type === 'retail' ? 'stock-badge' : 'status-badge'">{{ formatInventoryStatus(item.status) }}</span>
              </td>
              <td class="text-center">
                <div v-if="item.type === 'retail'" class="row-actions">
                  <button class="btn-inline btn-price" @click="openPriceModal(item)">
                    <span class="material-icons">edit_note</span>
                    Cập nhật giá
                  </button>
                  <button class="btn-inline" :disabled="resolveRetailStock(item) < 1" @click="openConvertModal(item)">
                    <span class="material-icons">sync_alt</span>
                    Chuyển ra Thuê
                  </button>
                </div>
              </td>
            </tr>
            <tr v-if="filteredItems.length === 0">
              <td colspan="7" class="empty-state">Không tìm thấy sách phù hợp.</td>
            </tr>
          </tbody>
        </table>
      </div>

      <BaseModal
        :is-open="isCreateModalOpen"
        :title="intakeMode === 'new' ? 'Nhập Đầu Sách Mới' : 'Bổ Sung Tồn Kho'"
        @close="isCreateModalOpen = false"
      >
        <div class="mode-toggle">
          <button
            type="button"
            :class="['mode-btn', { active: intakeMode === 'new' }]"
            @click="intakeMode = 'new'"
          >
            Nhập mới
          </button>
          <button
            type="button"
            :class="['mode-btn', { active: intakeMode === 'restock' }]"
            @click="intakeMode = 'restock'"
          >
            Bổ sung tồn
          </button>
        </div>

        <div v-if="intakeMode === 'new'" class="form-grid">
          <div class="form-group full-width">
            <label>Mã ISBN (*)</label>
            <div class="isbn-row">
              <input
                ref="isbnInputRef"
                v-model="newVolumeForm.isbn"
                type="text"
                placeholder="Quét hoặc nhập ISBN"
              />
              <button
                type="button"
                class="btn-secondary"
                :disabled="isMetadataLoading"
                @click="lookupMetadataByIsbn(newVolumeForm.isbn)"
              >
                <span class="material-icons">search</span>
                {{ isMetadataLoading ? "Đang tìm..." : "Tra metadata" }}
              </button>
            </div>
            <p :class="['metadata-status', metadataState]">{{ metadataMessage }}</p>
          </div>

          <div class="form-group full-width">
            <label>Ảnh bìa (thủ công)</label>
            <div class="cover-manual-row">
              <button
                type="button"
                class="btn-secondary"
                :disabled="isCoverImporting"
                @click="triggerCoverFileDialog"
              >
                <span class="material-icons">upload_file</span>
                {{ isCoverImporting ? "Đang tải..." : "Browse" }}
              </button>

              <input
                ref="coverFileInputRef"
                class="cover-file-input"
                type="file"
                accept="image/png,image/jpeg,image/webp,image/gif"
                @change="onCoverFileSelected"
              />

              <input
                v-model="manualCoverUrlInput"
                type="text"
                placeholder="Dán link ảnh http/https hoặc data:image/...;base64,..."
              />

              <button
                type="button"
                class="btn-secondary"
                :disabled="isCoverImporting"
                @click="importCoverFromManualLink"
              >
                <span class="material-icons">cloud_download</span>
                Tải link
              </button>
            </div>
            <p v-if="selectedCoverFileName" class="cover-file-name">
              Đã chọn file: {{ selectedCoverFileName }}
            </p>
            <p :class="['cover-import-status', coverImportState]">{{ coverImportMessage }}</p>
          </div>

          <div v-if="newVolumeForm.cover_url" class="cover-preview-wrap">
            <img :src="newVolumeForm.cover_url" alt="Bìa sách" />
          </div>

          <div class="form-group" :class="{ 'full-width': !newVolumeForm.cover_url }">
            <label>Tên truyện (*)</label>
            <input v-model="newVolumeForm.title_name" type="text" placeholder="VD: Conan" />
          </div>

          <div class="form-group">
            <label>Tác giả</label>
            <input v-model="newVolumeForm.author" type="text" placeholder="VD: Gosho Aoyama" />
          </div>

          <div class="form-group full-width">
            <label>Mô tả</label>
            <textarea
              v-model="newVolumeForm.description"
              rows="3"
              placeholder="Mô tả sách từ Google Books"
            ></textarea>
          </div>

          <div class="form-group">
            <label>Thể loại</label>
            <input
              v-model="newVolumeForm.categories"
              type="text"
              placeholder="VD: Truyện tranh, Phiêu lưu"
            />
          </div>

          <div class="form-group">
            <label>Số trang</label>
            <input v-model.number="newVolumeForm.page_count" type="number" min="1" />
          </div>

          <div class="form-group full-width">
            <label>Ngày xuất bản</label>
            <input
              v-model="newVolumeForm.published_date"
              type="text"
              placeholder="VD: 2024-05-11 hoặc 2024-05"
            />
          </div>

          <div class="form-group">
            <label>Tập số (*)</label>
            <input v-model.number="newVolumeForm.volume_number" type="number" min="1" />
          </div>

          <div class="form-group">
            <label>Số lượng nhập (*)</label>
            <input v-model.number="newVolumeForm.retail_stock" type="number" min="1" />
          </div>

          <div class="form-group">
            <label>Giá bán mới (VND)</label>
            <input
              v-model.number="newVolumeForm.p_sell_new"
              type="number"
              min="0"
              step="1000"
              placeholder="0 = Chưa sẵn sàng"
            />
          </div>
        </div>

        <div v-else class="restock-grid">
          <div class="form-group full-width">
            <label>Quét ISBN cần bổ sung</label>
            <input
              ref="restockInputRef"
              v-model="restockForm.isbn"
              type="text"
              placeholder="Quét ISBN đã tồn tại"
            />
          </div>

          <div v-if="matchedRestockItem" class="restock-preview">
            <p><strong>Đã tìm thấy:</strong> {{ matchedRestockItem.name }}</p>
            <p><strong>Mã:</strong> {{ matchedRestockItem.code }}</p>
            <label>
              Số lượng bổ sung
              <input v-model.number="restockForm.quantity" type="number" min="1" />
            </label>
          </div>

          <p v-else class="restock-hint">Chưa tìm thấy đầu sách bán lẻ theo ISBN này.</p>
        </div>

        <template #footer>
          <button class="btn-secondary" @click="isCreateModalOpen = false">Hủy</button>
          <button
            class="btn-primary"
            :disabled="isCreating || isCoverImporting || (intakeMode === 'new' ? !canCreateNew : !canRestock)"
            @click="intakeMode === 'new' ? processCreateVolume() : processRestockVolume()"
          >
            {{ isCreating ? "ĐANG LƯU..." : "LƯU VÀO KHO" }}
          </button>
        </template>
      </BaseModal>

      <BaseModal
        :is-open="isConvertModalOpen"
        title="Preview Chuyển Sang Hàng Thuê"
        @close="isConvertModalOpen = false"
      >
        <div v-if="selectedRetailItem" class="convert-grid">
          <div class="convert-banner">
            <span class="material-icons">preview</span>
            Bạn sắp chuyển item sang kho thuê. Xem kỹ tồn kho và mã tem trước khi xác nhận.
          </div>

          <div class="form-group full-width">
            <label>Cuốn chọn</label>
            <input type="text" :value="selectedRetailItem.name" disabled />
          </div>

          <div class="form-group">
            <label>Số lượng chuyển (max {{ selectedRetailStock }})</label>
            <input v-model.number="convertQuantity" type="number" min="1" :max="selectedRetailStock" />
          </div>

          <div class="convert-preview-box">
            <p>
              <strong>Tồn kho bán:</strong>
              {{ selectedRetailStock }} → {{ Math.max(0, selectedRetailStock - convertQuantity) }}
            </p>
            <p><strong>Mã tem dự kiến:</strong></p>
            <div class="sku-preview-list">
              <span v-for="sku in estimatedSkuList" :key="sku" class="sku-chip">{{ sku }}</span>
            </div>
          </div>
        </div>

        <template #footer>
          <button class="btn-secondary" @click="isConvertModalOpen = false">Hủy</button>
          <button class="btn-primary" :disabled="isConverting || !canConvert" @click="processConversion">
            {{ isConverting ? "ĐANG CHUYỂN..." : "XÁC NHẬN & IN TEM" }}
          </button>
        </template>
      </BaseModal>

      <BaseModal
        :is-open="isPriceModalOpen"
        title="Cập Nhật Giá Gốc"
        @close="closePriceModal"
      >
        <div v-if="selectedPriceItem" class="price-update-grid">
          <div class="price-banner">
            <span class="material-icons">sell</span>
            Giá gốc này sẽ ảnh hưởng đến giá bán/thuê tính theo rule cho tập truyện tương ứng.
          </div>

          <div class="form-group full-width">
            <label>Đầu sách</label>
            <input type="text" :value="selectedPriceItem.name" disabled />
          </div>

          <div class="form-group full-width">
            <label>Giá gốc mới (VND)</label>
            <input
              ref="priceInputRef"
              v-model.number="priceUpdateValue"
              type="number"
              min="1000"
              step="1000"
            />
          </div>

          <p class="price-preview">
            Giá hiện tại: <strong>{{ formatCurrency(Number(selectedPriceItem.price || 0)) }}</strong> →
            Giá mới: <strong>{{ formatCurrency(Math.max(1000, Number(priceUpdateValue || 0))) }}</strong>
          </p>
        </div>

        <template #footer>
          <button class="btn-secondary" @click="closePriceModal">Hủy</button>
          <button class="btn-primary" :disabled="isUpdatingPrice" @click="processUpdatePrice">
            {{ isUpdatingPrice ? "ĐANG CẬP NHẬT..." : "LƯU GIÁ" }}
          </button>
        </template>
      </BaseModal>

      <BaseModal
        :is-open="isSkuResultModalOpen"
        title="Đã Tạo Mã SKU Thuê"
        @close="isSkuResultModalOpen = false"
      >
        <div class="sku-result-wrap">
          <p class="sku-result-title">Đã tạo {{ lastGeneratedSkus.length }} mã SKU thành công</p>
          <div class="sku-grid">
            <div v-for="sku in lastGeneratedSkus" :key="sku" class="sku-card">
              <span class="material-icons">qr_code_2</span>
              <strong>{{ sku }}</strong>
            </div>
          </div>
        </div>

        <template #footer>
          <button class="btn-secondary" @click="copySkuList">Copy danh sách</button>
          <button class="btn-primary" @click="printSkuLabels">In tất cả tem</button>
        </template>
      </BaseModal>

      <HotkeyBar :items="hotkeyItems" />
    </div>
  </DefaultLayout>
</template>

<script setup lang="ts">
import { computed, inject, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { useScannerStore } from "../stores/scanner";
import DefaultLayout from "../components/layout/defaultLayout.vue";
import BaseModal from "../components/layout/BaseModal.vue";
import HotkeyBar, { type HotkeyItem } from "../components/layout/HotkeyBar.vue";
import {
  autofillTitleMetadata,
  StoryHubApiError,
  fetchInventoryItems,
  convertToRental,
  createVolume,
  importCoverImage,
  updateVolumePrice,
  buildRequestId,
  type InventoryItemListItem,
} from "../services/storyhubApi";

type IntakeMode = "new" | "restock";
type InventoryTypeFilter = "all" | "rental" | "retail";
type InventoryStatusFilter =
  | "all"
  | "available"
  | "reserved"
  | "rented"
  | "in_stock"
  | "out_of_stock"
  | "lost"
  | "damaged"
  | "maintenance"
  | "unready";

interface HotkeyEventDetail {
  name?: "f1" | "f2" | "f3" | "escape";
}

const scannerStore = useScannerStore();
const addNotification = inject("addNotification") as (type: string, message: string) => void;

const searchInputRef = ref<HTMLInputElement | null>(null);
const isbnInputRef = ref<HTMLInputElement | null>(null);
const restockInputRef = ref<HTMLInputElement | null>(null);
const coverFileInputRef = ref<HTMLInputElement | null>(null);
const priceInputRef = ref<HTMLInputElement | null>(null);

const isLoading = ref(true);
const searchQuery = ref("");
const inventoryTypeFilter = ref<InventoryTypeFilter>("all");
const inventoryStatusFilter = ref<InventoryStatusFilter>("all");
const items = ref<InventoryItemListItem[]>([]);

const isCreateModalOpen = ref(false);
const intakeMode = ref<IntakeMode>("new");
const isCreating = ref(false);

const newVolumeForm = ref({
  title_name: "",
  author: "",
  description: "",
  cover_url: "",
  page_count: null as number | null,
  categories: "",
  published_date: "",
  volume_number: 1,
  isbn: "",
  retail_stock: 1,
  p_sell_new: 0,
});

const metadataState = ref<"idle" | "loading" | "success" | "error">("idle");
const metadataMessage = ref("Nhập ISBN để tự điền metadata qua backend.");
const isMetadataLoading = ref(false);
const coverImportState = ref<"idle" | "loading" | "success" | "error">("idle");
const coverImportMessage = ref("Có thể Browse file ảnh hoặc dán link để lưu local.");
const isCoverImporting = ref(false);
const manualCoverUrlInput = ref("");
const selectedCoverFileName = ref("");

const restockForm = ref({
  isbn: "",
  quantity: 1,
});

const isConvertModalOpen = ref(false);
const isConverting = ref(false);
const selectedRetailItem = ref<InventoryItemListItem | null>(null);
const convertQuantity = ref(1);

const isPriceModalOpen = ref(false);
const isUpdatingPrice = ref(false);
const selectedPriceItem = ref<InventoryItemListItem | null>(null);
const priceUpdateValue = ref(30000);

const isSkuResultModalOpen = ref(false);
const lastGeneratedSkus = ref<string[]>([]);

const hotkeyItems: HotkeyItem[] = [
  { key: "F1", label: "Xác nhận modal hiện tại" },
  { key: "F2", label: "Focus ô tìm kiếm" },
  { key: "F3", label: "Đổi lọc loại hàng / tra metadata" },
  { key: "ESC", label: "Đóng modal / về Hub" },
];

const normalizeToken = (value: string) => value.replace(/[^A-Za-z0-9]/g, "").toUpperCase();
const normalizeIsbn = (value: string) => value.replace(/[^0-9Xx]/g, "").toUpperCase();
const parseCategoriesInput = (value: string) => {
  return value
    .split(",")
    .map((entry) => entry.trim())
    .filter((entry) => entry.length > 0);
};

const isHttpUrl = (value: string) => /^https?:\/\//i.test(value.trim());
const isBase64ImageDataUrl = (value: string) =>
  /^data:image\/[a-z0-9.+-]+;base64,/i.test(value.trim());
const normalizeManualCoverInput = (value: string) => {
  let normalized = value.trim();
  if (
    (normalized.startsWith('"') && normalized.endsWith('"')) ||
    (normalized.startsWith("'") && normalized.endsWith("'"))
  ) {
    normalized = normalized.slice(1, -1).trim();
  }
  return normalized.replace(/\s+/g, "");
};

const readFileAsDataUrl = (file: File): Promise<string> => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result ?? ""));
    reader.onerror = () => reject(new Error("file-read-failed"));
    reader.readAsDataURL(file);
  });
};

const resolveIsbnForCoverImport = (): string | null => {
  const normalizedIsbn = normalizeIsbn(newVolumeForm.value.isbn);
  if (normalizedIsbn.length < 10) {
    coverImportState.value = "error";
    coverImportMessage.value = "Vui lòng nhập ISBN hợp lệ trước khi nhập ảnh bìa.";
    return null;
  }
  return normalizedIsbn;
};

const importCoverByUrl = async (imageUrl: string, sourceLabel: string) => {
  const normalizedIsbn = resolveIsbnForCoverImport();
  if (!normalizedIsbn) {
    return false;
  }

  isCoverImporting.value = true;
  coverImportState.value = "loading";
  coverImportMessage.value = `Đang tải ảnh từ ${sourceLabel}...`;

  try {
    const payload = await importCoverImage({
      isbn: normalizedIsbn,
      image_url: imageUrl.trim(),
      request_id: buildRequestId("inventory-cover-url"),
    });
    newVolumeForm.value.cover_url = payload.cover_url;
    coverImportState.value = "success";
    coverImportMessage.value = "Đã lưu ảnh bìa local thành công.";
    return true;
  } catch (error: any) {
    coverImportState.value = "error";
    coverImportMessage.value = error?.message || "Không thể tải ảnh từ link đã nhập.";
    return false;
  } finally {
    isCoverImporting.value = false;
  }
};

const importCoverByBase64 = async (base64Data: string, fileLabel: string) => {
  const normalizedIsbn = resolveIsbnForCoverImport();
  if (!normalizedIsbn) {
    return false;
  }

  isCoverImporting.value = true;
  coverImportState.value = "loading";
  coverImportMessage.value = `Đang lưu ảnh local từ file ${fileLabel}...`;

  try {
    const payload = await importCoverImage({
      isbn: normalizedIsbn,
      image_base64: base64Data,
      request_id: buildRequestId("inventory-cover-file"),
    });
    newVolumeForm.value.cover_url = payload.cover_url;
    coverImportState.value = "success";
    coverImportMessage.value = "Đã lưu ảnh bìa local từ file thành công.";
    return true;
  } catch (error: any) {
    coverImportState.value = "error";
    coverImportMessage.value = error?.message || "Không thể lưu ảnh từ file đã chọn.";
    return false;
  } finally {
    isCoverImporting.value = false;
  }
};

const triggerCoverFileDialog = () => {
  coverFileInputRef.value?.click();
};

const onCoverFileSelected = async (event: Event) => {
  const target = event.target as HTMLInputElement;
  const file = target.files?.[0];
  if (!file) {
    return;
  }

  selectedCoverFileName.value = file.name;
  try {
    const dataUrl = await readFileAsDataUrl(file);
    await importCoverByBase64(dataUrl, file.name);
  } catch {
    coverImportState.value = "error";
    coverImportMessage.value = "Không thể đọc file ảnh đã chọn.";
  } finally {
    target.value = "";
  }
};

const importCoverFromManualLink = async () => {
  const link = normalizeManualCoverInput(manualCoverUrlInput.value);
  if (!link) {
    coverImportState.value = "error";
    coverImportMessage.value = "Vui lòng dán link ảnh hoặc data URL base64.";
    return;
  }

  if (isBase64ImageDataUrl(link)) {
    await importCoverByBase64(link, "data URL");
    return;
  }

  if (!isHttpUrl(link)) {
    coverImportState.value = "error";
    coverImportMessage.value =
      "Định dạng không hợp lệ. Hỗ trợ http/https hoặc data:image/...;base64,...";
    return;
  }

  await importCoverByUrl(link, "link thủ công");
};

const statusLabelMap: Record<string, string> = {
  available: "Sẵn sàng",
  reserved: "Đã giữ chỗ",
  rented: "Đang cho thuê",
  lost: "Mất",
  damaged: "Hư hỏng",
  maintenance: "Bảo trì",
  in_stock: "Còn hàng",
  out_of_stock: "Hết hàng",
  unready: "Chưa sẵn sàng",
};

const inventoryStatusFilterOptions: Array<{
  value: InventoryStatusFilter;
  label: string;
}> = [
  { value: "all", label: "Mọi trạng thái" },
  { value: "available", label: "Sẵn sàng" },
  { value: "reserved", label: "Đã giữ chỗ" },
  { value: "rented", label: "Đang cho thuê" },
  { value: "in_stock", label: "Còn hàng" },
  { value: "out_of_stock", label: "Hết hàng" },
  { value: "unready", label: "Chưa sẵn sàng" },
  { value: "lost", label: "Mất" },
  { value: "damaged", label: "Hư hỏng" },
  { value: "maintenance", label: "Bảo trì" },
];

const inventoryTypeFilterCycle: InventoryTypeFilter[] = ["all", "rental", "retail"];

const inventoryTypeFilterLabelMap: Record<InventoryTypeFilter, string> = {
  all: "toàn bộ kho",
  rental: "chỉ hàng thuê",
  retail: "chỉ hàng bán",
};

const formatCurrency = (value: number) => {
  const normalized = Math.max(0, Math.floor(Number(value) || 0));
  return normalized.toLocaleString("vi-VN") + " đ";
};

const formatInventoryStatus = (rawStatus: string) => {
  const normalized = String(rawStatus ?? "").trim().toLowerCase();
  if (!normalized) {
    return "Không rõ";
  }

  return statusLabelMap[normalized] ?? rawStatus;
};

const resolveRetailStock = (item: InventoryItemListItem | null) => {
  if (!item || item.type !== "retail") {
    return 0;
  }

  const fromField = Number(item.stock_quantity ?? 0);
  if (Number.isFinite(fromField) && fromField >= 0) {
    return Math.floor(fromField);
  }

  return 0;
};

const formatStockQuantity = (item: InventoryItemListItem) => {
  if (item.type === "retail") {
    return `${resolveRetailStock(item)} bản`;
  }

  return "1 SKU";
};

const resolveInventoryStatusKey = (item: InventoryItemListItem): InventoryStatusFilter => {
  const normalized = String(item.status ?? "").trim().toLowerCase();
  if (!normalized) {
    return "all";
  }

  if (item.type === "retail") {
    if (normalized === "available") {
      return "in_stock";
    }
    if (normalized === "out_of_stock" || normalized === "unavailable") {
      return "out_of_stock";
    }
    if (normalized === "unready") {
      return "unready";
    }
  }

  if (
    normalized === "available" ||
    normalized === "reserved" ||
    normalized === "rented" ||
    normalized === "in_stock" ||
    normalized === "out_of_stock" ||
    normalized === "lost" ||
    normalized === "damaged" ||
    normalized === "maintenance"
  ) {
    return normalized;
  }

  return "all";
};

const extractTitleAndVolume = (rawTitle: string) => {
  const cleaned = rawTitle.trim();
  const volumeMatch = cleaned.match(/(?:\b(?:t\.?|tap|tập|vol(?:ume)?\.?)[\s#:.-]*)(\d{1,4})/i);

  if (!volumeMatch) {
    return { title: cleaned, volume: 1 };
  }

  const volume = Number(volumeMatch[1]) || 1;
  const title = cleaned.replace(volumeMatch[0], "").replace(/[-:()\s]+$/g, "").trim();
  return {
    title: title || cleaned,
    volume,
  };
};

const filteredItems = computed(() => {
  const query = searchQuery.value.trim().toLowerCase();
  const matchedByText = query
    ? items.value.filter((item) => {
        return item.name.toLowerCase().includes(query) || item.code.toLowerCase().includes(query);
      })
    : items.value;

  const matchedByType =
    inventoryTypeFilter.value === "all"
      ? matchedByText
      : matchedByText.filter((item) => item.type === inventoryTypeFilter.value);

  if (inventoryStatusFilter.value === "all") {
    return matchedByType;
  }

  return matchedByType.filter(
    (item) => resolveInventoryStatusKey(item) === inventoryStatusFilter.value,
  );
});

const selectedRetailStock = computed(() => {
  return resolveRetailStock(selectedRetailItem.value);
});

const resolveVolumeIdFromItem = (item: InventoryItemListItem | null) => {
  if (!item) {
    return 0;
  }

  const rawVolumeId = Number(item.volume_id ?? 0);
  if (Number.isFinite(rawVolumeId) && rawVolumeId > 0) {
    return rawVolumeId;
  }

  const fallback = Number(String(item.id).replace(/\D/g, ""));
  if (Number.isFinite(fallback) && fallback > 0) {
    return fallback;
  }

  return 0;
};

const selectedVolumeId = computed(() => {
  return resolveVolumeIdFromItem(selectedRetailItem.value);
});

const estimatedSkuList = computed(() => {
  if (!selectedRetailItem.value) {
    return [];
  }

  const volumePart = selectedVolumeId.value || 0;
  const qty = Math.max(0, Math.min(convertQuantity.value || 0, 12));
  return Array.from({ length: qty }).map((_, index) => {
    return `RNT-${volumePart}-${String(index + 1).padStart(3, "0")}`;
  });
});

const canConvert = computed(() => {
  return (
    !!selectedRetailItem.value &&
    convertQuantity.value > 0 &&
    convertQuantity.value <= selectedRetailStock.value
  );
});

const matchedRestockItem = computed(() => {
  const isbn = normalizeToken(restockForm.value.isbn);
  if (!isbn) {
    return null;
  }

  return (
    items.value.find(
      (item) => item.type === "retail" && normalizeToken(item.code) === isbn,
    ) ?? null
  );
});

const canCreateNew = computed(() => {
  return (
    newVolumeForm.value.title_name.trim().length > 0 &&
    newVolumeForm.value.volume_number > 0 &&
    normalizeIsbn(newVolumeForm.value.isbn).length >= 10 &&
    newVolumeForm.value.retail_stock > 0
  );
});

const canRestock = computed(() => {
  return !!matchedRestockItem.value && restockForm.value.quantity > 0;
});

const resetNewVolumeForm = () => {
  newVolumeForm.value = {
    title_name: "",
    author: "",
    description: "",
    cover_url: "",
    page_count: null,
    categories: "",
    published_date: "",
    volume_number: 1,
    isbn: "",
    retail_stock: 1,
    p_sell_new: 0,
  };
  metadataState.value = "idle";
  metadataMessage.value = "Nhập ISBN để tự điền metadata qua backend.";
  coverImportState.value = "idle";
  coverImportMessage.value = "Có thể Browse file ảnh hoặc dán link để lưu local.";
  isCoverImporting.value = false;
  manualCoverUrlInput.value = "";
  selectedCoverFileName.value = "";
};

const loadData = async () => {
  isLoading.value = true;
  try {
    items.value = await fetchInventoryItems();
  } catch {
    addNotification("error", "Lỗi nạp dữ liệu kho.");
  } finally {
    isLoading.value = false;
  }
};

const applyMetadata = (
  metadata: {
    name: string;
    author: string;
    genre: string;
    description: string;
    cover_url: string;
    confidence: number;
  },
  source: "cache" | "external_api" | "fallback",
) => {
  const normalizedTitle = metadata.name.trim();
  const parsed = extractTitleAndVolume(normalizedTitle);
  const normalizedGenres = parseCategoriesInput(metadata.genre);

  newVolumeForm.value.title_name = parsed.title;
  newVolumeForm.value.volume_number = parsed.volume;
  if (metadata.author.trim().length > 0) {
    newVolumeForm.value.author = metadata.author.trim();
  }
  newVolumeForm.value.description = metadata.description;
  newVolumeForm.value.cover_url = metadata.cover_url;
  newVolumeForm.value.categories = normalizedGenres.join(", ");

  metadataState.value = "success";
  const sourceLabel =
    source === "cache"
      ? "cache local"
      : source === "external_api"
        ? "nguồn ngoài"
        : "fallback nội bộ";
  metadataMessage.value = `Đã tự điền metadata (${sourceLabel}): ${parsed.title} (Tập ${parsed.volume}).`;
};

const lookupMetadataByIsbn = async (rawIsbn: string) => {
  const isbn = normalizeIsbn(rawIsbn);
  if (isbn.length < 10) {
    metadataState.value = "error";
    metadataMessage.value = "ISBN quá ngắn để tra metadata.";
    return;
  }

  isMetadataLoading.value = true;
  metadataState.value = "loading";
  metadataMessage.value = "Đang tra metadata qua backend...";

  try {
    const response = await autofillTitleMetadata({
      isbn,
      request_id: buildRequestId("inventory-metadata-autofill"),
    });

    applyMetadata(response.metadata, response.source);

    if (response.metadata.cover_url && isHttpUrl(response.metadata.cover_url)) {
      await importCoverByUrl(response.metadata.cover_url, "metadata provider");
    }
  } catch (error: unknown) {
    const apiError = error instanceof StoryHubApiError ? error : null;
    metadataState.value = "error";
    if (apiError?.code === "EXTERNAL_API_TIMEOUT") {
      metadataMessage.value = "Nguồn metadata đang chậm. Vui lòng thử lại sau vài giây.";
    } else if (apiError?.code === "METADATA_NOT_FOUND") {
      metadataMessage.value = "Không tìm thấy metadata phù hợp. Vui lòng nhập thủ công.";
    } else {
      metadataMessage.value = apiError?.message || "Không thể tra metadata ở thời điểm hiện tại.";
    }
    newVolumeForm.value.cover_url = "";
  } finally {
    isMetadataLoading.value = false;
  }
};

const openCreateModal = (mode: IntakeMode, scannedIsbn = "") => {
  intakeMode.value = mode;
  isCreateModalOpen.value = true;

  if (mode === "new") {
    resetNewVolumeForm();
    if (scannedIsbn) {
      newVolumeForm.value.isbn = scannedIsbn;
      void lookupMetadataByIsbn(scannedIsbn);
    }
    setTimeout(() => isbnInputRef.value?.focus(), 120);
    return;
  }

  restockForm.value = {
    isbn: scannedIsbn,
    quantity: 1,
  };
  setTimeout(() => restockInputRef.value?.focus(), 120);
};

const processCreateVolume = async () => {
  if (!canCreateNew.value) {
    return;
  }

  isCreating.value = true;
  try {
    const normalizedCategories = parseCategoriesInput(newVolumeForm.value.categories);
    const normalizedPageCount = Number(newVolumeForm.value.page_count);

    await createVolume({
      title_name: newVolumeForm.value.title_name.trim(),
      isbn: normalizeIsbn(newVolumeForm.value.isbn),
      author: newVolumeForm.value.author.trim() || "Unknown",
      description: newVolumeForm.value.description.trim() || undefined,
      cover_url: newVolumeForm.value.cover_url.trim() || undefined,
      categories: normalizedCategories.length > 0 ? normalizedCategories : undefined,
      page_count:
        Number.isFinite(normalizedPageCount) && normalizedPageCount > 0
          ? Math.floor(normalizedPageCount)
          : undefined,
      published_date: newVolumeForm.value.published_date.trim() || undefined,
      volume_number: newVolumeForm.value.volume_number,
      retail_stock: newVolumeForm.value.retail_stock,
      request_id: buildRequestId("inventory-create-vol"),
    });

    addNotification(
      "success",
      `Đã nhập ${newVolumeForm.value.title_name} tập ${newVolumeForm.value.volume_number} thành công.`,
    );

    isCreateModalOpen.value = false;
    resetNewVolumeForm();
    await loadData();
  } catch (error: any) {
    addNotification("error", error?.message || "Không thể tạo đầu sách mới.");
  } finally {
    isCreating.value = false;
  }
};

const processRestockVolume = async () => {
  if (!canRestock.value || !matchedRestockItem.value) {
    return;
  }

  const parsed = extractTitleAndVolume(matchedRestockItem.value.name);
  isCreating.value = true;
  try {
    await createVolume({
      title_name: parsed.title,
      author: "Unknown",
      volume_number: parsed.volume,
      isbn: matchedRestockItem.value.code,
      retail_stock: Math.max(1, restockForm.value.quantity),
      request_id: buildRequestId("inventory-restock"),
    });

    addNotification("success", `Đã bổ sung ${restockForm.value.quantity} bản vào kho bán.`);
    isCreateModalOpen.value = false;
    restockForm.value = { isbn: "", quantity: 1 };
    await loadData();
  } catch (error: any) {
    addNotification("error", error?.message || "Không thể bổ sung tồn kho.");
  } finally {
    isCreating.value = false;
  }
};

const openConvertModal = (item: InventoryItemListItem) => {
  if (resolveRetailStock(item) < 1) {
    addNotification("warning", "Đầu sách này đã hết tồn kho bán, không thể chuyển sang hàng thuê.");
    return;
  }

  selectedRetailItem.value = item;
  convertQuantity.value = 1;
  isConvertModalOpen.value = true;
};

const openPriceModal = (item: InventoryItemListItem) => {
  selectedPriceItem.value = item;
  priceUpdateValue.value = Math.max(1000, Math.floor(Number(item.price) || 30000));
  isPriceModalOpen.value = true;
  setTimeout(() => priceInputRef.value?.focus(), 120);
};

const closePriceModal = () => {
  isPriceModalOpen.value = false;
  isUpdatingPrice.value = false;
  selectedPriceItem.value = null;
  priceUpdateValue.value = 30000;
};

const processUpdatePrice = async () => {
  if (!selectedPriceItem.value) {
    return;
  }

  const volumeId = resolveVolumeIdFromItem(selectedPriceItem.value);
  if (!volumeId) {
    addNotification("error", "Không xác định được volume_id để cập nhật giá.");
    return;
  }

  const normalizedPrice = Math.max(1000, Math.floor(Number(priceUpdateValue.value) || 0));
  isUpdatingPrice.value = true;

  try {
    const response = await updateVolumePrice(volumeId, {
      p_sell_new: normalizedPrice,
      request_id: buildRequestId("inventory-update-price"),
    });
    addNotification(
      "success",
      `Đã cập nhật giá từ ${formatCurrency(response.old_price)} lên ${formatCurrency(response.new_price)}.`,
    );
    closePriceModal();
    await loadData();
  } catch (error: any) {
    addNotification("error", error?.message || "Không thể cập nhật giá cho đầu sách này.");
  } finally {
    isUpdatingPrice.value = false;
  }
};

const processConversion = async () => {
  if (!canConvert.value || !selectedRetailItem.value) {
    return;
  }

  if (!selectedVolumeId.value) {
    addNotification("error", "Không xác định được volume_id để chuyển SKU thuê.");
    return;
  }

  isConverting.value = true;
  try {
    const response = await convertToRental({
      volume_id: selectedVolumeId.value,
      quantity: convertQuantity.value,
      request_id: buildRequestId("inventory-convert"),
    });

    lastGeneratedSkus.value = response.new_skus;
    isConvertModalOpen.value = false;
    isSkuResultModalOpen.value = true;

    addNotification("success", `Đã chuyển ${response.converted_quantity} bản sang kho thuê.`);
    await loadData();
  } catch (error: any) {
    addNotification("error", error?.message || "Không thể chuyển sang hàng thuê.");
  } finally {
    isConverting.value = false;
  }
};

const copySkuList = async () => {
  if (lastGeneratedSkus.value.length === 0) {
    return;
  }

  try {
    await navigator.clipboard.writeText(lastGeneratedSkus.value.join("\n"));
    addNotification("success", "Đã copy danh sách SKU.");
  } catch {
    addNotification("warning", "Không thể copy tự động, vui lòng copy thủ công.");
  }
};

const printSkuLabels = () => {
  if (lastGeneratedSkus.value.length === 0) {
    return;
  }

  const printWindow = window.open("", "_blank", "width=900,height=680");
  if (!printWindow) {
    addNotification("error", "Không mở được cửa sổ in.");
    return;
  }

  const labels = lastGeneratedSkus.value
    .map(
      (sku) =>
        `<div class="label"><div class="barcode">|||| |||| ||||</div><div class="sku">${sku}</div></div>`,
    )
    .join("");

  printWindow.document.write(`
    <html>
      <head>
        <title>StoryHub SKU Labels</title>
        <style>
          body { font-family: Arial, sans-serif; padding: 20px; }
          .grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; }
          .label { border: 1px solid #111; border-radius: 8px; padding: 14px; text-align: center; }
          .barcode { font-size: 18px; letter-spacing: 2px; margin-bottom: 8px; }
          .sku { font-size: 16px; font-weight: 700; }
        </style>
      </head>
      <body>
        <h2>StoryHub Rental SKU</h2>
        <div class="grid">${labels}</div>
      </body>
    </html>
  `);
  printWindow.document.close();
  printWindow.focus();
  printWindow.print();
};

const handleGlobalHotkey = (event: Event) => {
  const customEvent = event as CustomEvent<HotkeyEventDetail>;
  const hotkey = customEvent.detail?.name;

  if (hotkey === "f2") {
    searchInputRef.value?.focus();
    return;
  }

  if (hotkey === "f3") {
    if (isCreateModalOpen.value && intakeMode.value === "new") {
      void lookupMetadataByIsbn(newVolumeForm.value.isbn);
      return;
    }

    const currentIndex = inventoryTypeFilterCycle.indexOf(inventoryTypeFilter.value);
    const nextIndex = (currentIndex + 1) % inventoryTypeFilterCycle.length;
    inventoryTypeFilter.value = inventoryTypeFilterCycle[nextIndex];
    addNotification(
      "info",
      `Đã đổi lọc loại hàng: ${inventoryTypeFilterLabelMap[inventoryTypeFilter.value]}.`,
    );
    return;
  }

  if (hotkey === "f1") {
    if (isPriceModalOpen.value) {
      void processUpdatePrice();
      return;
    }

    if (isCreateModalOpen.value) {
      if (intakeMode.value === "new") {
        void processCreateVolume();
      } else {
        void processRestockVolume();
      }
      return;
    }

    if (isConvertModalOpen.value) {
      void processConversion();
    }
    return;
  }

  if (hotkey === "escape") {
    if (isSkuResultModalOpen.value) {
      isSkuResultModalOpen.value = false;
      return;
    }

    if (isPriceModalOpen.value) {
      closePriceModal();
      return;
    }

    if (isConvertModalOpen.value) {
      isConvertModalOpen.value = false;
      return;
    }

    if (isCreateModalOpen.value) {
      isCreateModalOpen.value = false;
    }
  }
};

let stopScannerWatch: (() => void) | null = null;

onMounted(async () => {
  await loadData();

  stopScannerWatch = watch(
    () => scannerStore.scanEventCounter,
    () => {
      if (scannerStore.lastScannedItem) {
        // Keep scanned item for checkout page to consume and auto-add to cart.
        // Clearing it here can race with router navigation from global scanner logic.
        return;
      }

      if (!scannerStore.lastScannedCode) {
        return;
      }

      const scanned = scannerStore.lastScannedCode;
      openCreateModal("new", scanned);
      addNotification("info", "Mã chưa có trong kho. Mời nhập thông tin đầu sách mới.");
      scannerStore.lastScannedCode = "";
    },
    { immediate: true },
  );

  window.addEventListener("storyhub:hotkey", handleGlobalHotkey as EventListener);
});

onBeforeUnmount(() => {
  window.removeEventListener("storyhub:hotkey", handleGlobalHotkey as EventListener);
  if (stopScannerWatch) {
    stopScannerWatch();
    stopScannerWatch = null;
  }
});
</script>

<style scoped>
@import url("https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap");

.inventory-page {
  padding: 28px;
  min-height: 100vh;
  background:
    radial-gradient(circle at 10% 10%, rgba(16, 185, 129, 0.12), transparent 26%),
    radial-gradient(circle at 88% 86%, rgba(59, 130, 246, 0.12), transparent 28%),
    #f8fafc;
  font-family: "Plus Jakarta Sans", sans-serif;
}

.header-section {
  margin-bottom: 18px;
}

.page-title {
  margin: 0;
  color: #0f172a;
  font-size: 2rem;
  letter-spacing: -0.03em;
}

.subtitle {
  margin: 4px 0 0;
  color: #64748b;
}

.actions-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.inventory-filter-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 12px;
}

.filter-group {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}

.filter-group-title {
  font-size: 0.78rem;
  font-weight: 800;
  color: #475569;
  margin-right: 2px;
}

.filter-btn {
  border: 1px solid #cbd5e1;
  border-radius: 999px;
  background: white;
  color: #475569;
  padding: 7px 12px;
  font-weight: 700;
  cursor: pointer;
}

.filter-btn.compact {
  padding: 6px 10px;
  font-size: 0.76rem;
}

.filter-btn.active {
  background: #1d4ed8;
  color: white;
  border-color: #1d4ed8;
}

.action-buttons {
  display: flex;
  gap: 8px;
}

.search-input {
  width: 100%;
  max-width: 460px;
  border: 1px solid #cbd5e1;
  border-radius: 12px;
  padding: 11px 14px;
  font-family: inherit;
}

.table-container {
  background: white;
  border-radius: 16px;
  border: 1px solid #e2e8f0;
  overflow: hidden;
}

table {
  width: 100%;
  border-collapse: collapse;
}

th {
  background: #f8fafc;
  padding: 14px;
  text-align: left;
  color: #64748b;
  font-weight: 800;
  font-size: 0.8rem;
  text-transform: uppercase;
}

td {
  padding: 14px;
  border-bottom: 1px solid #e2e8f0;
  color: #334155;
}

.code-text {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
  color: #1e3a8a;
  font-weight: 700;
}

.font-medium {
  font-weight: 700;
}

.text-center {
  text-align: center;
}

.price-text {
  color: #0f766e;
  font-weight: 800;
  white-space: nowrap;
}

.stock-qty-text {
  color: #0f172a;
  font-weight: 700;
  white-space: nowrap;
}

.tag-sale,
.tag-rent {
  border-radius: 999px;
  padding: 5px 10px;
  font-size: 0.76rem;
  font-weight: 800;
}

.tag-sale {
  background: #dcfce7;
  color: #166534;
}

.tag-rent {
  background: #ffedd5;
  color: #9a3412;
}

.stock-badge,
.status-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  padding: 5px 12px;
  font-weight: 700;
}

.stock-badge {
  background: #f1f5f9;
  color: #334155;
}

.status-badge {
  background: #eff6ff;
  color: #1d4ed8;
}

.btn-inline,
.btn-primary,
.btn-secondary {
  border: none;
  border-radius: 10px;
  padding: 9px 12px;
  font-weight: 700;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.btn-inline {
  background: #e0f2fe;
  color: #075985;
}

.btn-inline:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.btn-inline.btn-price {
  background: #e2e8f0;
  color: #334155;
}

.btn-primary {
  background: #2563eb;
  color: white;
}

.btn-secondary {
  background: #e2e8f0;
  color: #334155;
}

.btn-primary:disabled,
.btn-secondary:disabled {
  opacity: 0.65;
  cursor: not-allowed;
}

.empty-state {
  text-align: center;
  color: #94a3b8;
}

.row-actions {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.mode-toggle {
  display: inline-flex;
  border: 1px solid #dbeafe;
  border-radius: 999px;
  padding: 3px;
  gap: 4px;
  margin-bottom: 12px;
}

.mode-btn {
  border: none;
  border-radius: 999px;
  padding: 7px 12px;
  background: transparent;
  color: #475569;
  font-weight: 700;
  cursor: pointer;
}

.mode-btn.active {
  background: #2563eb;
  color: white;
}

.form-grid {
  display: grid;
  grid-template-columns: 120px 1fr 1fr;
  gap: 12px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-group label {
  font-size: 0.84rem;
  font-weight: 700;
  color: #475569;
}

.form-group input {
  width: 100%;
  border: 1px solid #cbd5e1;
  border-radius: 10px;
  padding: 9px 10px;
  font-family: inherit;
}

.form-group textarea {
  width: 100%;
  border: 1px solid #cbd5e1;
  border-radius: 10px;
  padding: 9px 10px;
  font-family: inherit;
  resize: vertical;
}

.form-group.full-width {
  grid-column: 1 / -1;
}

.isbn-row {
  display: flex;
  gap: 8px;
}

.cover-manual-row {
  display: grid;
  grid-template-columns: auto 1fr auto;
  gap: 8px;
  align-items: center;
}

.cover-file-input {
  display: none;
}

.cover-file-name {
  margin: 6px 0 0;
  font-size: 0.8rem;
  color: #334155;
  font-weight: 600;
}

.metadata-status {
  margin: 6px 0 0;
  font-size: 0.82rem;
  font-weight: 700;
}

.cover-import-status {
  margin: 6px 0 0;
  font-size: 0.82rem;
  font-weight: 700;
}

.metadata-status.idle {
  color: #64748b;
}

.metadata-status.loading {
  color: #0369a1;
}

.metadata-status.success {
  color: #166534;
}

.metadata-status.error {
  color: #b91c1c;
}

.cover-import-status.idle {
  color: #64748b;
}

.cover-import-status.loading {
  color: #0369a1;
}

.cover-import-status.success {
  color: #166534;
}

.cover-import-status.error {
  color: #b91c1c;
}

.cover-preview-wrap {
  grid-row: span 3;
  width: 100%;
  border-radius: 10px;
  overflow: hidden;
  border: 1px solid #dbeafe;
  background: #f8fafc;
}

.cover-preview-wrap img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.restock-grid {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.restock-preview {
  border: 1px solid #bbf7d0;
  background: #ecfdf3;
  border-radius: 10px;
  padding: 10px;
}

.restock-preview p {
  margin: 0 0 8px;
}

.restock-preview label {
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-weight: 700;
}

.restock-preview input {
  width: 140px;
  border: 1px solid #86efac;
  border-radius: 8px;
  padding: 8px;
}

.restock-hint {
  margin: 0;
  color: #92400e;
  background: #fffbeb;
  border: 1px dashed #fcd34d;
  border-radius: 10px;
  padding: 10px;
}

.convert-grid {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.price-update-grid {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.price-banner {
  border-radius: 10px;
  border: 1px solid #99f6e4;
  background: #f0fdfa;
  color: #0f766e;
  padding: 10px;
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 700;
}

.price-preview {
  margin: 0;
  border-radius: 10px;
  border: 1px dashed #94a3b8;
  background: #f8fafc;
  padding: 10px;
  color: #334155;
  font-weight: 600;
}

.convert-banner {
  border-radius: 10px;
  border: 1px solid #bfdbfe;
  background: #eff6ff;
  color: #1e3a8a;
  padding: 10px;
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 700;
}

.convert-preview-box {
  border-radius: 10px;
  border: 1px dashed #a5b4fc;
  background: #f5f3ff;
  padding: 10px;
}

.convert-preview-box p {
  margin: 0 0 8px;
  color: #4338ca;
}

.sku-preview-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.sku-chip {
  border-radius: 999px;
  border: 1px solid #c7d2fe;
  background: white;
  padding: 5px 10px;
  color: #3730a3;
  font-weight: 700;
  font-size: 0.8rem;
}

.sku-result-title {
  margin: 0 0 10px;
  color: #1e293b;
  font-weight: 800;
}

.sku-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}

.sku-card {
  border-radius: 10px;
  border: 1px solid #c7d2fe;
  background: #eef2ff;
  color: #312e81;
  padding: 10px;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.9rem;
}

.screen-loading-state {
  border-radius: 14px;
  border: 1px solid #dbeafe;
  background: white;
  color: #1e3a8a;
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 8px;
  padding: 18px;
  font-weight: 700;
}

.spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

@media (max-width: 980px) {
  .actions-bar {
    flex-direction: column;
    align-items: stretch;
  }

  .inventory-filter-bar {
    flex-wrap: wrap;
  }

  .action-buttons {
    width: 100%;
  }

  .form-grid {
    grid-template-columns: 1fr;
  }

  .cover-manual-row {
    grid-template-columns: 1fr;
  }

  .cover-preview-wrap {
    max-width: 220px;
    height: 280px;
  }

  .sku-grid {
    grid-template-columns: 1fr;
  }
}
</style>
