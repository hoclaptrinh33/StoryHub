<template>
  <DefaultLayout>
    <div class="checkout-page">
      <header class="page-header">
        <div>
          <h2 class="page-title">{{ checkoutModeTitle }}</h2>
          <p class="subtitle">{{ checkoutModeSubtitle }}</p>
        </div>
      </header>

      <transition name="fade">
        <div v-if="isScannerProcessing" class="state-banner scanning">
          <span class="material-icons">qr_code_scanner</span>
          Đang nhận mã scanner: <strong>{{ lastScannedCode || "..." }}</strong>
        </div>
      </transition>

      <transition name="fade">
        <div v-if="recoverableError" :class="['state-banner', recoverableError.type]">
          <span class="material-icons">error_outline</span>
          <div class="banner-copy">
            <strong>{{ recoverableError.title }}</strong>
            <span>{{ recoverableError.message }}</span>
          </div>
          <button class="btn-retry-banner" @click="retryCheckout">Thử lại</button>
        </div>
      </transition>

      <transition name="fade">
        <div v-if="hasRealtimeConflict" class="state-banner error">
          <span class="material-icons">sync_problem</span>
          <div class="banner-copy">
            <strong>Giỏ hàng có xung đột realtime</strong>
            <span>
              Một số item vừa đổi trạng thái ở quầy khác. Vui lòng xóa các dòng bị gạch đỏ hoặc
              quét lại mã để đồng bộ.
            </span>
          </div>
        </div>
      </transition>

      <section class="flow-guide">
        <div class="flow-step" :class="{ done: cart.length > 0 }">
          <span>1</span>
          Quét sách
        </div>
        <div
          class="flow-step"
          :class="{
            done: !hasRentalItems || !!customerObj,
            warning: hasRentalItems && !customerObj,
          }"
        >
          <span>2</span>
          Chọn khách (nếu thuê)
        </div>
        <div class="flow-step" :class="{ done: canSubmitCheckout }">
          <span>3</span>
          Xác nhận thanh toán
        </div>
      </section>

      <div v-if="isInitialLoading" class="screen-loading-state">
        <span class="material-icons spin">autorenew</span>
        Đang nạp dữ liệu quầy...
      </div>

      <div v-else class="sales-grid-layout">
        <section class="card-shell customer-column">
          <div class="card-header">
            <h3>
              <span class="material-icons">person</span>
              Smart Customer Bar
            </h3>
          </div>

          <div class="customer-smart-wrap" :class="{ alert: showCustomerWarning }">
            <label for="customer-smart-input">Khách hàng</label>
            <div class="smart-input-row">
              <span class="material-icons">manage_search</span>
              <input
                id="customer-smart-input"
                ref="customerSmartInputRef"
                v-model="customerQuery"
                type="text"
                placeholder="Quét thẻ / nhập SĐT / tên khách..."
                autocomplete="off"
                @focus="customerDropdownOpen = customerMatches.length > 0"
              />
              <button
                v-if="customerObj"
                type="button"
                class="chip-clear"
                @click="clearCustomerSelection"
                aria-label="Bỏ chọn khách"
              >
                <span class="material-icons">close</span>
              </button>
            </div>

            <div v-if="customerObj" class="customer-selected-chip">
              <span class="material-icons">verified</span>
              <strong>{{ customerObj.name }}</strong>
              <span>• {{ customerObj.phone }}</span>
            </div>

            <div
              v-if="customerDropdownOpen && customerMatches.length > 0 && !customerObj"
              class="customer-dropdown"
            >
              <button
                v-for="customer in customerMatches"
                :key="customer.id"
                type="button"
                class="customer-option"
                @click="selectCustomer(customer, false)"
              >
                <span class="material-icons">account_circle</span>
                <span class="text">
                  <strong>{{ customer.name }}</strong>
                  <small>{{ customer.phone }}</small>
                </span>
              </button>
            </div>

            <div
              v-if="canCreateQuickCustomer && !customerObj"
              class="quick-create-wrap"
            >
              <p>
                Không tìm thấy khách phù hợp.
                <strong>Tạo nhanh từ số {{ inferredPhone }}</strong>
              </p>
              <button
                class="btn-secondary"
                type="button"
                :disabled="isCreatingCustomer"
                @click="createAndSelectCustomer"
              >
                <span class="material-icons">person_add</span>
                {{ isCreatingCustomer ? "Đang tạo..." : "Tạo khách mới nhanh" }}
              </button>
            </div>

            <p v-if="showCustomerWarning" class="inline-warning">
              <span class="material-icons">warning_amber</span>
              Cần chọn khách để thuê sách.
            </p>
          </div>

          <transition name="slide-down">
            <div v-if="hasRentalItems" class="rental-requirement-banner">
              <div class="title-row">
                <span class="material-icons">rule</span>
                Có sách THUÊ trong giỏ, yêu cầu thông tin bổ sung
              </div>
              <div class="controls">
                <label>
                  Số ngày thuê
                  <input v-model.number="rentalDays" type="number" min="1" max="30" />
                </label>
                <p :class="{ warning: !customerObj }">
                  {{ customerObj ? "Khách hàng đã xác nhận" : "Khách hàng bắt buộc" }}
                </p>
              </div>
            </div>
          </transition>
        </section>

        <section class="card-shell cart-column">
          <div class="card-header cart-header">
            <h3>
              <span class="material-icons">shopping_bag</span>
              Giỏ hàng hỗn hợp
            </h3>
            <div class="manual-entry">
              <label for="manual-code-input">Nhập thủ công (F2)</label>
              <div class="manual-entry-row">
                <input
                  id="manual-code-input"
                  ref="manualBarcodeRef"
                  v-model="manualCode"
                  type="text"
                  placeholder="ISBN / RNT-..."
                  @keyup.enter="handleManualBarcode"
                />
                <button type="button" class="btn-primary" @click="handleManualBarcode">
                  <span class="material-icons">add</span>
                </button>
              </div>
            </div>
          </div>

          <div class="cart-table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Thông tin sách</th>
                  <th style="width: 120px">Loại GD</th>
                  <th style="width: 140px">Giá</th>
                  <th style="width: 70px"></th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="(item, index) in cart"
                  :key="item.id + item.code + index"
                  :class="{
                    active: selectedCartIndex === index,
                    'realtime-conflict': isCartItemInRealtimeConflict(item),
                  }"
                  @click="selectedCartIndex = index"
                >
                  <td>
                    <div class="product-cell">
                      <div class="book-icon">
                        <span class="material-icons">menu_book</span>
                      </div>
                      <div class="details">
                        <strong>{{ item.name }}</strong>
                        <small>Mã: {{ item.code }}</small>
                        <small v-if="isCartItemInRealtimeConflict(item)" class="conflict-note">
                          Trạng thái item đã thay đổi ở quầy khác.
                        </small>
                      </div>
                    </div>
                  </td>
                  <td>
                    <span :class="item.type === 'retail' ? 'tag-sale' : 'tag-rent'">
                      {{ item.type === "retail" ? "Mua" : "Thuê" }}
                    </span>
                  </td>
                  <td>{{ formatCurrency(item.price) }}</td>
                  <td>
                    <button class="btn-delete" @click.stop="removeCartItemAt(index)">
                      <span class="material-icons">delete_sweep</span>
                    </button>
                  </td>
                </tr>
                <tr v-if="cart.length === 0">
                  <td colspan="4">
                    <div class="empty-cart">
                      <span class="material-icons">add_shopping_cart</span>
                      <p>Giỏ hàng trống. Quét mã để bắt đầu phiên bán hoặc thuê.</p>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>

        <aside class="card-shell payment-column">
          <div class="card-header">
            <h3>
              <span class="material-icons">payments</span>
              Thanh toán
            </h3>
          </div>

          <div class="summary-box">
            <div class="line">
              <span>Tổng sách mua</span>
              <strong>{{ formatCurrency(salesTotal) }}</strong>
            </div>
            <div class="line">
              <span>Tổng phí thuê</span>
              <strong>{{ formatCurrency(rentalsTotal) }}</strong>
            </div>
            <div class="line">
              <span>Tiền cọc (thuê)</span>
              <strong>{{ formatCurrency(depositTotal) }}</strong>
            </div>
            <div class="divider"></div>
            <div class="line total">
              <span>Tổng khách đưa</span>
              <strong>{{ formatCurrency(total) }}</strong>
            </div>
          </div>

          <div class="payment-method-lux">
            <div class="payment-method-head">
              <p class="method-label">Hình thức thanh toán:</p>
              <label class="split-toggle">
                <input type="checkbox" v-model="isSplitPayment" />
                Tách thanh toán
              </label>
            </div>

            <div class="method-grid">
              <label class="method-btn" :class="{ active: paymentMethod === 'cash' }">
                <input type="radio" value="cash" v-model="paymentMethod" />
                <span class="material-icons">payments</span>
                Tiền mặt
              </label>
              <label class="method-btn" :class="{ active: paymentMethod === 'transfer' }">
                <input type="radio" value="transfer" v-model="paymentMethod" />
                <span class="material-icons">qr_code_2</span>
                Chuyển khoản
              </label>
            </div>

            <div v-if="isSplitPayment" class="split-payment-grid">
              <label class="split-input-row">
                <span>Tiền mặt</span>
                <input v-model.number="cashAmount" type="number" min="0" @input="normalizeSplitAmounts" />
              </label>
              <label class="split-input-row">
                <span>Chuyển khoản</span>
                <input v-model.number="transferAmount" type="number" min="0" @input="normalizeSplitAmounts" />
              </label>
              <p :class="['split-status', { error: !isSplitMatched }]">
                Tổng split: {{ formatCurrency(splitTotal) }}
                <span>• Chênh lệch: {{ formatCurrency(splitDelta) }}</span>
              </p>
            </div>
          </div>

          <div class="checkout-actions">
            <button
              class="btn-checkout"
              @click="confirmCheckout"
              :disabled="!canSubmitCheckout || isSubmittingCheckout"
              data-testid="pos-checkout-confirm"
            >
              {{ isSubmittingCheckout ? "ĐANG XỬ LÝ..." : "XUẤT HÓA ĐƠN" }}
              <span class="material-icons">arrow_forward</span>
            </button>
            <button class="btn-cancel" @click="clearCart">Hủy phiên</button>

            <div v-if="lastRentalContractId" class="rental-contract-note">
              <p>
                Mã hợp đồng thuê gần nhất: <strong>#{{ lastRentalContractId }}</strong>
              </p>
              <div class="rental-contract-actions">
                <button class="btn-secondary" type="button" @click="copyLatestContractId">
                  Copy mã HĐ
                </button>
                <button class="btn-inline-action" type="button" @click="openReturnForLatestContract">
                  Mở màn Trả sách
                </button>
              </div>
            </div>
          </div>
        </aside>
      </div>

      <BaseModal
        :is-open="isInvoiceModalOpen"
        title="Hóa đơn giao dịch"
        @close="closeInvoiceModal"
      >
        <div class="invoice-shell">
          <div v-if="isInvoiceLoading" class="invoice-loading-state">
            <span class="material-icons spin">autorenew</span>
            Đang tải dữ liệu hóa đơn...
          </div>

          <div v-else-if="invoiceLoadError" class="invoice-error-state">
            <span class="material-icons">error_outline</span>
            <p>{{ invoiceLoadError }}</p>
          </div>

          <div v-else-if="activeInvoice" class="invoice-content">
            <div class="invoice-header-grid">
              <div>
                <p class="invoice-label">Mã hóa đơn</p>
                <strong>{{ activeInvoice.invoice_key }}</strong>
              </div>
              <div>
                <p class="invoice-label">Loại giao dịch</p>
                <strong>{{ activeInvoice.transaction_type === "sale" ? "Bán" : "Thuê" }}</strong>
              </div>
              <div>
                <p class="invoice-label">Thời điểm</p>
                <strong>{{ formatInvoiceDate(activeInvoice.created_at) }}</strong>
              </div>
              <div>
                <p class="invoice-label">Trạng thái</p>
                <strong>{{ activeInvoice.status }}</strong>
              </div>
            </div>

            <div class="invoice-customer-row">
              <div>
                <p class="invoice-label">Khách hàng</p>
                <strong>{{ activeInvoice.customer_name }}</strong>
              </div>
              <div>
                <p class="invoice-label">Số điện thoại</p>
                <strong>{{ activeInvoice.customer_phone || "-" }}</strong>
              </div>
              <div v-if="activeInvoice.due_date">
                <p class="invoice-label">Hạn trả</p>
                <strong>{{ formatInvoiceDate(activeInvoice.due_date) }}</strong>
              </div>
            </div>

            <table class="invoice-line-table">
              <thead>
                <tr>
                  <th>Mã</th>
                  <th>Tên sách</th>
                  <th>Loại</th>
                  <th>SL</th>
                  <th>Đơn giá</th>
                  <th>Tiền cọc</th>
                  <th>Thành tiền</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(line, index) in activeInvoice.lines" :key="`${line.item_code}-${index}`">
                  <td>{{ line.item_code }}</td>
                  <td>{{ line.title }}</td>
                  <td>
                    <span :class="line.transaction_kind === 'sale' ? 'tag-sale' : 'tag-rent'">
                      {{ line.transaction_kind === "sale" ? "Bán" : "Thuê" }}
                    </span>
                  </td>
                  <td>{{ line.quantity }}</td>
                  <td>{{ formatCurrency(line.unit_price) }}</td>
                  <td>{{ formatCurrency(line.deposit) }}</td>
                  <td><strong>{{ formatCurrency(line.line_total) }}</strong></td>
                </tr>
              </tbody>
            </table>

            <div class="invoice-summary-grid">
              <div class="summary-line">
                <span>Tổng tiền bán:</span>
                <strong>{{ formatCurrency(activeInvoice.subtotal_sales) }}</strong>
              </div>
              <div class="summary-line">
                <span>Tổng tiền thuê:</span>
                <strong>{{ formatCurrency(activeInvoice.subtotal_rentals) }}</strong>
              </div>
              <div class="summary-line">
                <span>Tổng tiền cọc:</span>
                <strong>{{ formatCurrency(activeInvoice.total_deposit) }}</strong>
              </div>
              <div class="summary-line" v-if="activeInvoice.penalty_total > 0">
                <span>Phạt phát sinh:</span>
                <strong>{{ formatCurrency(activeInvoice.penalty_total) }}</strong>
              </div>
              <div class="summary-line total">
                <span>Tổng cộng:</span>
                <strong>{{ formatCurrency(activeInvoice.grand_total) }}</strong>
              </div>
            </div>

            <div v-if="activeInvoice.payments.length > 0" class="invoice-payments">
              <h4>Chi tiết thanh toán</h4>
              <ul>
                <li v-for="payment in activeInvoice.payments" :key="`${payment.method}-${payment.amount}`">
                  <span>{{ formatPaymentMethod(payment.method) }}</span>
                  <strong>{{ formatCurrency(payment.amount) }}</strong>
                </li>
              </ul>
            </div>
          </div>
        </div>

        <template #footer>
          <div class="invoice-footer-actions">
            <div v-if="checkoutInvoiceTargets.length > 1" class="invoice-carousel-actions">
              <button
                type="button"
                class="btn-secondary"
                :disabled="activeInvoiceIndex === 0 || isInvoiceLoading"
                @click="viewPreviousInvoice"
              >
                Hóa đơn trước
              </button>
              <span>{{ invoicePaginationLabel }}</span>
              <button
                type="button"
                class="btn-secondary"
                :disabled="activeInvoiceIndex >= checkoutInvoiceTargets.length - 1 || isInvoiceLoading"
                @click="viewNextInvoice"
              >
                Hóa đơn sau
              </button>
            </div>
            <button type="button" class="btn-cancel-modal" @click="closeInvoiceModal">Đóng</button>
          </div>
        </template>
      </BaseModal>

      <HotkeyBar :items="hotkeyItems" />
    </div>
  </DefaultLayout>
