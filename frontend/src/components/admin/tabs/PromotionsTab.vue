<template>
  <section class="tab-shell">
    <button class="mobile-toggle" @click="leftOpen = !leftOpen">
      {{ leftOpen ? 'Ẩn bộ lọc' : 'Hiện bộ lọc' }}
    </button>

    <div class="tab-split">
      <aside class="left-panel" :class="{ open: leftOpen }">
        <div class="panel-card" >
          <h3>Hành động Khuyến mãi</h3>
          <button class="btn-primary" @click="openVoucherCreate">Tạo Voucher</button>
          <button class="btn-primary" @click="openAutoPromoCreate">Tạo Khuyến mãi tự động</button>
          <button class="btn-primary-lux" @click="openPromoEventCreate">
            <span class="material-icons">event</span>
             Tạo Sự kiện Giảm giá
          </button>
          <button class="btn-ghost" :disabled="isBusy('refresh-all')" @click="refreshAll" style="align-self: center;">
            {{ isBusy('refresh-all') ? 'Đang tải...' : 'Làm mới tất cả' }}
          </button>
          <p v-if="errorMap['refresh-all']" class="error-text">{{ errorMap['refresh-all'] }}</p>
        </div>

        <div class="panel-card">
          <h3>Thống kê nhanh</h3>
          <p class="stat-line">Voucher: <strong>{{ vouchers.length }}</strong></p>
          <p class="stat-line">Khuyến mãi tự động: <strong>{{ autoPromos.length }}</strong></p>
          <p class="stat-line">Sự kiện đang chạy: <strong>{{ activePromoEventCount }}</strong></p>
        </div>
      </aside>

      <div class="right-panel">
        <article class="panel-card">
          <div class="card-head">
            <h3>Danh sách Voucher</h3>
            <span class="pill">{{ vouchers.length }} mã</span>
          </div>

          <div class="table-wrap">
            <table class="table">
              <thead>
                <tr>
                  <th>Mã</th>
                  <th>Loại</th>
                  <th>Giá trị</th>
                  <th>Đã dùng</th>
                  <th>Trạng thái</th>
                  <th>Hành động</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="voucher in vouchers" :key="voucher.id">
                  <td>{{ voucher.code }}</td>
                  <td>{{ voucher.voucher_type }}</td>
                  <td>{{ voucher.value }}</td>
                  <td>{{ voucher.current_uses }}/{{ voucher.max_uses ?? 'inf' }}</td>
                  <td>
                    <span :class="voucher.is_active ? 'pill-ok' : 'pill-danger'">
                      {{ voucher.is_active ? 'Hoạt động' : 'Đã khóa' }}
                    </span>
                  </td>
                  <td class="row-actions">
                    <button class="btn-row" @click="openVoucherEdit(voucher)">Sửa</button>
                    <button class="btn-row warn" @click="toggleVoucher(voucher)">
                      {{ voucher.is_active ? 'Khóa' : 'Mở' }}
                    </button>
                    <button class="btn-row danger" @click="removeVoucher(voucher)">Xóa</button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <p v-if="errorMap['load-vouchers']" class="error-text">{{ errorMap['load-vouchers'] }}</p>
        </article>

        <article class="panel-card">
          <div class="card-head">
            <h3>Khuyến mãi Tự động</h3>
            <span class="pill">{{ autoPromos.length }} quy tắc</span>
          </div>

          <div class="table-wrap">
            <table class="table">
              <thead>
                <tr>
                  <th>Tên</th>
                  <th>Ngày</th>
                  <th>Giảm giá</th>
                  <th>Trạng thái</th>
                  <th>Hành động</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="promo in autoPromos" :key="promo.id">
                  <td>{{ promo.name }}</td>
                  <td>{{ dayName(promo.day_of_week) }}</td>
                  <td>{{ promo.discount_percent }}%</td>
                  <td>
                    <span :class="promo.is_active ? 'pill-ok' : 'pill-danger'">
                      {{ promo.is_active ? 'Hoạt động' : 'Đã khóa' }}
                    </span>
                  </td>
                  <td class="row-actions">
                    <button class="btn-row" @click="openAutoPromoEdit(promo)">Sửa</button>
                    <button class="btn-row warn" @click="toggleAutoPromo(promo)">
                      {{ promo.is_active ? 'Khóa' : 'Mở' }}
                    </button>
                    <button class="btn-row danger" @click="removeAutoPromo(promo)">Xóa</button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <p v-if="errorMap['load-auto-promos']" class="error-text">{{ errorMap['load-auto-promos'] }}</p>
        </article>

        <!-- Promotion Events Section -->
        <article class="panel-card lux-border">
          <div class="card-head">
            <h3>Sự kiện Giảm giá (Promotion Events)</h3>
            <span class="pill">{{ promotionEvents.length }} sự kiện</span>
          </div>

          <div class="table-wrap">
            <table class="table table-lux">
              <thead>
                <tr>
                  <th>Tên sự kiện</th>
                  <th>Giảm giá</th>
                  <th>Thời hạn</th>
                  <th>Trạng thái</th>
                  <th class="text-right">Hành động</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="event in promotionEvents" :key="event.id">
                  <td>
                    <div class="event-name-cell">
                      <span class="name">{{ event.name }}</span>
                      <span class="desc">{{ event.description || 'Không có mô tả' }}</span>
                    </div>
                  </td>
                  <td>
                    <span class="discount-val">
                      {{ event.discount_type === 'percent' ? `-${event.discount_value}%` : `-${formatCurrency(event.discount_value)}` }}
                    </span>
                  </td>
                  <td>
                    <div class="date-range">
                      <span>{{ formatDate(event.start_date) }}</span>
                      <span class="divider">→</span>
                      <span>{{ formatDate(event.end_date) }}</span>
                    </div>
                  </td>
                  <td>
                    <span :class="event.is_active ? 'pill-ok' : 'pill-danger'">
                      {{ event.is_active ? 'Đang chạy' : 'Kết thúc / Khóa' }}
                    </span>
                  </td>
                  <td class="row-actions text-right">
                    <button class="btn-row" @click="managePromoItems(event)" title="Quản lý đầu truyện">
                      <span class="material-icons">menu_book</span>
                    </button>
                    <button class="btn-row" @click="openPromoEventEdit(event)">Sửa</button>
                    <button class="btn-row danger" @click="removePromoEvent(event)">Xóa</button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <p v-if="errorMap['load-promo-events']" class="error-text">{{ errorMap['load-promo-events'] }}</p>
        </article>
      </div>
    </div>

    <Teleport to="body">
      <!-- Modal xác nhận xóa Voucher -->
      <div v-if="deleteVoucherModal.open" class="modal-overlay">
        <div class="modal-card">
          <h3>Xóa Voucher vĩnh viễn</h3>
          <p class="modal-subtitle">{{ deleteVoucherModal.code }}</p>

          <label class="field-label">Lý do xóa (bắt buộc)</label>
          <textarea v-model="deleteVoucherModal.reason" class="field-input" rows="3" placeholder="Nhập lý do xóa (tối thiểu 3 ký tự)" />

          <div class="modal-actions">
            <button class="btn-ghost" @click="deleteVoucherModal.open = false">Hủy</button>
            <button
              class="btn-danger"
              :disabled="isBusy('delete-voucher') || !isReasonValid(deleteVoucherModal.reason)"
              @click="submitDeleteVoucher"
            >
              {{ isBusy('delete-voucher') ? 'Đang xóa...' : 'Xóa ngay' }}
            </button>
          </div>
          <p v-if="errorMap['delete-voucher']" class="error-text">{{ errorMap['delete-voucher'] }}</p>
        </div>
      </div>

      <!-- Modal xác nhận xóa AutoPromo -->
      <div v-if="deleteAutoPromoModal.open" class="modal-overlay">
        <div class="modal-card">
          <h3>Xóa Khuyến mãi tự động vĩnh viễn</h3>
          <p class="modal-subtitle">{{ deleteAutoPromoModal.name }}</p>

          <label class="field-label">Lý do xóa (bắt buộc)</label>
          <textarea v-model="deleteAutoPromoModal.reason" class="field-input" rows="3" placeholder="Nhập lý do xóa (tối thiểu 3 ký tự)" />

          <div class="modal-actions">
            <button class="btn-ghost" @click="deleteAutoPromoModal.open = false">Hủy</button>
            <button
              class="btn-danger"
              :disabled="isBusy('delete-auto-promo') || !isReasonValid(deleteAutoPromoModal.reason)"
              @click="submitDeleteAutoPromo"
            >
              {{ isBusy('delete-auto-promo') ? 'Đang xóa...' : 'Xóa ngay' }}
            </button>
          </div>
          <p v-if="errorMap['delete-auto-promo']" class="error-text">{{ errorMap['delete-auto-promo'] }}</p>
        </div>
      </div>

      <div v-if="voucherModal.open" class="modal-overlay">
        <div class="modal-card">
          <h3>{{ voucherModal.mode === 'create' ? 'Tạo Voucher' : 'Cập nhật Voucher' }}</h3>

          <label class="field-label">Mã Code</label>
          <input
            v-model="voucherModal.code"
            class="field-input"
            :disabled="voucherModal.mode === 'edit'"
            placeholder="SUMMER2026"
          />

          <label class="field-label">Loại</label>
          <select v-model="voucherModal.voucher_type" class="field-input">
            <option value="percent">percent</option>
            <option value="amount">amount</option>
          </select>

          <label class="field-label">Giá trị</label>
          <input v-model.number="voucherModal.value" class="field-input" type="number" min="1" />

          <label class="field-label">Chi tiêu tối thiểu</label>
          <input v-model.number="voucherModal.min_spend" class="field-input" type="number" min="0" />

          <label class="field-label">Giảm tối đa</label>
          <input v-model.number="voucherModal.max_discount" class="field-input" type="number" min="0" />

          <label class="field-label">Số lần dùng tối đa</label>
          <input v-model.number="voucherModal.max_uses" class="field-input" type="number" min="1" />

          <label class="field-label">Kết thúc (ISO datetime)</label>
          <input v-model="voucherModal.end_at" class="field-input" placeholder="2026-12-31T23:59:00" />

          <label class="field-checkbox">
            <input v-model="voucherModal.is_active" type="checkbox" />
            Đang hoạt động
          </label>

          <div class="modal-actions">
            <button class="btn-ghost" @click="voucherModal.open = false">Hủy</button>
            <button class="btn-primary" :disabled="isBusy('save-voucher')" @click="saveVoucher">
              {{ isBusy('save-voucher') ? 'Đang lưu...' : 'Lưu Voucher' }}
            </button>
          </div>
          <p v-if="errorMap['save-voucher']" class="error-text">{{ errorMap['save-voucher'] }}</p>
        </div>
      </div>

      <div v-if="autoPromoModal.open" class="modal-overlay">
        <div class="modal-card">
          <h3>{{ autoPromoModal.mode === 'create' ? 'Tạo Khuyến mãi tự động' : 'Cập nhật Khuyến mãi' }}</h3>

          <label class="field-label">Tên chương trình</label>
          <input v-model="autoPromoModal.name" class="field-input" />

          <label class="field-label">Ngày trong tuần (0..6, 0=CN)</label>
          <input v-model.number="autoPromoModal.day_of_week" class="field-input" type="number" min="0" max="6" />

          <label class="field-label">Phần trăm giảm giá</label>
          <input v-model.number="autoPromoModal.discount_percent" class="field-input" type="number" min="1" max="90" />

          <label class="field-checkbox">
            <input v-model="autoPromoModal.is_active" type="checkbox" />
            Đang hoạt động
          </label>

          <div class="modal-actions">
            <button class="btn-ghost" @click="autoPromoModal.open = false">Hủy</button>
            <button class="btn-primary" :disabled="isBusy('save-auto-promo')" @click="saveAutoPromo">
              {{ isBusy('save-auto-promo') ? 'Đang lưu...' : 'Lưu Khuyến mãi' }}
            </button>
          </div>
          <p v-if="errorMap['save-auto-promo']" class="error-text">{{ errorMap['save-auto-promo'] }}</p>
        </div>
      </div>

      <!-- Modal Promotion Event -->
      <div v-if="promoEventModal.open" class="modal-overlay">
        <div class="modal-card modal-wide">
          <div class="modal-header">
            <h3>{{ promoEventModal.mode === 'create' ? '✨ Tạo Sự kiện Giảm giá Mới' : '📝 Cập nhật Sự kiện' }}</h3>
            <button class="btn-close" @click="promoEventModal.open = false">×</button>
          </div>
          
          <div class="modal-body">
            <div class="form-grid">
              <div class="form-group span-2">
                <label class="field-label">Tên sự kiện</label>
                <input v-model="promoEventModal.name" class="field-input-lux" placeholder="Ví dụ: Lễ hội Manga Hè 2026" />
              </div>
              
              <div class="form-group">
                <label class="field-label">Loại giảm giá</label>
                <select v-model="promoEventModal.discount_type" class="field-input-lux">
                  <option value="percent">Phần trăm (%)</option>
                  <option value="amount">Số tiền cố định (VNĐ)</option>
                </select>
              </div>
              
              <div class="form-group">
                <label class="field-label">Giá trị giảm</label>
                <input v-model.number="promoEventModal.discount_value" type="number" class="field-input-lux" />
              </div>
              
              <div class="form-group">
                <label class="field-label">Ngày bắt đầu</label>
                <input v-model="promoEventModal.start_date" type="datetime-local" class="field-input-lux" />
              </div>
              
              <div class="form-group">
                <label class="field-label">Ngày kết thúc</label>
                <input v-model="promoEventModal.end_date" type="datetime-local" class="field-input-lux" />
              </div>
              
              <div class="form-group span-2">
                <label class="field-label">Mô tả chương trình</label>
                <textarea v-model="promoEventModal.description" class="field-input-lux" rows="2" placeholder="Nội dung khuyến mãi..."></textarea>
              </div>
            </div>

            <label class="field-checkbox mt-4">
              <input v-model="promoEventModal.is_active" type="checkbox" />
              <span class="checkbox-custom"></span>
              Kích hoạt sự kiện ngay lập tức
            </label>
          </div>

          <div class="modal-actions">
            <button class="btn-ghost-lux" @click="promoEventModal.open = false">Hủy bỏ</button>
            <button class="btn-primary-lux" :disabled="isBusy('save-promo-event')" @click="savePromoEvent">
              {{ isBusy('save-promo-event') ? 'Đang lưu...' : 'Lưu sự kiện' }}
            </button>
          </div>
        </div>
      </div>

      <!-- Modal Quản lý Item trong Promotion -->
      <div v-if="promoItemsModal.open" class="modal-overlay">
        <div class="modal-card modal-wide">
          <div class="modal-header">
            <div class="header-titles">
              <h3>📚 Áp dụng chương trình: {{ promoItemsModal.eventName }}</h3>
              <p class="subtitle">Giảm giá cho các đầu truyện hoặc tập truyện cụ thể</p>
            </div>
            <button class="btn-close" @click="promoItemsModal.open = false">×</button>
          </div>

          <div class="modal-body">
            <div class="action-bar-mini">
              <div class="search-section">
                <div class="search-input-wrap">
                  <span class="material-icons">search</span>
                  <input 
                    v-model="searchTitleQuery" 
                    @input="searchTitles" 
                    placeholder="Tìm theo tên truyện hoặc ISBN..." 
                    class="input-search-items"
                  />
                  <div v-if="searchingTitles" class="spinner-small"></div>
                </div>
                
                <div v-if="searchResultTitles.length > 0" class="search-results-dropdown">
                  <div v-for="title in searchResultTitles" :key="title.id" class="search-item-row">
                    <div class="title-info-mini">
                      <span class="title-name">{{ title.name }}</span>
                      <span class="title-meta">ID: {{ title.id }} | {{ title.author }}</span>
                    </div>
                    <div class="item-actions-mini">
                      <button class="btn-mini-add" @click="selectTitleForPromo(title)">
                        <span class="material-icons">library_add</span>
                        Áp dụng cả bộ
                      </button>
                      <div class="vol-list-mini">
                        <span class="label">Tập lẻ:</span>
                        <button 
                          v-for="vol in title.volumes" 
                          :key="vol.id" 
                          class="btn-mini-vol"
                          @click="selectVolumeForPromo(vol)"
                          title="Áp dụng riêng tập này"
                        >
                          {{ vol.volume_number }}
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
                
                <div v-if="searchTitleQuery.length >= 2 && searchResultTitles.length === 0 && !searchingTitles" class="no-results-hint">
                  Không tìm thấy đầu truyện nào phù hợp
                </div>

                <!-- Danh sách tất cả truyện để chọn nhanh -->
                <div v-if="searchResultTitles.length === 0 && !searchingTitles" class="all-titles-suggestion">
                  <div class="suggestion-header">
                    <span>Gợi ý / Tất cả đầu truyện:</span>
                    <span v-if="loadingAllTitles" class="spinner-small"></span>
                  </div>
                  <div class="suggestion-grid">
                    <div v-for="title in allTitles" :key="title.id" class="suggestion-item">
                      <div class="s-info">
                        <span class="s-name">{{ title.name }}</span>
                        <span class="s-meta">ID: {{ title.id }}</span>
                      </div>
                      <div class="s-actions">
                        <button class="btn-s-add" @click="selectTitleForPromo(title)" title="Áp dụng cả bộ">
                          + Bộ
                        </button>
                        <div class="s-vols">
                          <button 
                            v-for="vol in title.volumes" 
                            :key="vol.id" 
                            class="btn-s-vol"
                            @click="selectVolumeForPromo(vol)"
                            :title="`Áp dụng tập ${vol.volume_number}`"
                          >
                            {{ vol.volume_number }}
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              
              <div class="manual-add-divider">
                <span>HOẶC NHẬP ID THỦ CÔNG</span>
              </div>

              <div class="add-item-form">
                <select v-model="newItem.target_type" class="select-lux-mini">
                  <option value="title">Theo Đầu truyện (Toàn bộ tập)</option>
                  <option value="volume">Theo Tập truyện lẻ (Chỉ 1 tập)</option>
                </select>
                <input v-model.number="newItem.target_id" type="number" placeholder="ID..." class="input-lux-mini" />
                <button class="btn-add-mini" @click="addItemToPromo" :disabled="isBusy('add-promo-item')">
                  <span class="material-icons">add</span>
                </button>
              </div>
            </div>

            <div class="items-list-scroll">
              <table class="table-mini">
                <thead>
                  <tr>
                    <th>Loại</th>
                    <th>ID Đối tượng</th>
                    <th>Tên đối tượng</th>
                    <th class="text-right">Hành động</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="item in promoItemsModal.items" :key="item.id">
                    <td>
                      <span :class="['type-pill', item.target_type]">
                        {{ item.target_type === 'title' ? 'Đầu truyện' : 'Tập đơn' }}
                      </span>
                    </td>
                    <td class="font-mono">#{{ item.target_id }}</td>
                    <td>{{ item.target_name || 'Đang xác định...' }}</td>
                    <td class="text-right">
                      <button class="btn-icon-del" @click="removeItemFromPromo(item.id)" :disabled="isBusy('remove-promo-item')">
                        <span class="material-icons">close</span>
                      </button>
                    </td>
                  </tr>
                  <tr v-if="promoItemsModal.items.length === 0">
                    <td colspan="4" class="text-center text-muted py-8">Chưa có đầu truyện nào được áp dụng giảm giá</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </Teleport>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue';
