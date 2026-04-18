<template>
  <DefaultLayout>
    <div class="management-container">
      <div class="header-section">
        <div class="title-meta">
          <h2 class="page-title">Màn Hình Thu Ngân Gộp</h2>
          <p class="subtitle">
            Hệ thống nhận diện mã vạch tự động phân luồng Bán / Thuê
          </p>
        </div>
      </div>

      <transition name="fade">
        <div v-if="isScannerProcessing" class="state-banner scanning">
          <span class="material-icons">qr_code_scanner</span>
          Đang nhận mã scanner: <strong>{{ lastScannedCode || "..." }}</strong>
        </div>
      </transition>

      <transition name="fade">
        <div
          v-if="recoverableError"
          :class="['state-banner', recoverableError.type]"
        >
          <span class="material-icons">error_outline</span>
          <div class="banner-copy">
            <strong>{{ recoverableError.title }}</strong>
            <span>{{ recoverableError.message }}</span>
          </div>
          <button class="btn-retry-banner" @click="retryCheckout">
            Thử lại
          </button>
        </div>
      </transition>

      <div v-if="isInitialLoading" class="screen-loading-state">
        <span class="material-icons spin">autorenew</span>
        Đang nạp dữ liệu quầy...
      </div>

      <div v-else class="sales-grid-layout">
        <section class="sales-column sales-column-left">
          <div class="card-glass">
            <div class="card-header-lux">
              <h3>
                <span class="material-icons">person</span> Thông tin Khách hàng
              </h3>
            </div>

            <div class="customer-picker-lux">
              <div class="select-lux-wrapper flex-1">
                <select v-model="selectedCustomer" class="select-lux-input">
                  <option value="" disabled>
                    -- Chọn khách hàng thành viên --
                  </option>
                  <option v-for="c in customers" :key="c.id" :value="c.id">
                    {{ c.name }} • {{ c.phone }}
                  </option>
                </select>
              </div>
              <transition name="fade">
                <div v-if="customerObj" class="customer-mini-tag">
                  <span class="material-icons">verified</span>
                  {{ customerObj.name }}
                </div>
              </transition>
            </div>
            
            <div class="field-group" style="padding: 15px;">
                <label>Thời gian thuê dự kiến (Ngày):</label>
                <input type="number" v-model.number="rentalDays" class="form-control-lux w-100" min="1" max="30" />
            </div>
          </div>
        </section>

        <section class="sales-column sales-column-center">
          <div class="card-glass shadow-lux">
            <div class="card-header-lux">
              <h3>
                <span class="material-icons">shopping_bag</span> Giỏ hàng hỗn hợp
              </h3>
            </div>

            <div class="table-lux-sale">
              <table>
                <thead>
                  <tr>
                    <th>Thông tin sách</th>
                    <th style="width: 120px">Loại GD</th>
                    <th style="width: 150px">Giá (VNĐ)</th>
                    <th style="width: 60px"></th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="item in cart"
                    :key="item.id+item.code"
                    class="cart-item-row"
                  >
                    <td>
                      <div class="product-cell">
                        <div class="book-icon">
                          <span class="material-icons">menu_book</span>
                        </div>
                        <div class="details">
                          <span class="name">{{ item.name }}</span>
                          <span class="code">Mã: {{ item.code }}</span>
                        </div>
                      </div>
                    </td>
                    <td>
                      <span :class="item.type === 'retail' ? 'tag-sale' : 'tag-rent'">
                          {{ item.type === 'retail' ? 'Mua Mới' : 'Thuê' }}
                      </span>
                    </td>
                    <td class="font-bold text-blue">{{ formatCurrency(item.price) }}</td>
                    <td>
                      <button
                        class="btn-delete-lux"
                        @click="removeFromCart(item.code)"
                      >
                        <span class="material-icons">delete_sweep</span>
                      </button>
                    </td>
                  </tr>
                  <tr v-if="cart.length === 0">
                    <td colspan="4">
                      <div class="empty-cart-lux">
                        <span class="material-icons">add_shopping_cart</span>
                        <p>Giỏ hàng đang trống. Quét mã vạch (ISBN = Mua, RNT-... = Thuê).</p>
                      </div>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </section>

        <aside class="sales-column sales-column-right">
          <div ref="paymentPanelRef" class="card-glass checkout-card sticky-sidebar">
            <div class="card-header-lux">
              <h3>Thanh toán</h3>
            </div>

            <div class="summary-lux-box">
              <div class="s-line">
                <span class="lbl">Tổng Sách Mua:</span>
                <span class="val">{{ formatCurrency(salesTotal) }}</span>
              </div>
              <div class="s-line">
                <span class="lbl">Tổng Phí Thuê:</span>
                <span class="val">{{ formatCurrency(rentalsTotal) }}</span>
              </div>
              <div class="s-line discount" v-if="true">
                <span class="lbl">Tiền Cọc (Thuê):</span>
                <span class="val">{{ formatCurrency(depositTotal) }}</span>
              </div>
              <div class="divider-dashed"></div>
              <div class="total-grand">
                <span class="lbl">TỔNG KHÁCH ĐƯA</span>
                <h2 class="val">{{ formatCurrency(total) }}</h2>
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
                <label
                  class="method-btn"
                  :class="{ active: paymentMethod === 'cash' }"
                >
                  <input type="radio" value="cash" v-model="paymentMethod" />
                  <span class="material-icons">payments</span>
                  Tiền mặt
                </label>
                <label
                  class="method-btn"
                  :class="{ active: paymentMethod === 'transfer' }"
                >
                  <input
                    type="radio"
                    value="transfer"
                    v-model="paymentMethod"
                  />
                  <span class="material-icons">qr_code_2</span>
                  Chuyển khoản
                </label>
              </div>

              <div v-if="isSplitPayment" class="split-payment-grid">
                <label class="split-input-row">
                  <span>Tiền mặt</span>
                  <input
                    v-model.number="cashAmount"
                    type="number"
                    min="0"
                    @input="normalizeSplitAmounts"
                  />
                </label>
                <label class="split-input-row">
                  <span>Chuyển khoản</span>
                  <input
                    v-model.number="transferAmount"
                    type="number"
                    min="0"
                    @input="normalizeSplitAmounts"
                  />
                </label>
                <p :class="['split-status', { error: !isSplitMatched }]">
                  Tổng split: {{ formatCurrency(splitTotal) }}
                  <span>• Chênh lệch: {{ formatCurrency(splitDelta) }}</span>
                </p>
              </div>
            </div>

            <div class="checkout-actions">
              <p class="hotkey-hint">
                Phím tắt: <kbd>F1</kbd>/<kbd>Enter</kbd> xác nhận.
              </p>
              <button
                class="btn-checkout-lux"
                @click="confirmCheckout"
                :disabled="!canSubmitCheckout || isSubmittingCheckout"
                data-testid="pos-checkout-confirm"
              >
                {{
                  isSubmittingCheckout
                    ? "ĐANG XỬ LÝ..."
                    : "XUẤT HÓA ĐƠN"
                }}
                <span class="material-icons">arrow_forward</span>
              </button>
              <button class="btn-cancel-lux" @click="clearCart">
                Hủy
              </button>
            </div>
          </div>
        </aside>
      </div>

    </div>
  </DefaultLayout>