</template>

<script setup lang="ts">
import { computed, inject, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useWebSocket } from "../composables/useWebSocket";
import { useScannerStore } from "../stores/scanner";
import DefaultLayout from "../components/layout/defaultLayout.vue";
import BaseModal from "../components/layout/BaseModal.vue";
import HotkeyBar, { type HotkeyItem } from "../components/layout/HotkeyBar.vue";
import {
  StoryHubApiError,
  buildRequestId,
  fetchCheckoutInvoice,
  unifiedCheckout,
  fetchCustomers,
  fetchInventoryItems,
  upsertCustomer,
  autoCreateItem,
  type CheckoutInvoicePayload,
  type CheckoutInvoiceTransactionType,
  type CustomerListItem,
  type InventoryItemListItem,
  type PosSplitPaymentMethod,
} from "../services/storyhubApi";
import type { ItemStatusChangedEvent } from "../types/realtime";
import { playScanAudio } from "../utils/scanAudio";
import { toUiErrorMessage } from "../utils/backendErrorMessages";

interface RecoverableError {
  type: "error";
  title: string;
  message: string;
}

type CheckoutMode = "retail" | "rental" | "mixed";

interface HotkeyEventDetail {
  name?:
    | "f1"
    | "f2"
    | "f3"
    | "enter"
    | "escape"
    | "delete"
    | "arrow-up"
    | "arrow-down";
}

