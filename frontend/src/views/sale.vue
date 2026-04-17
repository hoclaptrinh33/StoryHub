<script setup lang="ts">
import { ref, computed, inject } from 'vue';
import { useRouter } from 'vue-router';
import DefaultLayout from '../components/layout/defaultLayout.vue';

const router = useRouter();
const addNotification = inject('addNotification') as (type: string, msg: string) => void;

// UI State
const mode = ref<'sale' | 'rental'>('sale');
const searchQuery = ref('');

// Mock Data for testing
const products = ref([
  { id: 1, name: 'One Piece - Tập 105', price: 25000, rent_price: 5000, image: 'https://via.placeholder.com/150x200?text=OP105', code: 'OP105' },
  { id: 2, name: 'Conan - Tập 98', price: 20000, rent_price: 4000, image: 'https://via.placeholder.com/150x200?text=CONAN98', code: 'CONAN98' },
  { id: 3, name: 'Spy x Family - Tập 10', price: 28000, rent_price: 6000, image: 'https://via.placeholder.com/150x200?text=SPY10', code: 'SPY10' },
  { id: 4, name: 'Jujutsu Kaisen - Tập 20', price: 30000, rent_price: 7000, image: 'https://via.placeholder.com/150x200?text=JJK20', code: 'JJK20' },
  { id: 5, name: 'Naruto - Tập 72', price: 22000, rent_price: 4500, image: 'https://via.placeholder.com/150x200?text=NARUTO', code: 'NARU72' },
  { id: 6, name: 'Doraemon - Tập 1', price: 18000, rent_price: 3000, image: 'https://via.placeholder.com/150x200?text=DORA', code: 'DORA01' },
]);

const cart = ref<any[]>([]);

// Computed
const filteredProducts = computed(() => {
  return products.value.filter(p => 
    p.name.toLowerCase().includes(searchQuery.value.toLowerCase()) || 
    p.code.toLowerCase().includes(searchQuery.value.toLowerCase())
  );
});

const subtotal = computed(() => {
  return cart.value.reduce((sum, item) => sum + (mode.value === 'sale' ? item.price : item.rent_price), 0);
});

// Methods
const formatCurrency = (v: number) => new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(v);

const addToCart = (product: any) => {
  cart.value.push({ ...product, cartId: Date.now() });
  addNotification('success', `Đã thêm ${product.name}`);
};

const removeFromCart = (cartId: number) => {
  cart.value = cart.value.filter(item => item.cartId !== cartId);
};

const handleConfirm = () => {
  if (cart.value.length === 0) {
    addNotification('info', 'Đang chuyển hướng đến trang tạo đơn mới...');
  } else {
    addNotification('success', 'Đã lưu giỏ hàng tạm thời và chuyển hướng thanh toán');
  }
  
  // Chuyển hướng theo mode
  if (mode.value === 'sale') {
    router.push('/order-sale');
  } else {
    router.push('/rentalorder');
  }
};
</script>