</template>

<script setup lang="ts">
import { computed, inject, onBeforeUnmount, onMounted, ref, watch } from "vue";
import DefaultLayout from "../components/layout/defaultLayout.vue";
import {
  StoryHubApiError,
  buildRequestId,
  unifiedCheckout,
  fetchCustomers,
  fetchInventoryItems,
  type CustomerListItem,
  type InventoryItemListItem,
  type PosSplitPaymentMethod,
} from "../services/storyhubApi";
import { playScanAudio } from "../utils/scanAudio";
import { toUiErrorMessage } from "../utils/backendErrorMessages";

// We compute deposits dynamically
const computeDeposit = (rentPrice: number) => Math.max(rentPrice * 4, 10000);

const addNotification = inject("addNotification") as (
  type: string,
  msg: string,
) => void;

const selectedCustomer = ref("");
const paymentMethod = ref("cash");
const isInitialLoading = ref(true);
const isSubmittingCheckout = ref(false);
const isScannerProcessing = ref(false);
const lastScannedCode = ref("");
const recoverableError = ref<any>(null);
const isSplitPayment = ref(false);
const cashAmount = ref(0);
const transferAmount = ref(0);
const paymentPanelRef = ref<HTMLElement | null>(null);
const rentalDays = ref(3);

let scannerIndicatorTimer: ReturnType<typeof setTimeout> | null = null;
const customers = ref<CustomerListItem[]>([]);
const availableProducts = ref<InventoryItemListItem[]>([]);
const cart = ref<InventoryItemListItem[]>([]);