interface InvoiceTarget {
  transactionType: CheckoutInvoiceTransactionType;
  referenceId: string;
  label: string;
}

const addNotification = inject("addNotification") as (type: string, msg: string) => void;

const scannerStore = useScannerStore();
const route = useRoute();
const router = useRouter();
const ws = useWebSocket();

const isInitialLoading = ref(true);
const isSubmittingCheckout = ref(false);
const isScannerProcessing = ref(false);
const recoverableError = ref<RecoverableError | null>(null);

const customers = ref<CustomerListItem[]>([]);
const availableProducts = ref<InventoryItemListItem[]>([]);
const cart = ref<InventoryItemListItem[]>([]);
const selectedCartIndex = ref(-1);

const selectedCustomerId = ref<number | null>(null);
const customerQuery = ref("");
const customerDropdownOpen = ref(false);
const isCreatingCustomer = ref(false);
const isSyncingCustomerQuery = ref(false);
const hasShownRentalWarning = ref(false);

const isInvoiceModalOpen = ref(false);
const isInvoiceLoading = ref(false);
const invoiceLoadError = ref("");
const activeInvoice = ref<CheckoutInvoicePayload | null>(null);
const checkoutInvoiceTargets = ref<InvoiceTarget[]>([]);
const activeInvoiceIndex = ref(0);

const paymentMethod = ref<"cash" | "transfer">("cash");
const isSplitPayment = ref(false);
const cashAmount = ref(0);
const transferAmount = ref(0);
const rentalDays = ref(3);

const manualCode = ref("");
const manualBarcodeRef = ref<HTMLInputElement | null>(null);
const customerSmartInputRef = ref<HTMLInputElement | null>(null);
const lastRentalContractId = ref("");
const realtimeConflictCodes = ref<string[]>([]);
const lastScannedCode = computed(() => scannerStore.lastScannedCode);

const checkoutMode = computed<CheckoutMode>(() => {
  const rawMode = String(route.query.mode ?? "").toLowerCase();
  if (rawMode === "retail" || rawMode === "rental") {
    return rawMode;
  }
  return "mixed";
});

const isRetailMode = computed(() => checkoutMode.value === "retail");
const isRentalMode = computed(() => checkoutMode.value === "rental");

const checkoutModeTitle = computed(() => {
  if (isRetailMode.value) {
    return "Thu Ngân Bán Sách";
  }

  if (isRentalMode.value) {
    return "Thu Ngân Thuê Sách";
  }

  return "Thu Ngân Gộp (Bán và Thuê)";
});

const checkoutModeSubtitle = computed(() => {
  if (isRetailMode.value) {
    return "Chỉ nhận sách bán lẻ. Sách thuê sẽ được từ chối trong phiên này.";
  }

  if (isRentalMode.value) {
    return "Chỉ nhận SKU thuê, bắt buộc chọn khách và số ngày thuê.";
  }

  return "Scan-first cho quầy nhanh, nhập tay luôn sẵn sàng làm fallback.";
});

const hotkeyItems: HotkeyItem[] = [
  { key: "F1 / Enter", label: "Xác nhận" },
  { key: "F2", label: "Nhập thủ công" },
  { key: "F3", label: "Nhắc quy tắc mode" },
  { key: "ESC", label: "Về Command Hub" },
  { key: "↑ ↓", label: "Chọn dòng giỏ" },
  { key: "Delete", label: "Xóa dòng chọn" },
];

const computeDeposit = (rentPrice: number) => Math.max(rentPrice * 4, 10000);

const normalizeLookup = (value: string) => value.replace(/[^A-Za-z0-9]/g, "").toUpperCase();
const normalizePhone = (value: string) => value.replace(/\D/g, "");

const visibleProducts = computed(() => {
  let products = availableProducts.value;
    if (isRetailMode.value) products = products.filter(p => p.type === 'retail');
    if (isRentalMode.value) products = products.filter(p => p.type === 'rental');
    // Thêm lọc trạng thái (phòng ngừa dữ liệu cũ)
    return products.filter(p => p.status === 'available');
});

const customerObj = computed(() => {
  if (selectedCustomerId.value === null) {
    return null;
  }

  return customers.value.find((customer) => customer.id === selectedCustomerId.value) ?? null;
});