import { StoryHubApiError, fetchTitlesWithVolumes } from '../../../services/storyhubApi';
import type { AutoPromoItem, VoucherItem, TitleEntry } from '../../../services/storyhubApi';
import { useAdminApi } from '../../../composables/useAdminApi';

type ActionKey =
  | 'refresh-all'
  | 'load-vouchers'
  | 'load-auto-promos'
  | 'save-voucher'
  | 'delete-voucher'
  | 'save-auto-promo'
  | 'delete-auto-promo'
  | 'load-promo-events'
  | 'save-promo-event'
  | 'delete-promo-event'
  | 'load-promo-items'
  | 'add-promo-item'
  | 'remove-promo-item';

type KpiPayload = {
  primaryLabel: string;
  primaryValue: string;
  secondaryLabel: string;
  secondaryValue: string;
};

const props = defineProps<{ isActive: boolean }>();

const emit = defineEmits<{
  (e: 'notify', payload: { type: 'success' | 'error'; message: string }): void;
  (e: 'kpi', payload: KpiPayload): void;
}>();

const adminApi = useAdminApi();

const initialized = ref(false);
const leftOpen = ref(false);

const vouchers = ref<VoucherItem[]>([]);
const autoPromos = ref<AutoPromoItem[]>([]);
const promotionEvents = ref<any[]>([]);