const customerObj = computed(() =>
  customers.value.find(
    (customer) => customer.id === Number(selectedCustomer.value),
  ),
);

const salesTotal = computed(() =>
  cart.value.filter(i => i.type === 'retail').reduce((acc, i) => acc + i.price, 0)
);

const rentalsTotal = computed(() =>
  cart.value.filter(i => i.type === 'rental').reduce((acc, i) => acc + i.price, 0)
);

const depositTotal = computed(() =>
  cart.value.filter(i => i.type === 'rental').reduce((acc, i) => acc + computeDeposit(i.price), 0)
);

const total = computed(() => salesTotal.value + rentalsTotal.value + depositTotal.value);
const splitTotal = computed(() => cashAmount.value + transferAmount.value);
const splitDelta = computed(() => total.value - splitTotal.value);
const isSplitMatched = computed(() => {
  if (!isSplitPayment.value) return true;
  return splitDelta.value === 0;
});
const hasRentalItems = computed(() => cart.value.some(i => i.type === 'rental'));
const canSubmitCheckout = computed(() => {
    if (cart.value.length === 0) return false;
    if (hasRentalItems.value && !selectedCustomer.value) return false;
    if (!isSplitMatched.value) return false;
    if (isInitialLoading.value) return false;
    return true;
});

const formatCurrency = (value: number) =>
  new Intl.NumberFormat("vi-VN", { style: "currency", currency: "VND" }).format(value);

const normalizeBarcode = (rawValue: string) =>
  rawValue.replace(/[^A-Za-z0-9]/g, "").toUpperCase();

const findProductByBarcode = (rawCode: string): InventoryItemListItem | undefined => {
  const normalizedCode = normalizeBarcode(rawCode);
  if (!normalizedCode) return undefined;
  return availableProducts.value.find((product) => {
    return normalizeBarcode(product.code) === normalizedCode || normalizeBarcode(product.id) === normalizedCode;
  });
};

const normalizeSplitAmounts = () => {
  cashAmount.value = Math.max(0, Math.round(cashAmount.value || 0));
  transferAmount.value = Math.max(0, Math.round(transferAmount.value || 0));
};

const syncSinglePaymentAmount = () => {
  if (isSplitPayment.value) return;
  if (paymentMethod.value === "transfer") {
    transferAmount.value = total.value;
    cashAmount.value = 0;
    return;
  }
  cashAmount.value = total.value;
  transferAmount.value = 0;
};

const getSplitPaymentsPayload = () => {
  if (!isSplitPayment.value) {
    return [{ method: toBackendPaymentMethod(paymentMethod.value), amount: total.value }];
  }
  return [
    { method: "cash" as const, amount: cashAmount.value },
    { method: "bank_transfer" as const, amount: transferAmount.value },
  ].filter((payment) => payment.amount > 0);
};