<template>
  <DefaultLayout>
    <div class="pos-container">
      <div class="pos-layout">
        <!-- Left Column: Search & Products -->
        <div class="products-column">
          <div class="header-lux-area">
             <div class="title-meta">
                <h2>Bán Hàng & Cho Thuê</h2>
                <p>Tìm kiếm sản phẩm hoặc quét mã vạch để bắt đầu</p>
             </div>
             <div class="mode-pills">
                <button :class="{ active: mode === 'sale' }" @click="mode = 'sale'; cart = []">BÁN HÀNG</button>
                <button :class="{ active: mode === 'rental' }" @click="mode = 'rental'; cart = []">CHO THUÊ</button>
             </div>
          </div>

          <div class="search-bar-premium">
             <span class="material-icons">search</span>
             <input v-model="searchQuery" type="text" placeholder="Gõ tên truyện hoặc mã SKU để tìm thủ công..." />
          </div>

          <div class="product-grid-lux">
             <div v-for="p in filteredProducts" :key="p.id" class="p-card-pos" @click="addToCart(p)">
                <div class="p-image-box">
                   <img :src="p.image" :alt="p.name" />
                   <div class="p-sku">{{ p.code }}</div>
                </div>
                <div class="p-info-box">
                   <span class="p-name">{{ p.name }}</span>
                   <span class="p-price-pill">{{ formatCurrency(mode === 'sale' ? p.price : p.rent_price) }}</span>
                </div>
                <div class="p-add-overlay"><span class="material-icons">add_shopping_cart</span></div>
             </div>
             <div v-if="filteredProducts.length === 0" class="empty-search">
                <span class="material-icons">find_in_page</span>
                <p>Không tìm thấy sản phẩm nào khớp với từ khóa</p>
             </div>
          </div>
        </div>

        <!-- Right Column: Cart (Mini) -->
        <div class="cart-column">
           <div class="cart-glass-card shadow-premium">
              <div class="cart-top">
                 <h3>🛒 Giỏ hàng tạm</h3>
                 <span class="count-badge">{{ cart.length }}</span>
              </div>

              <div class="cart-list-mini">
                 <div v-if="cart.length === 0" class="empty-mini">
                    <p>Chưa chọn món nào</p>
                 </div>
                 <div v-for="item in cart" :key="item.cartId" class="mini-item">
                    <div class="item-name-wrap">
                       <span class="item-name">{{ item.name }}</span>
                       <span class="item-price-small">{{ formatCurrency(mode === 'sale' ? item.price : item.rent_price) }}</span>
                    </div>
                    <button class="item-del" @click="removeFromCart(item.cartId)">✕</button>
                 </div>
              </div>

              <div class="cart-bottom-pos">
                 <div class="subtotal-row">
                    <span>Tổng tiền</span>
                    <span class="total-price-pos">{{ formatCurrency(subtotal) }}</span>
                 </div>
                 <button class="btn-checkout-forward" @click="handleConfirm">
                    {{ mode === 'sale' ? 'XÁC NHẬN THANH TOÁN' : 'XÁC NHẬN CHO THUÊ' }}
                    <span class="material-icons">arrow_forward</span>
                 </button>
              </div>
           </div>
        </div>
      </div>
    </div>
  </DefaultLayout>
</template>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

