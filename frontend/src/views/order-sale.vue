<template>
  <DefaultLayout>
    <div class="management-container">
      <!-- Header Section -->
      <div class="header-section">
        <div class="title-meta">
          <h2 class="page-title">Tạo Đơn Bán Hàng</h2>
          <p class="subtitle">Quản lý giỏ hàng và thanh toán trực tiếp cho khách hàng</p>
        </div>
        <div class="header-actions">
           <div class="order-id-badge">ĐƠN HÀNG #{{ orderNumber }}</div>
        </div>
      </div>

      <div class="sales-grid-layout">
        <!-- Main Sales Area (Left) -->
        <div class="sales-main-content">
          <!-- Customer Selection Card -->
          <div class="card-glass mb-6">
            <div class="card-header-lux">
               <h3><span class="material-icons">person</span> Thông tin Khách hàng</h3>
               <button class="btn-text-lux" @click="isCustomerModalOpen = true">
                 <span class="material-icons">person_add_alt</span> Khách mới
               </button>
            </div>
            
            <div class="customer-picker-lux">
               <div class="select-lux-wrapper flex-1">
                 <select v-model="selectedCustomer" class="select-lux-input">
                    <option value="" disabled>-- Chọn khách hàng thành viên --</option>
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
          </div>

          <!-- Product Selection & Table -->
          <div class="card-glass shadow-lux">
            <div class="card-header-lux">
               <h3><span class="material-icons">shopping_bag</span> Sản phẩm Đang chọn</h3>
               <div class="search-product-lux">
                  <span class="material-icons">search</span>
                  <input type="text" placeholder="Tìm tên truyện hoặc mã..." v-model="productSearch" />
               </div>
            </div>

            <div class="table-lux-sale">
               <table>
                  <thead>
                    <tr>
                      <th>Thông tin truyện</th>
                      <th style="width: 120px">Số lượng</th>
                      <th style="width: 150px">Đơn giá</th>
                      <th style="width: 150px">Thành tiền</th>
                      <th style="width: 60px"></th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="item in cart" :key="item.id" class="cart-item-row">
                      <td>
                        <div class="product-cell">
                           <div class="book-icon"><span class="material-icons">menu_book</span></div>
                           <div class="details">
                              <span class="name">{{ item.name }}</span>
                              <span class="code">SKU: {{ item.code }}</span>
                           </div>
                        </div>
                      </td>
                      <td>
                        <div class="qty-counter-lux">
                           <button @click="item.qty > 1 ? item.qty-- : null">-</button>
                           <input type="number" v-model.number="item.qty" />
                           <button @click="item.qty++">+</button>
                        </div>
                      </td>
                      <td class="font-bold">{{ formatCurrency(item.price) }}</td>
                      <td class="font-extrabold text-blue">{{ formatCurrency(item.price * item.qty) }}</td>
                      <td>
                        <button class="btn-delete-lux" @click="removeFromCart(item.id)">
                           <span class="material-icons">delete_sweep</span>
                        </button>
                      </td>
                    </tr>
                    <tr v-if="cart.length === 0">
                      <td colspan="5">
                         <div class="empty-cart-lux">
                            <span class="material-icons">add_shopping_cart</span>
                            <p>Giỏ hàng đang trống. Vui lòng thêm sản phẩm.</p>
                         </div>
                      </td>
                    </tr>
                  </tbody>
               </table>
            </div>

            <div class="product-shelf-lux">
               <p class="section-label">Gợi ý sản phẩm:</p>
               <div class="shelf-grid">
                  <div v-for="p in availableProducts" :key="p.id" class="shelf-item" @click="addToCart(p)">
                     <div class="p-info">
                        <span class="p-name">{{ p.name }}</span>
                        <span class="p-price">{{ formatCurrency(p.price) }}</span>
                     </div>
                     <span class="material-icons add-icon">add_shopping_cart</span>
                  </div>
               </div>
            </div>
          </div>
        </div>

        <!-- Checkout Sidebar (Right) -->
        <div class="sales-sidebar">
           <div class="card-glass checkout-card sticky-sidebar">
              <div class="card-header-lux">
                <h3> Thanh toán</h3>
              </div>

              <div class="promo-section-lux">
                 <label>Mã giảm giá / Quà tặng</label>
                 <div class="promo-input-group">
                    <input type="text" placeholder="STORYHUB_2024..." v-model="promoCode" />
                    <button class="btn-apply-lux">Áp dụng</button>
                 </div>
              </div>

              <div class="summary-lux-box">
                 <div class="s-line">
                    <span class="lbl">Tạm tính ({{ totalItems }} món)</span>
                    <span class="val">{{ formatCurrency(subtotal) }}</span>
                 </div>
                 <div class="s-line discount">
                    <span class="lbl">Chiết khấu hội viên</span>
                    <span class="val">-{{ formatCurrency(discount) }}</span>
                 </div>
                 <div class="divider-dashed"></div>
                 <div class="total-grand">
                    <span class="lbl">CẦN THANH TOÁN</span>
                    <h2 class="val">{{ formatCurrency(total) }}</h2>
                 </div>
              </div>

              <div class="payment-method-lux">
                 <p class="method-label">Hình thức thanh toán:</p>
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
              </div>

              <div class="checkout-actions">
                 <button class="btn-checkout-lux" @click="confirmCheckout">
                    XÁC NHẬN & XUẤT HÓA ĐƠN
                    <span class="material-icons">arrow_forward</span>
                 </button>
                 <button class="btn-cancel-lux" @click="clearCart">
                    Hủy đơn hàng
                 </button>
              </div>
           </div>
        </div>
      </div>
    </div>

    <!-- Modals (Placeholders for Customer/Success) -->
    <BaseModal :is-open="isCustomerModalOpen" title="Thêm khách hàng nhanh" @close="isCustomerModalOpen = false">
       <div class="quick-form">
          <div class="form-group-lux">
             <label>Tên khách hàng</label>
             <input type="text" class="input-lux" />
          </div>
          <div class="form-group-lux">
             <label>Số điện thoại</label>
             <input type="text" class="input-lux" />
          </div>
       </div>
       <template #footer>
          <button class="btn-lux" @click="isCustomerModalOpen = false">Lưu lại</button>
       </template>
    </BaseModal>
  </DefaultLayout>