const setRecoverableError = (title: string, message: string) => {
  recoverableError.value = { type: "error", title, message };
};
const clearRecoverableError = () => { recoverableError.value = null; };

watch([total, paymentMethod, isSplitPayment], () => syncSinglePaymentAmount());

const addToCart = (product: InventoryItemListItem, source = "scanner") => {
  const exist = cart.value.find((item) => item.code === product.code);
  if (exist) {
    if (source === "scanner") playScanAudio("error");
    addNotification("warning", "Mã này đã nằm trong giỏ.");
    return;
  }
  // Retail allows multiples of the SAME book but right now scanning identical ISBNs means +1 retail.
  // Wait, our payload expects scanned codes to be unique!
  // Oh actually, identical ISBNs might conflict if scanned multiple times or we just say each physical barcode is unique.
  // Let's assume in storyhub a retail book scan adds uniquely. In our schema payload, it checks uniqueness of scanned_codes!
  // This means they can't scan same ISBN twice unless we allow it or generate mock unique codes. To bypass the validator `scanned_codes must be unique`, 
  // We can just append a differentiator or the backend validator needs changing.
  // But wait, the backend `validate_discount` says `if len(set(scanned_codes)) != len(scanned_codes): raise Error`.
  // So they can only buy 1 quantity of each ISBN per transaction for now.
  
  cart.value.push({ ...product });
  clearRecoverableError();
  if (source === "scanner") playScanAudio("success");
};

const removeFromCart = (code: string) => {
  cart.value = cart.value.filter((item) => item.code !== code);
  clearRecoverableError();
};

const toBackendPaymentMethod = (method: string): PosSplitPaymentMethod =>
  method === "transfer" ? "bank_transfer" : "cash";

const confirmCheckout = async () => {
  if (!canSubmitCheckout.value) {
    addNotification("warning", "Kiểm tra lại giỏ hàng, số tiền hoặc khách hàng (bắt buộc khi thuê).");
    return;
  }
  isSubmittingCheckout.value = true;
  clearRecoverableError();
  try {
    const customerId = selectedCustomer.value ? Number(selectedCustomer.value) : null;
    const res = await unifiedCheckout({
      customer_id: customerId,
      scanned_codes: cart.value.map((item) => item.code),
      discount_type: "none",
      discount_value: 0,
      split_payments: getSplitPaymentsPayload(),
      rental_days: rentalDays.value,
      request_id: buildRequestId("checkout-unified"),
    });

    let msg = `Thanh toán thành công. `;
    if(res.order_id) msg += `Đơn Mua: #${res.order_id}. `;
    if(res.rental_contract_id) msg += `HĐ Thuê: #${res.rental_contract_id}. `;
    msg += `Tổng KH thu: ${formatCurrency(res.grand_total)}.`;

    addNotification("success", msg);
    clearCart();
    
    // Refresh products
    availableProducts.value = await fetchInventoryItems();
  } catch (error) {
    if (error instanceof StoryHubApiError) {
      addNotification("error", toUiErrorMessage(error.code, error.message));
      return;
    }
    addNotification("error", "Lỗi kết nối.");
  } finally {
    isSubmittingCheckout.value = false;
  }
};

const clearCart = () => { cart.value = []; clearRecoverableError(); };
const retryCheckout = () => { if (!isSubmittingCheckout.value) void confirmCheckout(); };

const handleScannerScan = (event: Event) => {
  const customEvent = event as CustomEvent<{code?: string}>;
  const rawCode = customEvent.detail?.code?.trim() ?? "";
  if (!rawCode) return;

  isScannerProcessing.value = true;
  lastScannedCode.value = rawCode;
  if (scannerIndicatorTimer) clearTimeout(scannerIndicatorTimer);
  scannerIndicatorTimer = setTimeout(() => {
    isScannerProcessing.value = false;
    scannerIndicatorTimer = null;
  }, 700);

  const matchedProduct = findProductByBarcode(rawCode);
  if (!matchedProduct) {
    playScanAudio("error");
    addNotification("error", `Không nhận diện được mã: ${rawCode}`);
    return;
  }
  addToCart(matchedProduct, "scanner");
};