const customerMatches = computed(() => {
  if (customerObj.value) {
    return [];
  }

  const query = customerQuery.value.trim().toLowerCase();
  const queryDigits = normalizePhone(customerQuery.value);
  if (!query && !queryDigits) {
    return [];
  }

  return customers.value
    .filter((customer) => {
      const byName = query ? customer.name.toLowerCase().includes(query) : false;
      const byPhone = queryDigits ? customer.phone.includes(queryDigits) : false;
      return byName || byPhone;
    })
    .slice(0, 6);
});

const inferredPhone = computed(() => normalizePhone(customerQuery.value));

const canCreateQuickCustomer = computed(() => {
  return (
    !customerObj.value &&
    customerQuery.value.trim().length > 0 &&
    customerMatches.value.length === 0 &&
    inferredPhone.value.length >= 8
  );
});

const salesTotal = computed(() => cart.value.filter((item) => item.type === "retail").reduce((acc, item) => acc + item.price, 0));
const rentalsTotal = computed(() => cart.value.filter((item) => item.type === "rental").reduce((acc, item) => acc + item.price, 0));
const depositTotal = computed(() => cart.value.filter((item) => item.type === "rental").reduce((acc, item) => acc + computeDeposit(item.price), 0));

const total = computed(() => salesTotal.value + rentalsTotal.value + depositTotal.value);
const splitTotal = computed(() => cashAmount.value + transferAmount.value);
const splitDelta = computed(() => total.value - splitTotal.value);
const hasRentalItems = computed(() => cart.value.some((item) => item.type === "rental"));
const showCustomerWarning = computed(() => hasRentalItems.value && !customerObj.value);

const isSplitMatched = computed(() => {
  if (!isSplitPayment.value) {
    return true;
  }

  return splitDelta.value === 0;
});

const canSubmitCheckout = computed(() => {
  if (cart.value.length === 0) {
    return false;
  }
  if (hasRentalItems.value && !customerObj.value) {
    return false;
  }
  if (hasRentalItems.value && rentalDays.value < 1) {
    return false;
  }
  if (!isSplitMatched.value) {
    return false;
  }
  if (isInitialLoading.value) {
    return false;
  }
  if (hasRealtimeConflict.value) {
    return false;
  }
  return true;
});
const hasOutOfStock = computed(() =>
  cart.value.some(item => item.type === 'retail' && (item.stock_quantity ?? 0) <= 0)
);
// sau đó trong canSubmitCheckout thêm điều kiện:

const hasRealtimeConflict = computed(() => realtimeConflictCodes.value.length > 0);
const currentInvoiceTarget = computed(
  () => checkoutInvoiceTargets.value[activeInvoiceIndex.value] ?? null,
);
const invoicePaginationLabel = computed(() => {
  if (checkoutInvoiceTargets.value.length <= 1) {
    return "";
  }

  const current = activeInvoiceIndex.value + 1;
  const totalTargets = checkoutInvoiceTargets.value.length;
  const target = currentInvoiceTarget.value;
  if (!target) {
    return `${current}/${totalTargets}`;
  }

  return `${current}/${totalTargets} • ${target.label}`;
});

const formatCurrency = (value: number) =>
  new Intl.NumberFormat("vi-VN", {
    style: "currency",
    currency: "VND",
  }).format(value);