</template>

<script setup lang="ts">
import { ref, computed, inject } from 'vue';
import DefaultLayout from '../components/layout/defaultLayout.vue';
import BaseModal from '../components/layout/BaseModal.vue';


 

const addNotification = inject('addNotification') as (type: string, msg: string) => void;

// Mock Data
const orderNumber = ref('SAL-2024-0042');
const selectedCustomer = ref('');
const promoCode = ref('');
const paymentMethod = ref('cash');
const productSearch = ref('');
const isCustomerModalOpen = ref(false);

const customers = ref([
  { id: 1, name: 'Nguyễn Văn A', phone: '0901234567' },
  { id: 2, name: 'Trần Thị B', phone: '0987654321' },
]);

const availableProducts = ref([
  { id: 101, name: 'One Piece Tập 105', code: 'OP-105', price: 25000 },
  { id: 102, name: 'Conan Tập 98', code: 'CONAN-98', price: 22000 },
  { id: 103, name: 'Jujutsu Kaisen Vol 20', code: 'JJK-20', price: 35000 },
  { id: 104, name: 'Spy x Family Vol 10', code: 'SPY-10', price: 30000 },
]);

const cart = ref<any[]>([]);

// Computed
const customerObj = computed(() => customers.value.find(c => c.id === Number(selectedCustomer.value)));
const subtotal = computed(() => cart.value.reduce((s, i) => s + (i.price * i.qty), 0));
const discount = computed(() => customerObj.value ? Math.round(subtotal.value * 0.05) : 0); // 5% cho hội viên
const total = computed(() => subtotal.value - discount.value);
const totalItems = computed(() => cart.value.reduce((s, i) => s + i.qty, 0));

// Methods
const formatCurrency = (v: number) => new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(v);

const addToCart = (product: any) => {
  const exist = cart.value.find(i => i.id === product.id);
  if (exist) {
    exist.qty++;
  } else {
    cart.value.push({ ...product, qty: 1 });
  }
  addNotification('success', `Đã thêm ${product.name} vào giỏ`);
};

const removeFromCart = (id: number) => {
  cart.value = cart.value.filter(i => i.id !== id);
};