const handleGlobalHotkey = (event: Event) => {
  const customEvent = event as CustomEvent<{name?: string}>;
  const hotkey = customEvent.detail?.name;
  if (hotkey === "f1" || hotkey === "enter") void confirmCheckout();
  if (hotkey === "escape") { clearCart(); addNotification("info", "Đã hủy"); }
};

onMounted(async () => {
  syncSinglePaymentAmount();
  try {
    const [custData, itemData] = await Promise.all([fetchCustomers(), fetchInventoryItems()]);
    customers.value = custData;
    availableProducts.value = itemData;
  } catch (err) {
    addNotification("error", "Lỗi nạp dữ liệu.");
  } finally {
    isInitialLoading.value = false;
  }
  window.addEventListener("storyhub:scan", handleScannerScan as EventListener);
  window.addEventListener("storyhub:hotkey", handleGlobalHotkey as EventListener);
});

onBeforeUnmount(() => {
  window.removeEventListener("storyhub:scan", handleScannerScan as EventListener);
  window.removeEventListener("storyhub:hotkey", handleGlobalHotkey as EventListener);
});
</script>

<style scoped>
@import url("https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap");

.management-container {
  padding: 32px;
  background: #fdfdfd;
  min-height: 100vh;
  font-family: "Plus Jakarta Sans", sans-serif;
}

.header-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 32px;
}
.page-title {
  font-size: 2.25rem;
  font-weight: 800;
  color: #0f172a;
  margin: 0;
  letter-spacing: -0.04em;
}
.subtitle {
  color: #64748b;
  font-size: 1rem;
  margin-top: 4px;
}

.screen-loading-state {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 20px;
  padding: 20px;
  color: #334155;
  font-weight: 700;
}

.sales-grid-layout {
  display: grid;
  grid-template-columns: 350px 1fr 400px;
  gap: 24px;
}

.card-glass {
  background: white;
  border-radius: 24px;
  border: 1px solid #e2e8f0;
  overflow: hidden;
}

.shadow-lux {
  box-shadow: 0 12px 32px rgba(0,0,0,0.04);
}

.card-header-lux {
  padding: 18px 24px;
  background: #f8fafc;
  border-bottom: 1px solid #e2e8f0;
}
.card-header-lux h3 {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 700;
  color: #1e293b;
  display: flex;
  align-items: center;
  gap: 10px;
}

.customer-picker-lux {
  padding: 15px;
}
.select-lux-input {
  width: 100%;
  padding: 12px;
  border-radius: 12px;
  border: 1px solid #cbd5e1;
  font-family: inherit;
}
.customer-mini-tag {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: #eff6ff;
  color: #2563eb;
  padding: 6px 12px;
  border-radius: 20px;
  font-weight: 600;
  font-size: 0.85rem;
  margin-top: 10px;
}

.table-lux-sale table {
  width: 100%;
  border-collapse: collapse;
}
.table-lux-sale th {
  text-align: left;
  padding: 12px 15px;
  font-size: 0.85rem;
  font-weight: 700;
  color: #64748b;
  background: #f8fafc;
  border-bottom: 2px solid #e2e8f0;
}
.table-lux-sale td {
  padding: 16px 15px;
  border-bottom: 1px solid #f1f5f9;
  vertical-align: middle;
}