const loadingMap = reactive<Record<ActionKey, boolean>>({
  'refresh-all': false,
  'load-vouchers': false,
  'load-auto-promos': false,
  'save-voucher': false,
  'delete-voucher': false,
  'save-auto-promo': false,
  'delete-auto-promo': false,
  'load-promo-events': false,
  'save-promo-event': false,
  'delete-promo-event': false,
  'load-promo-items': false,
  'add-promo-item': false,
  'remove-promo-item': false,
});

const errorMap = reactive<Record<ActionKey, string | null>>({
  'refresh-all': null,
  'load-vouchers': null,
  'load-auto-promos': null,
  'save-voucher': null,
  'delete-voucher': null,
  'save-auto-promo': null,
  'delete-auto-promo': null,
  'load-promo-events': null,
  'save-promo-event': null,
  'delete-promo-event': null,
  'load-promo-items': null,
  'add-promo-item': null,
  'remove-promo-item': null,
});

const voucherModal = reactive({
  open: false,
  mode: 'create' as 'create' | 'edit',
  id: null as number | null,
  code: '',
  voucher_type: 'percent' as 'percent' | 'amount',
  value: 10,
  min_spend: 0,
  max_discount: null as number | null,
  max_uses: null as number | null,
  end_at: '',
  is_active: true,
});