const formatInvoiceDate = (value: string) => {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat("vi-VN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
};

const formatPaymentMethod = (method: PosSplitPaymentMethod) => {
  if (method === "cash") {
    return "Tiền mặt";
  }
  if (method === "bank_transfer") {
    return "Chuyển khoản";
  }
  if (method === "card") {
    return "Thẻ";
  }
  return "Ví điện tử";
};

const clearRecoverableError = () => {
  recoverableError.value = null;
};

const selectCustomer = (customer: CustomerListItem, autoSelected: boolean) => {
  selectedCustomerId.value = customer.id;
  isSyncingCustomerQuery.value = true;
  customerQuery.value = `${customer.name} - ${customer.phone}`;
  customerDropdownOpen.value = false;

  queueMicrotask(() => {
    isSyncingCustomerQuery.value = false;
  });

  if (autoSelected) {
    addNotification("info", `Đã tự chọn khách: ${customer.name}`);
  }
};

const clearCustomerSelection = () => {
  selectedCustomerId.value = null;
  customerQuery.value = "";
  customerDropdownOpen.value = false;
};

const createAndSelectCustomer = async () => {
  if (!canCreateQuickCustomer.value) {
    return;
  }

  const phone = inferredPhone.value;
  const fallbackName = `Khách ${phone.slice(-4)}`;
  const nameFromQuery = customerQuery.value.trim().replace(/\d/g, "").trim();
  const name = nameFromQuery.length > 1 ? nameFromQuery : fallbackName;

  isCreatingCustomer.value = true;
  try {
    const created = await upsertCustomer(phone, {
      name,
      membership_level: "regular",
      request_id: buildRequestId("crm-upsert"),
    });

    const newCustomer: CustomerListItem = {
      id: Number(created.customer_id),
      name: created.name,
      phone: created.phone,
      membership_level: created.membership_level,
      deposit_balance: created.deposit_balance,
      debt: created.debt,
      blacklist_flag: created.blacklist_flag,
    };

    customers.value.unshift(newCustomer);
    selectCustomer(newCustomer, false);
    addNotification("success", `Đã tạo nhanh khách hàng: ${newCustomer.name}`);
  } catch (error) {
    const message = error instanceof Error ? error.message : "Không thể tạo khách mới";
    addNotification("error", message);
  } finally {
    isCreatingCustomer.value = false;
  }
};

const normalizeSplitAmounts = () => {
  cashAmount.value = Math.max(0, Math.round(cashAmount.value || 0));
  transferAmount.value = Math.max(0, Math.round(transferAmount.value || 0));
};

const syncSinglePaymentAmount = () => {
  if (isSplitPayment.value) {
    return;
  }

  if (paymentMethod.value === "transfer") {
    transferAmount.value = total.value;
    cashAmount.value = 0;
    return;
  }

  cashAmount.value = total.value;
  transferAmount.value = 0;
};

const toBackendPaymentMethod = (method: string): PosSplitPaymentMethod =>
  method === "transfer" ? "bank_transfer" : "cash";

const getSplitPaymentsPayload = () => {
  if (!isSplitPayment.value) {
    return [
      {
        method: toBackendPaymentMethod(paymentMethod.value),
        amount: total.value,
      },
    ];
  }

  return [
    { method: "cash" as const, amount: cashAmount.value },
    { method: "bank_transfer" as const, amount: transferAmount.value },
  ].filter((payment) => payment.amount > 0);
};

const setRecoverableError = (title: string, message: string) => {
  recoverableError.value = {
    type: "error",
    title,
    message,
  };
};

const findProductByBarcode = (rawCode: string): InventoryItemListItem | undefined => {
  const normalizedCode = normalizeLookup(rawCode);
  if (!normalizedCode) {
    return undefined;
  }

  return visibleProducts.value.find((product) => {
    return normalizeLookup(product.code) === normalizedCode || normalizeLookup(product.id) === normalizedCode;
  });
};

const isCartItemInRealtimeConflict = (item: InventoryItemListItem) => {
  return realtimeConflictCodes.value.includes(item.code);
};

const addRealtimeConflict = (itemCode: string) => {
  if (realtimeConflictCodes.value.includes(itemCode)) {
    return;
  }
  realtimeConflictCodes.value = [...realtimeConflictCodes.value, itemCode];
};

const removeRealtimeConflict = (itemCode: string) => {
  if (!realtimeConflictCodes.value.includes(itemCode)) {
    return;
  }

  realtimeConflictCodes.value = realtimeConflictCodes.value.filter((code) => code !== itemCode);
};

const handleRealtimeItemStatus = (event: ItemStatusChangedEvent) => {
  const normalizedEventItemId = normalizeLookup(event.item_id);
  if (!normalizedEventItemId) {
    return;
  }

  const matchedCartItem = cart.value.find((item) => {
    const normalizedItemId = normalizeLookup(item.id);
    const normalizedItemCode = normalizeLookup(item.code);
    return (
      normalizedItemId === normalizedEventItemId || normalizedItemCode === normalizedEventItemId
    );
  });

  if (!matchedCartItem) {
    return;
  }

  const conflictingStatuses = new Set(["sold", "rented", "lost", "unavailable"]);
  const nextStatus = event.new_status.toLowerCase();

  if (conflictingStatuses.has(nextStatus)) {
    const hadConflict = realtimeConflictCodes.value.includes(matchedCartItem.code);
    addRealtimeConflict(matchedCartItem.code);

    if (!hadConflict) {
      addNotification(
        "warning",
        `Item ${matchedCartItem.code} đã chuyển sang ${event.new_status}. Cần xử lý trước khi checkout.`,
      );
    }
    return;
  }

  removeRealtimeConflict(matchedCartItem.code);
};

const isProductAllowedInCurrentMode = (product: InventoryItemListItem) => {
  if (isRetailMode.value) {
    return product.type === "retail";
  }

  if (isRentalMode.value) {
    return product.type === "rental";
  }

  return true;
};

const getModeMismatchMessage = (productType: InventoryItemListItem["type"]) => {
  if (isRetailMode.value && productType === "rental") {
    return "Đang ở mode Bán sách: không thể thêm SKU thuê.";
  }

  if (isRentalMode.value && productType === "retail") {
    return "Đang ở mode Thuê sách: không thể thêm sách bán lẻ.";
  }

  return "Item không phù hợp với mode hiện tại.";
};

const ensureProduct = async (rawCode: string): Promise<InventoryItemListItem | undefined> => {
  const existing = findProductByBarcode(rawCode);
  if (existing) return existing;

  // Thử auto-create
  try {
    const result = await autoCreateItem({
      barcode: rawCode,
      request_id: buildRequestId('auto-create'),
    }, token.value);
    // Thêm sản phẩm mới vào danh sách availableProducts để lần sau quét nhanh
    availableProducts.value.push(result.item);
    return result.item;
  } catch (e) {
    // Nếu không tạo được, return undefined để hiển thị lỗi
    return undefined;
  }
};

const addToCart = async (product: InventoryItemListItem | undefined, source: "scanner" | "manual") => {
  if (!product) {
    playScanAudio('error');
    addNotification('error', 'Không thể thêm sản phẩm. Kiểm tra lại mã.');
    return;
  }
  
  if (!isProductAllowedInCurrentMode(product)) {
    playScanAudio("error");
    addNotification("warning", getModeMismatchMessage(product.type));
    return;
  }

  const exists = cart.value.some((item) => item.code === product.code);
  if (exists) {
    playScanAudio("error");
    addNotification("warning", "Mã này đã nằm trong giỏ.");
    return;
  }

  cart.value.push({ ...product });
  selectedCartIndex.value = cart.value.length - 1;

  clearRecoverableError();
  if (source === "scanner") {
    playScanAudio("success");
  }
};

const removeCartItemAt = (index: number) => {
  if (index < 0 || index >= cart.value.length) {
    return;
  }

  const removed = cart.value[index];
  cart.value.splice(index, 1);
  removeRealtimeConflict(removed.code);
  if (cart.value.length === 0) {
    selectedCartIndex.value = -1;
    return;
  }

  selectedCartIndex.value = Math.min(index, cart.value.length - 1);
};

const removeSelectedCartItem = () => {
  if (selectedCartIndex.value < 0 || selectedCartIndex.value >= cart.value.length) {
    return;
  }

  const removed = cart.value[selectedCartIndex.value];
  removeCartItemAt(selectedCartIndex.value);
  addNotification("info", `Đã xóa ${removed.name} khỏi giỏ.`);
};

const moveSelectedCart = (delta: number) => {
  if (cart.value.length === 0) {
    return;
  }

  if (selectedCartIndex.value < 0) {
    selectedCartIndex.value = 0;
    return;
  }

  const nextIndex = Math.min(cart.value.length - 1, Math.max(0, selectedCartIndex.value + delta));
  selectedCartIndex.value = nextIndex;
};

const handleManualBarcode = async () => {
  const code = manualCode.value.trim();
  if (!code) return;
  const matchedProduct = await ensureProduct(code);  // SỬA
  if (!matchedProduct) {
    playScanAudio("error");
    addNotification("error", `Không tìm thấy hoặc không thể tạo sản phẩm với mã: ${code}`);
  } else {
    addToCart(matchedProduct, "manual");
  }
  manualCode.value = "";
};

const clearCart = () => {
  cart.value = [];
  selectedCartIndex.value = -1;
  realtimeConflictCodes.value = [];
  clearRecoverableError();
};

const copyLatestContractId = async () => {
  if (!lastRentalContractId.value) {
    return;
  }

  try {
    await navigator.clipboard.writeText(lastRentalContractId.value);
    addNotification("success", `Đã copy mã hợp đồng #${lastRentalContractId.value}.`);
  } catch {
    addNotification("warning", "Không thể copy tự động, vui lòng copy thủ công.");
  }
};

const openReturnForLatestContract = () => {
  if (!lastRentalContractId.value) {
    return;
  }

  void router.push({
    path: "/hoan-tra",
    query: { scan: lastRentalContractId.value },
  });
};

const resetInvoiceModalState = () => {
  isInvoiceLoading.value = false;
  invoiceLoadError.value = "";
  activeInvoice.value = null;
  checkoutInvoiceTargets.value = [];
  activeInvoiceIndex.value = 0;
};

const closeInvoiceModal = () => {
  isInvoiceModalOpen.value = false;
  resetInvoiceModalState();
};

const buildInvoiceTargetsFromCheckoutResponse = (response: {
  order_id: string | null;
  rental_contract_id: string | null;
}): InvoiceTarget[] => {
  const targets: InvoiceTarget[] = [];

  if (response.order_id) {
    targets.push({
      transactionType: "sale",
      referenceId: response.order_id,
      label: `Đơn mua #${response.order_id}`,
    });
  }

  if (response.rental_contract_id) {
    targets.push({
      transactionType: "rental",
      referenceId: response.rental_contract_id,
      label: `HĐ thuê #${response.rental_contract_id}`,
    });
  }

  return targets;
};

const loadActiveInvoice = async () => {
  const target = currentInvoiceTarget.value;
  if (!target) {
    activeInvoice.value = null;
    invoiceLoadError.value = "Không tìm thấy dữ liệu hóa đơn để hiển thị.";
    return;
  }

  isInvoiceLoading.value = true;
  invoiceLoadError.value = "";

  try {
    activeInvoice.value = await fetchCheckoutInvoice(
      target.transactionType,
      target.referenceId,
    );
  } catch (error) {
    activeInvoice.value = null;
    invoiceLoadError.value =
      error instanceof Error ? error.message : "Không thể tải hóa đơn giao dịch.";
  } finally {
    isInvoiceLoading.value = false;
  }
};

const openInvoiceModalWithTargets = (targets: InvoiceTarget[]) => {
  if (targets.length === 0) {
    return;
  }

  checkoutInvoiceTargets.value = targets;
  activeInvoiceIndex.value = 0;
  isInvoiceModalOpen.value = true;
  void loadActiveInvoice();
};

const viewNextInvoice = () => {
  if (activeInvoiceIndex.value >= checkoutInvoiceTargets.value.length - 1) {
    return;
  }

  activeInvoiceIndex.value += 1;
  void loadActiveInvoice();
};

const viewPreviousInvoice = () => {
  if (activeInvoiceIndex.value <= 0) {
    return;
  }

  activeInvoiceIndex.value -= 1;
  void loadActiveInvoice();
};

const confirmCheckout = async () => {
  if (!canSubmitCheckout.value) {
    setRecoverableError(
      "Thiếu thông tin phiên giao dịch",
      "Kiểm tra giỏ hàng, khách thuê hoặc số tiền split trước khi xuất hóa đơn.",
    );
    addNotification("warning", "Kiểm tra lại giỏ hàng, thông tin khách và thanh toán.");
    return;
  }

  isSubmittingCheckout.value = true;
  clearRecoverableError();

  try {
    const response = await unifiedCheckout({
      customer_id: selectedCustomerId.value,
      scanned_codes: cart.value.map((item) => item.code),
      discount_type: "none",
      discount_value: 0,
      split_payments: getSplitPaymentsPayload(),
      rental_days: Math.max(1, rentalDays.value),
      request_id: buildRequestId("checkout-unified"),
    });

    let successMessage = "Thanh toán thành công. ";
    if (response.order_id) {
      successMessage += `Đơn mua #${response.order_id}. `;
    }
    if (response.rental_contract_id) {
      successMessage += `HĐ thuê #${response.rental_contract_id}. `;
    }
    successMessage += `Tổng thu: ${formatCurrency(response.grand_total)}.`;

    lastRentalContractId.value = response.rental_contract_id ?? "";

    addNotification("success", successMessage);
    openInvoiceModalWithTargets(buildInvoiceTargetsFromCheckoutResponse(response));
    clearCart();
    clearCustomerSelection();
    availableProducts.value = await fetchInventoryItems();
  } catch (error) {
    if (error instanceof StoryHubApiError) {
      const uiMessage = toUiErrorMessage(error.code, error.message);
      setRecoverableError("Backend từ chối giao dịch", uiMessage);
      addNotification("error", uiMessage);
    } else {
      setRecoverableError("Không thể kết nối", "Lỗi kết nối ngoài dự kiến. Vui lòng thử lại.");
      addNotification("error", "Lỗi kết nối.");
    }
  } finally {
    isSubmittingCheckout.value = false;
  }
};

const retryCheckout = () => {
  if (!isSubmittingCheckout.value) {
    void confirmCheckout();
  }
};

const handleGlobalHotkey = (event: Event) => {
  const customEvent = event as CustomEvent<HotkeyEventDetail>;
  const hotkey = customEvent.detail?.name;

  if (hotkey === "f1" || hotkey === "enter") {
    void confirmCheckout();
    return;
  }

  if (hotkey === "f2") {
    manualBarcodeRef.value?.focus();
    return;
  }

  if (hotkey === "f3") {
    if (isRetailMode.value) {
      addNotification("info", "Mode Bán sách: chỉ nhận item bán lẻ (retail).");
      return;
    }

    if (isRentalMode.value) {
      addNotification("info", "Mode Thuê sách: chỉ nhận SKU thuê và cần chọn khách.");
      return;
    }

    addNotification("info", "Mode gộp: nhận cả bán và thuê trong cùng phiên.");
    return;
  }

  if (hotkey === "delete") {
    removeSelectedCartItem();
    return;
  }

  if (hotkey === "arrow-up") {
    moveSelectedCart(-1);
    return;
  }

  if (hotkey === "arrow-down") {
    moveSelectedCart(1);
    return;
  }

  if (hotkey === "escape") {
    if (isInvoiceModalOpen.value) {
      closeInvoiceModal();
      return;
    }

    clearCart();
  }
};

const consumePendingScans = () => {
  const queuedItems = scannerStore.consumePendingCheckoutItems();

  if (queuedItems.length === 0) {
    if (!scannerStore.lastScannedItem) {
      return;
    }

    addToCart(scannerStore.lastScannedItem, "scanner");
    scannerStore.lastScannedItem = null;
    scannerStore.lastScannedCode = "";
    return;
  }

  queuedItems.forEach((item) => {
    addToCart(item, "scanner");
  });

  scannerStore.lastScannedItem = null;
  scannerStore.lastScannedCode = "";
};

let stopScannerWatch: (() => void) | null = null;
let stopRealtimeWatch: (() => void) | null = null;

watch([total, paymentMethod, isSplitPayment], () => syncSinglePaymentAmount(), {
  immediate: true,
});

watch(customerQuery, (value) => {
  if (isSyncingCustomerQuery.value) {
    return;
  }

  if (selectedCustomerId.value !== null) {
    selectedCustomerId.value = null;
  }

  const trimmed = value.trim();
  if (!trimmed) {
    customerDropdownOpen.value = false;
    return;
  }

  customerDropdownOpen.value = true;
  if (customerMatches.value.length === 1 && trimmed.length >= 4) {
    selectCustomer(customerMatches.value[0], true);
  }
});

watch(
  () => hasRentalItems.value,
  (hasRental) => {
    if (!hasRental) {
      hasShownRentalWarning.value = false;
      return;
    }

    if (!customerObj.value && !hasShownRentalWarning.value) {
      addNotification("warning", "Giỏ có sách thuê: cần chọn khách hàng trước khi xuất hóa đơn.");
      hasShownRentalWarning.value = true;
    }
  },
);

watch(
  () => cart.value.map((item) => item.id),
  (itemIds) => {
    ws.setTrackedItems(itemIds);
  },
  { immediate: true },
);

onMounted(async () => {
  ws.connect("cashier-demo", "main");
  ws.subscribe(["item_status_changed"]);
  stopRealtimeWatch = watch(
    () => ws.latestItemStatusEvent.value,
    (event) => {
      if (!event) {
        return;
      }
      handleRealtimeItemStatus(event);
    },
    { immediate: true },
  );

  try {
    const [customerData, inventoryData] = await Promise.all([fetchCustomers(), fetchInventoryItems()]);
    customers.value = customerData;
    availableProducts.value = inventoryData;
  } catch {
    addNotification("error", "Lỗi nạp dữ liệu ban đầu.");
  } finally {
    isInitialLoading.value = false;
  }

  stopScannerWatch = watch(
    () => scannerStore.scanEventCounter,
    () => {
      isScannerProcessing.value = true;
      setTimeout(() => {
        isScannerProcessing.value = false;
      }, 500);
      consumePendingScans();
    },
    { immediate: true },
  );

  window.addEventListener("storyhub:hotkey", handleGlobalHotkey as EventListener);

  if (route.query.focus === "customer" || route.query.mode === "rental") {
    setTimeout(() => {
      customerSmartInputRef.value?.focus();
    }, 120);
  } else if (route.query.manual === "1") {
    setTimeout(() => {
      manualBarcodeRef.value?.focus();
    }, 120);
  }

  if (route.query.mode === "rental") {
    addNotification("info", "Đang ở mode Thuê sách. Chỉ nhận SKU thuê và cần chọn khách.");
  }

  if (route.query.mode === "retail") {
    addNotification("info", "Đang ở mode Bán sách. Chỉ nhận item bán lẻ.");
  }
});

onBeforeUnmount(() => {
  ws.unsubscribe(["item_status_changed"]);
  ws.setTrackedItems([]);

  if (stopRealtimeWatch) {
    stopRealtimeWatch();
    stopRealtimeWatch = null;
  }

  window.removeEventListener("storyhub:hotkey", handleGlobalHotkey as EventListener);
  if (stopScannerWatch) {
    stopScannerWatch();
    stopScannerWatch = null;
  }
});
</script>

<style scoped>
@import url("https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap");

.checkout-page {
  padding: 28px;
  min-height: 100vh;
  font-family: "Plus Jakarta Sans", sans-serif;
  background:
    radial-gradient(circle at 8% 4%, rgba(56, 189, 248, 0.12), transparent 28%),
    radial-gradient(circle at 86% 88%, rgba(34, 197, 94, 0.1), transparent 26%),
    #f8fafc;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.page-title {
  margin: 0;
  font-size: 2rem;
  color: #0f172a;
  letter-spacing: -0.03em;
}

.subtitle {
  margin: 4px 0 0;
  color: #475569;
}

.flow-guide {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
  margin-bottom: 14px;
}

.flow-step {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  border-radius: 12px;
  padding: 10px 12px;
  background: #f1f5f9;
  border: 1px solid #cbd5e1;
  color: #475569;
  font-weight: 700;
}

.flow-step span {
  width: 24px;
  height: 24px;
  display: grid;
  place-items: center;
  border-radius: 999px;
  background: white;
  font-size: 0.8rem;
}

.flow-step.done {
  border-color: #86efac;
  background: #ecfdf3;
  color: #166534;
}

.flow-step.warning {
  border-color: #facc15;
  background: #fefce8;
  color: #854d0e;
}

.state-banner {
  border-radius: 12px;
  border: 1px solid;
  padding: 10px 12px;
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 14px;
}

.state-banner.scanning {
  border-color: #7dd3fc;
  background: #f0f9ff;
  color: #0c4a6e;
}

.state-banner.error {
  border-color: #fecaca;
  background: #fff1f2;
  color: #9f1239;
}

tr.realtime-conflict {
  background: #fff1f2;
}

tr.realtime-conflict .details strong {
  color: #9f1239;
  text-decoration: line-through;
}

.conflict-note {
  color: #b91c1c;
  font-weight: 700;
}

.banner-copy {
  display: flex;
  flex-direction: column;
  gap: 2px;
  flex: 1;
}

.btn-retry-banner {
  border: none;
  border-radius: 10px;
  padding: 8px 12px;
  background: #0f172a;
  color: white;
  font-weight: 700;
  cursor: pointer;
}

.screen-loading-state {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  border: 1px solid #e2e8f0;
  border-radius: 16px;
  background: white;
  color: #334155;
  padding: 18px;
  font-weight: 700;
}

.sales-grid-layout {
  display: grid;
  grid-template-columns: 370px 1fr 380px;
  gap: 16px;
  align-items: start;
}

.card-shell {
  border-radius: 22px;
  border: 1px solid #e2e8f0;
  background: rgba(255, 255, 255, 0.95);
  box-shadow: 0 20px 36px -26px rgba(15, 23, 42, 0.28);
  overflow: hidden;
}

.card-header {
  padding: 14px 16px;
  border-bottom: 1px solid #e2e8f0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.card-header h3 {
  margin: 0;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: #0f172a;
  font-size: 1rem;
}

.customer-smart-wrap {
  position: relative;
  padding: 14px;
}

.customer-smart-wrap label {
  display: block;
  font-size: 0.86rem;
  color: #475569;
  margin-bottom: 7px;
  font-weight: 700;
}

.smart-input-row {
  border: 1.5px solid #cbd5e1;
  border-radius: 12px;
  background: white;
  padding: 8px 10px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.smart-input-row input {
  border: none;
  outline: none;
  width: 100%;
  font-family: inherit;
  font-weight: 600;
}

.chip-clear {
  width: 28px;
  height: 28px;
  border: none;
  border-radius: 999px;
  background: #f1f5f9;
  color: #475569;
  cursor: pointer;
  display: grid;
  place-items: center;
}

.customer-smart-wrap.alert .smart-input-row {
  border-color: #facc15;
  box-shadow: 0 0 0 3px rgba(250, 204, 21, 0.2);
}

.customer-selected-chip {
  margin-top: 10px;
  border-radius: 10px;
  border: 1px solid #bfdbfe;
  background: #eff6ff;
  color: #1d4ed8;
  padding: 8px 10px;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 0.9rem;
}

.customer-dropdown {
  position: absolute;
  left: 14px;
  right: 14px;
  top: 96px;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  background: white;
  box-shadow: 0 16px 24px -20px rgba(15, 23, 42, 0.42);
  overflow: hidden;
  z-index: 18;
}

.customer-option {
  width: 100%;
  border: none;
  background: white;
  cursor: pointer;
  padding: 10px;
  display: flex;
  align-items: center;
  gap: 8px;
  text-align: left;
}

.customer-option:hover {
  background: #f8fafc;
}

.customer-option .text {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.customer-option small {
  color: #64748b;
}

.quick-create-wrap {
  margin-top: 10px;
  border-radius: 10px;
  border: 1px dashed #93c5fd;
  background: #f0f9ff;
  padding: 10px;
}

.quick-create-wrap p {
  margin: 0 0 8px;
  color: #0c4a6e;
  font-size: 0.84rem;
}

.inline-warning {
  margin: 10px 0 0;
  color: #92400e;
  font-weight: 700;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.rental-requirement-banner {
  margin-top: 14px;
  border: 1px solid #fdba74;
  background: #fff7ed;
  border-radius: 12px;
  padding: 10px;
}

.rental-requirement-banner .title-row {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-weight: 800;
  color: #9a3412;
  margin-bottom: 10px;
}

.rental-requirement-banner .controls {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.rental-requirement-banner label {
  font-size: 0.84rem;
  color: #9a3412;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.rental-requirement-banner input {
  width: 96px;
  padding: 8px 10px;
  border-radius: 10px;
  border: 1px solid #fdba74;
}

.rental-requirement-banner p {
  margin: 0;
  font-size: 0.86rem;
  font-weight: 700;
  color: #166534;
}

.rental-requirement-banner p.warning {
  color: #b45309;
}

.cart-header {
  align-items: flex-start;
}

.manual-entry {
  min-width: 245px;
}

.manual-entry label {
  display: block;
  font-size: 0.76rem;
  font-weight: 800;
  color: #475569;
  margin-bottom: 6px;
  text-transform: uppercase;
}

.manual-entry-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.manual-entry-row input {
  width: 100%;
  border-radius: 10px;
  border: 1px solid #cbd5e1;
  padding: 8px 10px;
  font-family: inherit;
}

.cart-table-wrap table {
  width: 100%;
  border-collapse: collapse;
}

.cart-table-wrap th,
.cart-table-wrap td {
  padding: 12px;
  border-bottom: 1px solid #f1f5f9;
}

.cart-table-wrap tr.active {
  background: #eff6ff;
}

.product-cell {
  display: flex;
  align-items: center;
  gap: 10px;
}

.book-icon {
  width: 40px;
  height: 40px;
  display: grid;
  place-items: center;
  border-radius: 10px;
  background: #eff6ff;
  color: #2563eb;
}

.details {
  display: flex;
  flex-direction: column;
}

.details small {
  color: #64748b;
}

.tag-sale,
.tag-rent {
  padding: 4px 8px;
  border-radius: 999px;
  font-size: 0.74rem;
  font-weight: 800;
}

.tag-sale {
  color: #166534;
  background: #dcfce7;
}

.tag-rent {
  color: #92400e;
  background: #fef3c7;
}

.btn-delete {
  width: 34px;
  height: 34px;
  border: none;
  border-radius: 10px;
  background: #fee2e2;
  color: #dc2626;
  cursor: pointer;
  display: grid;
  place-items: center;
}

.empty-cart {
  padding: 34px 12px;
  text-align: center;
  color: #94a3b8;
}

.empty-cart .material-icons {
  font-size: 2.3rem;
}

.payment-column {
  position: sticky;
  top: 18px;
}

.summary-box {
  padding: 14px;
  border-bottom: 1px solid #e2e8f0;
  background: #f8fafc;
}

.summary-box .line {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 5px 0;
  color: #334155;
}

.summary-box .line.total {
  font-size: 1.07rem;
  font-weight: 800;
  color: #0f172a;
}

.divider {
  border-top: 1px dashed #cbd5e1;
  margin: 8px 0;
}

.payment-method-lux {
  padding: 14px;
}

.payment-method-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.method-label {
  margin: 0;
  font-weight: 700;
}

.split-toggle {
  font-size: 0.85rem;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
}

.method-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
  margin-top: 10px;
}

.method-btn {
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 11px;
  font-weight: 700;
  color: #64748b;
  display: flex;
  flex-direction: column;
  gap: 6px;
  align-items: center;
  cursor: pointer;
}

.method-btn input {
  display: none;
}

.method-btn.active {
  border-color: #93c5fd;
  background: #eff6ff;
  color: #1e3a8a;
}

.split-payment-grid {
  margin-top: 10px;
  border-radius: 10px;
  border: 1px solid #e2e8f0;
  background: #fafafa;
  padding: 10px;
}

.split-input-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.split-input-row input {
  width: 120px;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  padding: 7px;
  text-align: right;
}

.split-status {
  margin: 0;
  text-align: right;
  font-size: 0.8rem;
  color: #334155;
}

.split-status.error {
  color: #dc2626;
}

.checkout-actions {
  padding: 14px;
  border-top: 1px solid #e2e8f0;
}

.rental-contract-note {
  margin-top: 10px;
  border: 1px dashed #bfdbfe;
  border-radius: 10px;
  background: #eff6ff;
  padding: 10px;
}

.rental-contract-note p {
  margin: 0;
  color: #1e3a8a;
  font-weight: 700;
}

.rental-contract-actions {
  margin-top: 8px;
  display: flex;
  gap: 8px;
}

.btn-inline-action {
  border: none;
  border-radius: 10px;
  padding: 9px 12px;
  font-weight: 700;
  cursor: pointer;
  background: #dbeafe;
  color: #1d4ed8;
}

.btn-checkout {
  width: 100%;
  border: none;
  border-radius: 12px;
  background: #16a34a;
  color: white;
  font-weight: 800;
  padding: 13px;
  display: inline-flex;
  justify-content: center;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.btn-checkout:disabled {
  cursor: not-allowed;
  opacity: 0.7;
}

.btn-cancel,
.btn-secondary,
.btn-primary {
  border: none;
  border-radius: 10px;
  padding: 9px 12px;
  font-weight: 700;
  cursor: pointer;
}

.btn-cancel {
  width: 100%;
  margin-top: 8px;
  background: #f1f5f9;
  color: #475569;
}

.btn-secondary {
  background: #e0f2fe;
  color: #075985;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.btn-secondary:disabled {
  opacity: 0.7;
}

.btn-primary {
  background: #2563eb;
  color: white;
  display: grid;
  place-items: center;
}

.invoice-shell {
  min-height: 220px;
}

.invoice-loading-state,
.invoice-error-state {
  min-height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  color: #334155;
  font-weight: 700;
}

.invoice-error-state {
  color: #b91c1c;
}

.invoice-error-state p {
  margin: 0;
}

.invoice-content {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.invoice-header-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
  padding: 12px;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  background: #f8fafc;
}

.invoice-customer-row {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
  padding: 0 2px;
}

.invoice-label {
  margin: 0 0 4px;
  font-size: 0.78rem;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  font-weight: 700;
}

.invoice-line-table {
  width: 100%;
  border-collapse: collapse;
}

.invoice-line-table th,
.invoice-line-table td {
  border-bottom: 1px solid #f1f5f9;
  padding: 9px;
  text-align: left;
}

.invoice-line-table th {
  background: #f8fafc;
  color: #334155;
  font-size: 0.8rem;
  text-transform: uppercase;
}

.invoice-summary-grid {
  border: 1px dashed #cbd5e1;
  border-radius: 12px;
  padding: 10px 12px;
  display: grid;
  gap: 8px;
}

.summary-line {
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: #334155;
}

.summary-line.total {
  color: #0f172a;
  font-size: 1.06rem;
  padding-top: 6px;
  border-top: 1px dashed #cbd5e1;
}

.invoice-payments {
  border-radius: 12px;
  border: 1px solid #dbeafe;
  background: #eff6ff;
  padding: 10px 12px;
}

.invoice-payments h4 {
  margin: 0 0 8px;
  font-size: 0.95rem;
  color: #1e3a8a;
}

.invoice-payments ul {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  gap: 6px;
}

.invoice-payments li {
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: #1e3a8a;
}

.invoice-footer-actions {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.invoice-carousel-actions {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: #475569;
  font-size: 0.86rem;
}

.btn-cancel-modal {
  border: none;
  border-radius: 10px;
  padding: 8px 14px;
  background: #0f172a;
  color: white;
  font-weight: 700;
  cursor: pointer;
}

.spin {
  animation: spin 1s linear infinite;
}

.fade-enter-active,
.fade-leave-active,
.slide-down-enter-active,
.slide-down-leave-active {
  transition: all 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}

.slide-down-enter-from,
.slide-down-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

@media (max-width: 1240px) {
  .sales-grid-layout {
    grid-template-columns: 1fr;
  }

  .payment-column {
    position: static;
  }

  .flow-guide {
    grid-template-columns: 1fr;
  }

  .invoice-header-grid,
  .invoice-customer-row {
    grid-template-columns: 1fr 1fr;
  }
}

@media (max-width: 768px) {
  .checkout-page {
    padding: 16px;
  }

  .manual-entry {
    min-width: 0;
  }

  .card-header {
    flex-direction: column;
    align-items: stretch;
  }

  .invoice-header-grid,
  .invoice-customer-row {
    grid-template-columns: 1fr;
  }

  .invoice-footer-actions {
    flex-direction: column;
    align-items: stretch;
  }

  .invoice-carousel-actions {
    justify-content: space-between;
  }
}
</style>