.pos-container { padding: 32px; background: #f8fafc; min-height: 100vh; font-family: 'Plus Jakarta Sans', sans-serif; }
.pos-layout { display: grid; grid-template-columns: 1fr 340px; gap: 32px; align-items: start; }

/* Header & Mode */
.header-lux-area { display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 24px; }
.header-lux-area h2 { font-size: 1.75rem; font-weight: 800; color: #0f172a; margin: 0; letter-spacing: -0.04em; }
.header-lux-area p { color: #64748b; font-size: 0.9rem; margin-top: 4px; }

.mode-pills { background: #e2e8f0; padding: 4px; border-radius: 12px; display: flex; gap: 4px; }
.mode-pills button { padding: 8px 16px; border-radius: 8px; border: none; background: transparent; font-weight: 700; font-size: 0.75rem; color: #64748b; cursor: pointer; transition: 0.2s; }
.mode-pills button.active { background: white; color: #2563eb; box-shadow: 0 4px 6px -1px rgba(37, 99, 235, 0.1); }

/* Search Bar */
.search-bar-premium { position: relative; margin-bottom: 32px; }
.search-bar-premium .material-icons { position: absolute; left: 16px; top: 50%; transform: translateY(-50%); color: #94a3b8; }
.search-bar-premium input { width: 100%; padding: 16px 16px 16px 52px; border-radius: 18px; border: 1.5px solid #f1f5f9; background: white; font-weight: 600; outline: none; transition: 0.3s; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.02); }
.search-bar-premium input:focus { border-color: #2563eb; box-shadow: 0 0 0 4px rgba(37, 99, 235, 0.05); }

/* Product Grid */
.product-grid-lux { display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 24px; }
.p-card-pos { background: white; border-radius: 20px; padding: 12px; border: 1px solid #f1f5f9; cursor: pointer; position: relative; transition: 0.3s; overflow: hidden; }
.p-card-pos:hover { transform: translateY(-5px); box-shadow: 0 15px 30px -10px rgba(0,0,0,0.05); border-color: #2563eb; }

.p-image-box { width: 100%; height: 220px; border-radius: 14px; overflow: hidden; position: relative; background: #f8fafc; }
.p-image-box img { width: 100%; height: 100%; object-fit: cover; }
.p-sku { position: absolute; top: 8px; left: 8px; background: rgba(15, 23, 42, 0.7); color: white; padding: 2px 8px; border-radius: 6px; font-size: 0.65rem; font-weight: 700; }

.p-info-box { margin-top: 12px; display: flex; flex-direction: column; gap: 4px; }
.p-name { font-weight: 750; color: #1e293b; font-size: 0.9rem; line-height: 1.25; height: 2.5em; overflow: hidden; }
.p-price-pill { color: #2563eb; font-weight: 800; font-size: 1rem; }

.p-add-overlay { position: absolute; top: 0; left: 0; width: 100%; height: 100%; background: rgba(37, 99, 235, 0.1); display: flex; align-items: center; justify-content: center; opacity: 0; transition: 0.2s; }
.p-card-pos:hover .p-add-overlay { opacity: 1; }
.p-add-overlay .material-icons { font-size: 32px; color: #2563eb; }

/* Cart Column */
.cart-glass-card { background: white; border-radius: 24px; padding: 24px; border: 1px solid #f1f5f9; min-height: 500px; display: flex; flex-direction: column; }
.shadow-premium { box-shadow: 0 10px 15px -3px rgba(0,0,0,0.02); }

.cart-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.cart-top h3 { font-size: 1.1rem; font-weight: 800; color: #1e293b; margin: 0; }
.count-badge { background: #2563eb; color: white; padding: 2px 10px; border-radius: 20px; font-size: 0.75rem; font-weight: 800; }

.cart-list-mini { flex: 1; display: flex; flex-direction: column; gap: 12px; margin-bottom: 20px; overflow-y: auto; max-height: calc(100vh - 400px); }
.mini-item { display: flex; justify-content: space-between; align-items: center; padding: 12px; background: #f8fafc; border-radius: 12px; border: 1px solid #f1f5f9; }
.item-name-wrap { display: flex; flex-direction: column; flex: 1; }
.item-name { font-size: 0.8rem; font-weight: 700; color: #334155; line-height: 1.2; }
.item-price-small { font-size: 0.75rem; font-weight: 700; color: #94a3b8; }
.item-del { background: none; border: none; color: #cbd5e1; cursor: pointer; padding: 4px; font-size: 0.8rem; transition: 0.2s; }
.item-del:hover { color: #ef4444; }

.empty-mini { text-align: center; color: #cbd5e1; padding-top: 40px; font-weight: 700; font-size: 0.85rem; }

/* Cart Bottom */
.cart-bottom-pos { border-top: 1px dashed #e2e8f0; padding-top: 20px; }
.subtotal-row { display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 16px; }
.subtotal-row span:first-child { font-size: 0.75rem; font-weight: 800; color: #94a3b8; text-transform: uppercase; }
.total-price-pos { font-size: 1.5rem; font-weight: 900; color: #0f172a; }

.btn-checkout-forward { width: 100%; padding: 16px; border-radius: 16px; border: none; background: #0f172a; color: white; font-weight: 800; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 10px; transition: 0.3s; box-shadow: 0 10px 15px -3px rgba(15, 23, 42, 0.2); }
.btn-checkout-forward:hover { background: #2563eb; transform: translateY(-2px); box-shadow: 0 20px 25px -5px rgba(37, 99, 235, 0.3); }

.empty-search { text-align: center; padding: 60px; color: #cbd5e1; grid-column: 1 / -1; }
.empty-search .material-icons { font-size: 4rem; opacity: 0.2; }
</style>