const autoPromoModal = reactive({
  open: false,
  mode: 'create' as 'create' | 'edit',
  id: null as number | null,
  name: '',
  day_of_week: 2,
  discount_percent: 10,
  is_active: true,
});

const promoEventModal = reactive({
  open: false,
  mode: 'create' as 'create' | 'edit',
  id: null as number | null,
  name: '',
  description: '',
  discount_type: 'percent' as 'percent' | 'amount',
  discount_value: 0,
  start_date: '',
  end_date: '',
  is_active: true,
});

const promoItemsModal = reactive({
  open: false,
  promoId: null as number | null,
  eventName: '',
  items: [] as any[],
});

const newItem = reactive({
  target_type: 'title' as 'title' | 'volume',
  target_id: null as number | null,
});

const searchTitleQuery = ref('');
const searchResultTitles = ref<TitleEntry[]>([]);
const searchingTitles = ref(false);

const allTitles = ref<TitleEntry[]>([]);
const loadingAllTitles = ref(false);

async function loadAllTitles() {
  if (allTitles.value.length > 0) return;
  loadingAllTitles.value = true;
  try {
    allTitles.value = await fetchTitlesWithVolumes();
  } catch (e) {
    console.error('Failed to load titles', e);
  } finally {
    loadingAllTitles.value = false;
  }
}

function selectTitleForPromo(title: TitleEntry) {
  newItem.target_type = 'title';
  newItem.target_id = title.id;
  addItemToPromo();
}

function selectVolumeForPromo(vol: any) {
  newItem.target_type = 'volume';
  newItem.target_id = vol.id;
  addItemToPromo();
}

async function searchTitles() {
  if (searchTitleQuery.value.trim().length < 2) {
    searchResultTitles.value = [];
    return;
  }
  searchingTitles.value = true;
  try {
    searchResultTitles.value = await fetchTitlesWithVolumes(searchTitleQuery.value.trim());
  } catch (e) {
    console.error('Search failed', e);
  } finally {
    searchingTitles.value = false;
  }
}

function selectTitleForPromo(title: TitleEntry) {
  newItem.target_type = 'title';
  newItem.target_id = title.id;
  addItemToPromo();
}

function selectVolumeForPromo(volume: any) {
  newItem.target_type = 'volume';
  newItem.target_id = volume.id;
  addItemToPromo();
}

const activeAutoPromoCount = computed(() => autoPromos.value.filter((promo) => promo.is_active).length);
const activePromoEventCount = computed(() => promotionEvents.value.filter((e) => e.is_active).length);

const deleteVoucherModal = reactive({
  open: false,
  id: null as number | null,
  code: '',
  reason: '',
});

const deleteAutoPromoModal = reactive({
  open: false,
  id: null as number | null,
  name: '',
  reason: '',
});

onMounted(() => {
  if (props.isActive) {
    initialized.value = true;
    void refreshAll();
  }
});

watch(
  () => props.isActive,
  (isActive) => {
    if (isActive && !initialized.value) {
      initialized.value = true;
      void refreshAll();
    }
  },
);