const confirmCheckout = () => {
  if (cart.value.length === 0) return addNotification('warning', 'Giỏ hàng đang trống');
  addNotification('success', 'Thanh toán hoàn tất! Hóa đơn đã được tạo.');
  clearCart();
};

const clearCart = () => {
  cart.value = [];
  selectedCustomer.value = '';
};
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

.management-container { 
  padding: 32px; 
  background: #fdfdfd; 
  min-height: 100vh;
  font-family: 'Plus Jakarta Sans', sans-serif;
}

.header-section { display: flex; justify-content: space-between; align-items: center; margin-bottom: 32px; }
.page-title { font-size: 2.25rem; font-weight: 800; color: #0f172a; margin: 0; letter-spacing: -0.04em; }
.subtitle { color: #64748b; font-size: 1rem; margin-top: 4px; }
.order-id-badge { background: #eff6ff; color: #2563eb; padding: 10px 20px; border-radius: 14px; font-weight: 800; font-size: 0.9rem; border: 1px solid #dbeafe; }

.sales-grid-layout { display: grid; grid-template-columns: 1fr 400px; gap: 32px; align-items: start; }

.card-glass { 
  background: white; border-radius: 28px; padding: 32px; border: 1px solid #f1f5f9;
  box-shadow: 0 10px 15px -3px rgba(0,0,0,0.02);
}
.shadow-lux { box-shadow: 0 20px 25px -5px rgba(0,0,0,0.05); }
.mb-6 { margin-bottom: 32px; }

.card-header-lux { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; }
.card-header-lux h3 { font-size: 1.25rem; font-weight: 800; color: #1e293b; margin: 0; display: flex; align-items: center; gap: 12px; }

/* Product Search */
.search-product-lux { position: relative; width: 300px; }
.search-product-lux .material-icons { position: absolute; left: 14px; top: 50%; transform: translateY(-50%); color: #94a3b8; font-size: 20px; }
.search-product-lux input { width: 100%; padding: 10px 10px 10px 42px; border-radius: 14px; border: 1.5px solid #f1f5f9; background: #f8fafc; outline: none; font-weight: 600; transition: 0.3s; }
.search-product-lux input:focus { border-color: #2563eb; background: white; box-shadow: 0 0 0 4px rgba(37, 99, 235, 0.05); }

/* Table Sale */
.table-lux-sale table { width: 100%; border-collapse: separate; border-spacing: 0 16px; }
.table-lux-sale th { padding: 0 16px; font-size: 0.75rem; font-weight: 800; color: #94a3b8; text-transform: uppercase; text-align: left; }
.table-lux-sale td { padding: 16px; vertical-align: middle; background: rgba(248, 250, 252, 0.5); border-radius: 0; }
.table-lux-sale td:first-child { border-radius: 16px 0 0 16px; }
.table-lux-sale td:last-child { border-radius: 0 16px 16px 0; }

.product-cell { display: flex; align-items: center; gap: 16px; }
.book-icon { width: 44px; height: 44px; border-radius: 12px; background: white; border: 1px solid #f1f5f9; display: flex; align-items: center; justify-content: center; color: #2563eb; }
.product-cell .name { display: block; font-weight: 800; color: #1e293b; font-size: 1.05rem; }
.product-cell .code { font-size: 0.75rem; font-weight: 600; color: #94a3b8; }

.qty-counter-lux { display: flex; align-items: center; background: white; border-radius: 10px; border: 1.5px solid #f1f5f9; width: 100px; overflow: hidden; }
.qty-counter-lux button { width: 32px; height: 32px; border: none; background: transparent; font-weight: 800; cursor: pointer; transition: 0.2s; }
.qty-counter-lux button:hover { background: #f1f5f9; color: #2563eb; }
.qty-counter-lux input { width: 36px; border: none; text-align: center; font-weight: 800; font-family: inherit; font-size: 0.9rem; -moz-appearance: textfield; }
.qty-counter-lux input::-webkit-inner-spin-button { -webkit-appearance: none; }

.btn-delete-lux { width: 36px; height: 36px; border-radius: 10px; border: none; background: #fee2e2; color: #ef4444; cursor: pointer; transition: 0.3s; }
.btn-delete-lux:hover { background: #ef4444; color: white; transform: rotate(-8deg); }

.empty-cart-lux { text-align: center; padding: 40px; color: #cbd5e1; }
.empty-cart-lux .material-icons { font-size: 4rem; opacity: 0.2; margin-bottom: 12px; }

/* Product Shelf */
.product-shelf-lux { margin-top: 32px; padding-top: 32px; border-top: 1px solid #f1f5f9; }
.section-label { font-weight: 800; color: #94a3b8; font-size: 0.8rem; text-transform: uppercase; margin-bottom: 16px; }
.shelf-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 16px; }
.shelf-item { border-radius: 20px; border: 1.5px solid #f1f5f9; padding: 16px; display: flex; justify-content: space-between; align-items: center; cursor: pointer; transition: 0.3s; }
.shelf-item:hover { border-color: #2563eb; background: #eff6ff; transform: translateY(-3px); }
.shelf-item .p-name { display: block; font-weight: 700; color: #1e293b; font-size: 0.95rem; }
.shelf-item .p-price { font-weight: 800; color: #059669; font-size: 0.85rem; }
.add-icon { color: #2563eb; opacity: 0; transition: 0.3s; }
.shelf-item:hover .add-icon { opacity: 1; }

/* Sidebar */
.sticky-sidebar { position: sticky; top: 32px; }
.promo-section-lux { margin-bottom: 32px; }
.promo-section-lux label { display: block; font-size: 0.75rem; font-weight: 800; color: #94a3b8; text-transform: uppercase; margin-bottom: 8px; }
.promo-input-group { display: flex; gap: 10px; }
.promo-input-group input { flex: 1; padding: 12px; border-radius: 14px; border: 1.5px solid #f1f5f9; outline: none; font-weight: 700; background: #f8fafc; }
.promo-input-group input:focus { border-color: #2563eb; background: white; }
.btn-apply-lux { background: #0f172a; color: white; border: none; padding: 0 20px; border-radius: 14px; font-weight: 700; cursor: pointer; }

.summary-lux-box { background: #f8fafc; border-radius: 24px; padding: 24px; margin-bottom: 32px; }
.s-line { display: flex; justify-content: space-between; padding: 8px 0; }
.s-line .lbl { font-weight: 600; color: #64748b; }
.s-line .val { font-weight: 800; color: #1e293b; }
.s-line.discount { color: #dc2626; }
.s-line.discount .val { color: #dc2626; }
.divider-dashed { margin: 16px 0; border-top: 2px dashed #e2e8f0; }
.total-grand { text-align: right; }
.total-grand .lbl { display: block; font-size: 0.75rem; font-weight: 800; color: #94a3b8; margin-bottom: 4px; }
.total-grand h2 { margin: 0; font-size: 2.25rem; font-weight: 900; color: #0f172a; letter-spacing: -0.05em; }

.payment-method-lux { margin-bottom: 32px; }
.method-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-top: 12px; }
.method-btn { padding: 16px; border-radius: 20px; border: 2px solid #f1f5f9; display: flex; flex-direction: column; align-items: center; gap: 8px; font-weight: 700; color: #64748b; cursor: pointer; transition: 0.3s; font-size: 0.85rem; }
.method-btn input { display: none; }
.method-btn.active { border-color: #2563eb; background: #eff6ff; color: #2563eb; }
.method-btn:hover:not(.active) { background: #f8fafc; border-color: #cbd5e1; }

.checkout-actions { display: flex; flex-direction: column; gap: 12px; }
.btn-checkout-lux { background: #2563eb; color: white; border: none; padding: 20px; border-radius: 24px; font-weight: 800; font-family: inherit; font-size: 1.1rem; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 10px; transition: 0.3s; box-shadow: 0 10px 20px -5px rgba(37, 99, 235, 0.4); }
.btn-checkout-lux:hover { background: #1d4ed8; transform: translateY(-3px); box-shadow: 0 15px 30px -10px rgba(37, 99, 235, 0.5); }
.btn-cancel-lux { background: transparent; border: none; color: #94a3b8; font-weight: 700; cursor: pointer; padding: 12px; }
.btn-cancel-lux:hover { color: #ef4444; }

@media (max-width: 1200px) {
  .sales-grid-layout { grid-template-columns: 1fr; }
  .sticky-sidebar { position: static; }
}

/* Helpers */
.font-bold { font-weight: 700; }
.font-extrabold { font-weight: 900; }
.text-blue { color: #2563eb; }
</style>