.product-cell {
  display: flex;
  align-items: center;
  gap: 12px;
}
.book-icon {
  background: #eff6ff;
  color: #3b82f6;
  width: 44px;
  height: 44px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.details {
  display: flex;
  flex-direction: column;
}
.details .name {
  font-weight: 700;
  color: #0f172a;
}
.details .code {
  font-size: 0.8rem;
  color: #64748b;
  margin-top: 2px;
}

.tag-sale {
    background: #dcfce7;
    color: #166534;
    padding: 6px 10px;
    border-radius: 8px;
    font-size: 0.8rem;
    font-weight: 700;
}
.tag-rent {
    background: #fef08a;
    color: #854d0e;
    padding: 6px 10px;
    border-radius: 8px;
    font-size: 0.8rem;
    font-weight: 700;
}

.btn-delete-lux {
  background: #fef2f2;
  color: #dc2626;
  border: none;
  width: 36px;
  height: 36px;
  border-radius: 10px;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}
.btn-delete-lux:hover {
  background: #fee2e2;
}

.empty-cart-lux {
  text-align: center;
  padding: 40px;
  color: #94a3b8;
}
.empty-cart-lux .material-icons {
  font-size: 3rem;
  color: #cbd5e1;
  margin-bottom: 12px;
}

.summary-lux-box {
  padding: 20px;
  background: #f8fafc;
}
.s-line {
  display: flex;
  justify-content: space-between;
  margin-bottom: 12px;
  font-size: 0.95rem;
  color: #334155;
}
.s-line.discount {
  color: #10b981;
}
.divider-dashed {
  border-top: 2px dashed #cbd5e1;
  margin: 16px 0;
}
.total-grand {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.total-grand .lbl {
  font-weight: 800;
  color: #0f172a;
}
.total-grand .val {
  margin: 0;
  font-size: 1.8rem;
  font-weight: 800;
  color: #2563eb;
}

.payment-method-lux {
  padding: 20px;
}
.payment-method-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}
.method-label {
  font-weight: 700;
  margin: 0;
}
.split-toggle {
  font-size: 0.9rem;
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
}
.method-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}
.method-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 16px;
  border: 2px solid #e2e8f0;
  border-radius: 16px;
  cursor: pointer;
  font-weight: 600;
  color: #64748b;
  transition: all 0.2s;
}
.method-btn input {
  display: none;
}
.method-btn.active {
  background: #eff6ff;
  border-color: #3b82f6;
  color: #1d4ed8;
}

.split-payment-grid {
  margin-top: 15px;
  background: #f8fafc;
  padding: 15px;
  border-radius: 12px;
}
.split-input-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}
.split-input-row input {
  width: 120px;
  padding: 8px;
  border-radius: 8px;
  border: 1px solid #cbd5e1;
  text-align: right;
  font-family: "Plus Jakarta Sans", sans-serif;
  font-weight: 700;
}
.split-status {
  font-size: 0.85rem;
  margin: 10px 0 0 0;
  text-align: right;
  font-weight: 600;
}
.split-status.error {
  color: #ef4444;
}

.checkout-actions {
  padding: 20px;
  border-top: 1px solid #e2e8f0;
}
.hotkey-hint {
  text-align: center;
  font-size: 0.85rem;
  color: #94a3b8;
  margin: 0 0 15px 0;
}
.hotkey-hint kbd {
  background: #f1f5f9;
  padding: 2px 6px;
  border-radius: 4px;
  border: 1px solid #cbd5e1;
  font-family: inherit;
  font-weight: 700;
  color: #334155;
}

.btn-checkout-lux {
  width: 100%;
  padding: 16px;
  background: #10b981;
  color: white;
  border: none;
  border-radius: 16px;
  font-size: 1.1rem;
  font-weight: 800;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  cursor: pointer;
  margin-bottom: 12px;
}
.btn-checkout-lux:disabled {
  background: #94a3b8;
  cursor: not-allowed;
}
.btn-cancel-lux {
  width: 100%;
  padding: 14px;
  background: transparent;
  color: #64748b;
  border: 2px solid #e2e8f0;
  border-radius: 16px;
  font-weight: 700;
  cursor: pointer;
}
.btn-cancel-lux:hover {
  background: #f1f5f9;
}
</style>