watch(
  () => [vouchers.value.length, autoPromos.value.length, activeAutoPromoCount.value],
  () => {
    emit('kpi', {
      primaryLabel: 'Voucher',
      primaryValue: String(vouchers.value.length),
      secondaryLabel: 'Khuyến mãi tự động',
      secondaryValue: String(activeAutoPromoCount.value),
    });
  },
  { immediate: true },
);

function isBusy(key: ActionKey) {
  return loadingMap[key];
}

function isReasonValid(reason: string) {
  return reason.trim().length >= 3;
}

function mapError(error: unknown) {
  if (error instanceof StoryHubApiError) {
    // Xử lý lỗi quyền truy cập rõ ràng
    if (error.status === 403) {
      return 'Không có quyền thực hiện thao tác này. Vui lòng đăng nhập lại với tài khoản chủ sở hữu.';
    }
    if (error.status === 401) {
      return 'Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.';
    }
    return error.message;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return 'Lỗi không xác định. Vui lòng thử lại.';
}

async function runAction<T>(key: ActionKey, work: () => Promise<T>) {
  loadingMap[key] = true;
  errorMap[key] = null;

  try {
    return await work();
  } catch (error) {
    const message = mapError(error);
    errorMap[key] = message;
    emit('notify', { type: 'error', message });
    return undefined;
  } finally {
    loadingMap[key] = false;
  }
}

async function refreshAll() {
  await runAction('refresh-all', async () => {
    await Promise.all([loadVouchers(), loadAutoPromotions(), loadPromotionEvents()]);
  });
}

async function loadVouchers() {
  await runAction('load-vouchers', async () => {
    vouchers.value = await adminApi.fetchVouchers();
  });
}

async function loadAutoPromotions() {
  await runAction('load-auto-promos', async () => {
    autoPromos.value = await adminApi.fetchAutoPromotions();
  });
}

async function loadPromotionEvents() {
  await runAction('load-promo-events', async () => {
    promotionEvents.value = await adminApi.fetchPromotionEvents();
  });
}

function openVoucherCreate() {
  voucherModal.mode = 'create';
  voucherModal.id = null;
  voucherModal.code = '';
  voucherModal.voucher_type = 'percent';
  voucherModal.value = 10;
  voucherModal.min_spend = 0;
  voucherModal.max_discount = null;
  voucherModal.max_uses = null;
  voucherModal.end_at = '';
  voucherModal.is_active = true;
  voucherModal.open = true;
}

function openVoucherEdit(voucher: VoucherItem) {
  voucherModal.mode = 'edit';
  voucherModal.id = voucher.id;
  voucherModal.code = voucher.code;
  voucherModal.voucher_type = voucher.voucher_type;
  voucherModal.value = voucher.value;
  voucherModal.min_spend = voucher.min_spend;
  voucherModal.max_discount = voucher.max_discount;
  voucherModal.max_uses = voucher.max_uses;
  voucherModal.end_at = voucher.end_at ?? '';
  voucherModal.is_active = voucher.is_active;
  voucherModal.open = true;
}

async function saveVoucher() {
  if (!voucherModal.code.trim() && voucherModal.mode === 'create') {
    emit('notify', { type: 'error', message: 'Mã Voucher là bắt buộc.' });
    return;
  }

  await runAction('save-voucher', async () => {
    if (voucherModal.mode === 'create') {
      await adminApi.createVoucher({
        code: voucherModal.code.trim(),
        voucher_type: voucherModal.voucher_type,
        value: voucherModal.value,
        min_spend: voucherModal.min_spend,
        max_discount: voucherModal.max_discount,
        max_uses: voucherModal.max_uses,
        end_at: voucherModal.end_at.trim() || null,
      });
    } else if (voucherModal.id !== null) {
      await adminApi.updateVoucher(voucherModal.id, {
        value: voucherModal.value,
        min_spend: voucherModal.min_spend,
        max_discount: voucherModal.max_discount,
        max_uses: voucherModal.max_uses,
        end_at: voucherModal.end_at.trim() || null,
        is_active: voucherModal.is_active,
      });
    }

    voucherModal.open = false;
    emit('notify', { type: 'success', message: 'Lưu Voucher thành công.' });
    await loadVouchers();
  });
}

async function toggleVoucher(voucher: VoucherItem) {
  await runAction('save-voucher', async () => {
    await adminApi.updateVoucher(voucher.id, { is_active: !voucher.is_active });
    emit('notify', { type: 'success', message: 'Đã thay đổi trạng thái Voucher.' });
    await loadVouchers();
  });
}

function openDeleteVoucherModal(voucher: VoucherItem) {
  deleteVoucherModal.id = voucher.id;
  deleteVoucherModal.code = voucher.code;
  deleteVoucherModal.reason = '';
  deleteVoucherModal.open = true;
}

async function submitDeleteVoucher() {
  if (deleteVoucherModal.id === null || !isReasonValid(deleteVoucherModal.reason)) {
    return;
  }

  await runAction('delete-voucher', async () => {
    await adminApi.deleteVoucher(deleteVoucherModal.id!);
    deleteVoucherModal.open = false;
    emit('notify', { type: 'success', message: 'Đã xóa Voucher thành công.' });
    await loadVouchers();
  });
}

// Hàm cũ removeVoucher thay bằng openDeleteVoucherModal – xem ở template
function removeVoucher(voucher: VoucherItem) {
  openDeleteVoucherModal(voucher);
}

function openAutoPromoCreate() {
  autoPromoModal.mode = 'create';
  autoPromoModal.id = null;
  autoPromoModal.name = '';
  autoPromoModal.day_of_week = 2;
  autoPromoModal.discount_percent = 10;
  autoPromoModal.is_active = true;
  autoPromoModal.open = true;
}

function openAutoPromoEdit(promo: AutoPromoItem) {
  autoPromoModal.mode = 'edit';
  autoPromoModal.id = promo.id;
  autoPromoModal.name = promo.name;
  autoPromoModal.day_of_week = promo.day_of_week;
  autoPromoModal.discount_percent = promo.discount_percent;
  autoPromoModal.is_active = promo.is_active;
  autoPromoModal.open = true;
}

async function saveAutoPromo() {
  if (!autoPromoModal.name.trim()) {
    emit('notify', { type: 'error', message: 'Tên chương trình là bắt buộc.' });
    return;
  }

  await runAction('save-auto-promo', async () => {
    if (autoPromoModal.mode === 'create') {
      await adminApi.createAutoPromotion({
        name: autoPromoModal.name.trim(),
        day_of_week: autoPromoModal.day_of_week,
        discount_percent: autoPromoModal.discount_percent,
      });
    } else if (autoPromoModal.id !== null) {
      await adminApi.updateAutoPromotion(autoPromoModal.id, {
        name: autoPromoModal.name.trim(),
        day_of_week: autoPromoModal.day_of_week,
        discount_percent: autoPromoModal.discount_percent,
        is_active: autoPromoModal.is_active,
      });
    }

    autoPromoModal.open = false;
    emit('notify', { type: 'success', message: 'Lưu khuyến mãi tự động thành công.' });
    await loadAutoPromotions();
  });
}

async function toggleAutoPromo(promo: AutoPromoItem) {
  await runAction('save-auto-promo', async () => {
    await adminApi.updateAutoPromotion(promo.id, { is_active: !promo.is_active });
    emit('notify', { type: 'success', message: 'Đã thay đổi trạng thái khuyến mãi.' });
    await loadAutoPromotions();
  });
}

function openDeleteAutoPromoModal(promo: AutoPromoItem) {
  deleteAutoPromoModal.id = promo.id;
  deleteAutoPromoModal.name = promo.name;
  deleteAutoPromoModal.reason = '';
  deleteAutoPromoModal.open = true;
}

async function submitDeleteAutoPromo() {
  if (deleteAutoPromoModal.id === null || !isReasonValid(deleteAutoPromoModal.reason)) {
    return;
  }

  await runAction('delete-auto-promo', async () => {
    await adminApi.deleteAutoPromotion(deleteAutoPromoModal.id!);
    deleteAutoPromoModal.open = false;
    emit('notify', { type: 'success', message: 'Đã xóa khuyến mãi tự động thành công.' });
    await loadAutoPromotions();
  });
}

// Hàm cũ removeAutoPromo thay bằng openDeleteAutoPromoModal – xem ở template
function removeAutoPromo(promo: AutoPromoItem) {
  openDeleteAutoPromoModal(promo);
}

function dayName(dayOfWeek: number) {
  const labels = ['CN', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7'];
  return labels[dayOfWeek] ?? String(dayOfWeek);
}

// Promotion Event Handlers
function openPromoEventCreate() {
  promoEventModal.mode = 'create';
  promoEventModal.id = null;
  promoEventModal.name = '';
  promoEventModal.description = '';
  promoEventModal.discount_type = 'percent';
  promoEventModal.discount_value = 10;
  promoEventModal.start_date = new Date().toISOString().slice(0, 16);
  promoEventModal.end_date = new Date(Date.now() + 7 * 86400000).toISOString().slice(0, 16);
  promoEventModal.is_active = true;
  promoEventModal.open = true;
}

function openPromoEventEdit(event: any) {
  promoEventModal.mode = 'edit';
  promoEventModal.id = event.id;
  promoEventModal.name = event.name;
  promoEventModal.description = event.description || '';
  promoEventModal.discount_type = event.discount_type;
  promoEventModal.discount_value = event.discount_value;
  promoEventModal.start_date = event.start_date.slice(0, 16);
  promoEventModal.end_date = event.end_date.slice(0, 16);
  promoEventModal.is_active = event.is_active;
  promoEventModal.open = true;
}

async function savePromoEvent() {
  if (!promoEventModal.name.trim()) {
    emit('notify', { type: 'error', message: 'Tên sự kiện là bắt buộc.' });
    return;
  }

  await runAction('save-promo-event', async () => {
    const isCreate = promoEventModal.mode === 'create';
    const payload: any = {
      name: promoEventModal.name.trim(),
      description: promoEventModal.description.trim(),
      discount_type: promoEventModal.discount_type,
      discount_value: promoEventModal.discount_value,
      start_date: promoEventModal.start_date,
      end_date: promoEventModal.end_date,
      is_active: promoEventModal.is_active,
    };

    let resp;
    if (isCreate) {
      resp = await adminApi.createPromotionEvent(payload);
    } else if (promoEventModal.id !== null) {
      resp = await adminApi.updatePromotionEvent(promoEventModal.id, payload);
    }

    promoEventModal.open = false;
    emit('notify', { type: 'success', message: 'Lưu sự kiện khuyến mãi thành công.' });
    await loadPromotionEvents();

    // Tự động mở quan lý item nếu là tạo mới
    if (isCreate && resp?.id) {
       const newEvent = promotionEvents.value.find(e => e.id === resp.id);
       if (newEvent) managePromoItems(newEvent);
    }
  });
}

async function removePromoEvent(event: any) {
  if (!confirm(`Bạn có chắc muốn xóa sự kiện "${event.name}"? Tât cả các đầu truyện đã áp dụng sẽ mất khuyến mãi này.`)) return;
  
  await runAction('delete-promo-event', async () => {
    await adminApi.deletePromotionEvent(event.id);
    emit('notify', { type: 'success', message: 'Đã xóa sự kiện.' });
    await loadPromotionEvents();
  });
}

async function managePromoItems(event: any) {
  promoItemsModal.promoId = event.id;
  promoItemsModal.eventName = event.name;
  promoItemsModal.items = [];
  promoItemsModal.open = true;
  loadAllTitles();
  await loadPromoItems();
}

async function loadPromoItems() {
  if (!promoItemsModal.promoId) return;
  await runAction('load-promo-items', async () => {
    promoItemsModal.items = await adminApi.fetchPromotionItems(promoItemsModal.promoId!);
  });
}

async function addItemToPromo() {
  if (!promoItemsModal.promoId || !newItem.target_id) return;
  
  await runAction('add-promo-item', async () => {
    await adminApi.addPromotionItem(promoItemsModal.promoId!, newItem.target_type, newItem.target_id!);
    emit('notify', { type: 'success', message: 'Đã thêm thành công.' });
    newItem.target_id = null;
    await loadPromoItems();
  });
}

async function removeItemFromPromo(itemId: number) {
  if (!promoItemsModal.promoId) return;
  
  await runAction('remove-promo-item', async () => {
    await adminApi.removePromotionItem(promoItemsModal.promoId!, itemId);
    emit('notify', { type: 'success', message: 'Đã gỡ tập/đầu truyện khỏi sự kiện.' });
    await loadPromoItems();
  });
}

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleString('vi-VN', { 
    day: '2-digit', month: '2-digit', year: 'numeric', 
    hour: '2-digit', minute: '2-digit' 
  });
}

function formatCurrency(val: number) {
  return new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(val);
}
</script>

<style scoped>
.tab-shell {
  width: 100%;
}

.mobile-toggle {
  display: none;
  margin-bottom: 12px;
  border: 1px solid #cbd5e1;
  background: #ffffff;
  color: #0f172a;
  border-radius: 12px;
  padding: 8px 12px;
  font-weight: 600;
}

.tab-split {
  display: grid;
  grid-template-columns: 320px minmax(0, 1fr);
  gap: 16px;
}

.left-panel,
.right-panel {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.panel-card {
  border: 1px solid #dbe4f0;
  background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
  border-radius: 16px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  
}
.panel-card h3 {
  margin-top: 0;
  margin-bottom: 20px;
  font-size: 1.2rem;
  color: #1e293b;
  font-weight: 700;
  display: flex;
  align-items: center;
}
.panel-card h3::before {
  content: "";
  width: 4px;
  height: 18px;
  background: #2563eb; /* Thanh màu xanh nhấn bên cạnh tiêu đề */
  margin-right: 10px;
  border-radius: 4px;
}
.card-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.card-head h3,
.panel-card h3 {
  margin: 0;
  font-size: 16px;
  color: #0f172a;
}

.field-label {
  display: block;
  font-size: 12px;
  font-weight: 700;
  color: #334155;
  margin: 8px 0 6px;
}

.field-input {
  width: 100%;
  border: 1px solid #cbd5e1;
  background: #ffffff;
  border-radius: 10px;
  padding: 9px 10px;
  font-size: 14px;
}

.field-checkbox {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 10px 0;
  font-size: 13px;
}

.stat-line {
  margin: 8px 0;
  color: #334155;
}

.btn-primary,
.btn-ghost,
.btn-row,
.btn-danger {
  border: none;
  border-radius: 10px;
  padding: 9px 12px;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
}

.btn-primary {
  padding: 10px 16px;
  border-radius: 10px;
  border: 1px solid #e2e8f0;
  background: #ffffff;
  color: #475569;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  flex: 1; /* Để các nút trải đều nếu bọc trong div flex */
}
.btn-primary:hover {
  background: #f8fafc;
  border-color: #cbd5e1;
  color: #2563eb;
}
.btn-primary-lux {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 14px 24px;
  border-radius: 12px;
  border: none;
  background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
  color: #ffffff;
  font-weight: 700;
  font-size: 15px;
  cursor: pointer;
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
  transition: all 0.3s ease;
}

.btn-primary-lux:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(37, 99, 235, 0.4);
  filter: brightness(1.1);
}

/* Nút Làm mới tất cả (Ghost Button) */


.btn-ghost:hover:not(:disabled) {
  color: #64748b;
}

.btn-ghost:disabled {
  cursor: wait;
  opacity: 0.6;
}

/* Thông báo lỗi */
.error-text {
  color: #ef4444;
  font-size: 13px;
  margin-top: 4px;
  font-style: italic;
}

.btn-ghost {
  background: transparent;
  border: none;
  color: #94a3b8;
  font-size: 13px;
  cursor: pointer;
  padding: 8px;
  align-self: flex-start; /* Nút này nhỏ, nên để sang một bên */
}

.btn-row {
  background: #dbeafe;
  color: #1e3a8a;
}

.btn-row.warn {
  background: #ffedd5;
  color: #9a3412;
}

.btn-row.danger {
  background: #fee2e2;
  color: #991b1b;
}

.btn-danger {
  background: #b91c1c;
  color: #ffffff;
}

.btn-primary:disabled,
.btn-ghost:disabled,
.btn-danger:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.table-wrap {
  overflow-x: auto;
}

.table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.table th,
.table td {
  border-bottom: 1px solid #e2e8f0;
  text-align: left;
  padding: 8px;
  vertical-align: top;
}

.table th {
  color: #334155;
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.03em;
}

.row-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.pill,
.pill-ok,
.pill-danger {
  display: inline-flex;
  align-items: center;
  border-radius: 999px;
  padding: 4px 10px;
  font-size: 11px;
  font-weight: 700;
}

.pill {
  background: #e2e8f0;
  color: #0f172a;
}

.pill-ok {
  background: #dcfce7;
  color: #166534;
}

.pill-danger {
  background: #fee2e2;
  color: #991b1b;
}

.error-text {
  margin-top: 8px;
  color: #b91c1c;
  font-size: 12px;
}

.modal-overlay {
  position: fixed;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(15, 23, 42, 0.55);
  z-index: 2000;
}

.modal-card {
  width: min(560px, calc(100vw - 24px));
  background: #ffffff;
  border-radius: 16px;
  border: 1px solid #dbe4f0;
  padding: 18px;
}

.modal-card h3 {
  margin: 0;
  color: #0f172a;
}

.modal-actions {
  margin-top: 14px;
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

@media (max-width: 1024px) {
  .mobile-toggle {
    display: inline-flex;
  }

  .tab-split {
    grid-template-columns: 1fr;
  }

  .left-panel {
    display: none;
  }

  .left-panel.open {
    display: flex;
  }
}

/* Premium Styles for Promotion Events */
.lux-border {
  border: 1px solid rgba(37, 99, 235, 0.2);
  box-shadow: 0 10px 25px -5px rgba(37, 99, 235, 0.1);
}

.btn-primary-lux {
  background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
  color: white;
  border: none;
  padding: 12px 20px;
  border-radius: 14px;
  font-weight: 700;
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  transition: 0.3s;
  box-shadow: 0 4px 6px -1px rgba(37, 99, 235, 0.2);
  width: 100%;
  justify-content: center;
  margin-bottom: 12px;
}
.btn-primary-lux:hover { transform: translateY(-1px); box-shadow: 0 10px 15px -3px rgba(37, 99, 235, 0.3); }

.table-lux th {
  background: #f1f5f9;
  color: #475569;
  font-weight: 800;
}

.event-name-cell .name { display: block; font-weight: 800; color: #0f172a; }
.event-name-cell .desc { display: block; font-size: 11px; color: #64748b; }

.discount-val {
  font-weight: 800;
  color: #2563eb;
  font-size: 1.1rem;
}

.date-range {
  font-size: 12px;
  color: #475569;
  display: flex;
  flex-direction: column;
}
.date-range .divider { color: #94a3b8; font-weight: bold; }

.modal-wide { width: 600px !important; }

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
}
.header-titles h3 { margin: 0; font-size: 1.25rem; font-weight: 800; }
.header-titles .subtitle { margin: 4px 0 0; font-size: 0.85rem; color: #64748b; }

.btn-close {
  background: none; border: none; font-size: 24px; color: #94a3b8; cursor: pointer;
}

.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}
.span-2 { grid-column: span 2; }

.field-input-lux {
  width: 100%;
  padding: 12px;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  background: #f8fafc;
  font-family: inherit;
  font-weight: 600;
  transition: 0.3s;
}
.field-input-lux:focus { border-color: #2563eb; background: white; outline: none; box-shadow: 0 0 0 4px rgba(37, 99, 235, 0.05); }

.action-bar-mini {
  background: #f1f5f9;
  padding: 12px;
  border-radius: 12px;
  margin-bottom: 16px;
}

.add-item-form {
  display: flex;
  gap: 8px;
}

.select-lux-mini, .input-lux-mini {
  padding: 8px 12px;
  border-radius: 8px;
  border: 1px solid #cbd5e1;
  font-size: 0.85rem;
  font-weight: 600;
}
.input-lux-mini { flex: 1; }

.btn-add-mini {
  background: #0f172a;
  color: white;
  border: none;
  padding: 8px 12px;
  border-radius: 8px;
  font-weight: 700;
  display: flex;
  align-items: center;
  gap: 4px;
  cursor: pointer;
}

.items-list-scroll {
  max-height: 300px;
  overflow-y: auto;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
}

.table-mini {
  width: 100%;
  border-collapse: collapse;
}
.table-mini th { background: #f8fafc; padding: 10px; font-size: 11px; text-transform: uppercase; color: #64748b; }
.table-mini td { padding: 10px; border-bottom: 1px solid #f1f5f9; font-size: 13px; }

.type-pill {
  padding: 2px 8px;
  border-radius: 6px;
  font-size: 10px;
  font-weight: 800;
  text-transform: uppercase;
}
.type-pill.title { background: #dcfce7; color: #166534; }
.type-pill.volume { background: #eff6ff; color: #1e40af; }

.btn-icon-del {
  background: none; border: none; color: #94a3b8; cursor: pointer; padding: 4px;
}
.btn-icon-del:hover { color: #ef4444; }

.btn-ghost-lux {
  background: #f1f5f9; color: #475569; border: none; padding: 12px 24px; border-radius: 14px; font-weight: 700; cursor: pointer;
}
.search-section {
  position: relative;
  flex: 1;
}

.search-input-wrap {
  display: flex;
  align-items: center;
  gap: 8px;
  background: #f1f5f9;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 8px 12px;
  transition: all 0.2s;
}

.search-input-wrap:focus-within {
  border-color: #2563eb;
  background: #ffffff;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
}

.input-search-items {
  border: none;
  background: transparent;
  width: 100%;
  font-size: 14px;
  outline: none;
}

.search-results-dropdown {
  position: absolute;
  top: calc(100% + 4px);
  left: 0;
  right: 0;
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
  z-index: 100;
  max-height: 300px;
  overflow-y: auto;
  padding: 6px;
}

.search-item-row {
  padding: 10px;
  border-bottom: 1px solid #f1f5f9;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.search-item-row:last-child {
  border-bottom: none;
}

.title-info-mini {
  display: flex;
  flex-direction: column;
}

.title-name {
  font-weight: 700;
  color: #0f172a;
}

.title-meta {
  font-size: 11px;
  color: #64748b;
}

.item-actions-mini {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.btn-mini-add {
  background: #2563eb;
  color: #ffffff;
  border: none;
  border-radius: 6px;
  padding: 4px 8px;
  font-size: 11px;
  font-weight: 700;
  display: flex;
  align-items: center;
  gap: 4px;
  cursor: pointer;
}

.vol-list-mini {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-wrap: wrap;
}

.vol-list-mini .label {
  font-size: 10px;
  color: #64748b;
  font-weight: 600;
}

.btn-mini-vol {
  background: #f1f5f9;
  border: 1px solid #e2e8f0;
  border-radius: 4px;
  padding: 2px 6px;
  font-size: 10px;
  font-weight: 700;
  cursor: pointer;
}

.btn-mini-vol:hover {
  background: #e2e8f0;
  border-color: #cbd5e1;
}

.manual-add-divider {
  display: flex;
  align-items: center;
  margin: 0 8px;
  font-size: 10px;
  color: #94a3b8;
  font-weight: 700;
  white-space: nowrap;
}

.manual-add-divider::before,
.manual-add-divider::after {
  content: "";
  height: 1px;
  flex: 1;
  background: #e2e8f0;
}

.manual-add-divider span {
  padding: 0 8px;
}

.no-results-hint {
  font-size: 12px;
  color: #94a3b8;
  padding: 12px;
  text-align: center;
}

.spinner-small {
  width: 14px;
  height: 14px;
  border: 2px solid #e2e8f0;
  border-top-color: #2563eb;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.all-titles-suggestion {
  margin-top: 16px;
  border-top: 1px dashed #e2e8f0;
  padding-top: 12px;
}

.suggestion-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 11px;
  font-weight: 700;
  color: #64748b;
  margin-bottom: 8px;
  text-transform: uppercase;
}

.suggestion-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 8px;
  max-height: 200px;
  overflow-y: auto;
  padding-right: 4px;
}

.suggestion-item {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 8px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.s-name {
  display: block;
  font-size: 13px;
  font-weight: 700;
  color: #1e293b;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.s-meta {
  font-size: 10px;
  color: #94a3b8;
}

.s-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  justify-content: space-between;
}

.btn-s-add {
  background: #f1f5f9;
  border: 1px solid #cbd5e1;
  border-radius: 4px;
  padding: 2px 6px;
  font-size: 10px;
  font-weight: 700;
  color: #2563eb;
  cursor: pointer;
}

.btn-s-add:hover {
  background: #2563eb;
  color: #ffffff;
  border-color: #2563eb;
}

.s-vols {
  display: flex;
  gap: 2px;
  flex-wrap: wrap;
}

.btn-s-vol {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 3px;
  padding: 1px 4px;
  font-size: 9px;
  font-weight: 600;
  cursor: pointer;
}

.btn-s-vol:hover {
  background: #f1f5f9;
}
</style>
