<script setup lang="ts">
import DefaultLayout from '../components/layout/defaultLayout.vue'
import { ref, computed, inject } from 'vue';

const addNotification = inject('addNotification') as any;

const mode = ref<'sale' | 'rental'>('sale');
const searchQuery = ref('');

const products = ref([
  { id: 1, name: 'One Piece - Tập 105', price: 25000, rent_price: 5000, image: 'https://via.placeholder.com/150x200', stock: 15 },
  { id: 2, name: 'Conan - Tập 98', price: 20000, rent_price: 4000, image: 'https://via.placeholder.com/150x200', stock: 8 },
  { id: 3, name: 'Spy x Family - Tập 10', price: 28000, rent_price: 6000, image: 'https://via.placeholder.com/150x200', stock: 12 },
  { id: 4, name: 'Jujutsu Kaisen - Tập 20', price: 30000, rent_price: 7000, image: 'https://via.placeholder.com/150x200', stock: 5 },
  { id: 5, name: 'Attack on Titan - Tập 34', price: 35000, rent_price: 8000, image: 'https://via.placeholder.com/150x200', stock: 20 },
  { id: 6, name: 'Demon Slayer - Tập 23', price: 27000, rent_price: 5000, image: 'https://via.placeholder.com/150x200', stock: 10 },
]);

const cart = ref<any[]>([]);
const totalAmount = computed(() => {
  return cart.value.reduce((sum, item) => sum + (mode.value === 'sale' ? item.price : item.rent_price), 0);
});

const addToCart = (product: any) => {
  cart.value.push({ ...product, cartId: Date.now() });
  addNotification('success', `Đã thêm ${product.name} vào giỏ hàng`);
};

const removeFromCart = (cartId: number) => {
  cart.value = cart.value.filter(item => item.cartId !== cartId);
};

const history = ref([
  { id: 'DH001', customer: 'Nguyễn Văn A', type: 'Bán', items: 'One Piece x1, Conan x1', total: 45000, date: '2026-04-16 10:30' },
  { id: 'DH002', customer: 'Trần Thị B', type: 'Thuê', items: 'Spy x Family x2', total: 12000, date: '2026-04-16 11:15' },
]);

const confirmTransaction = () => {
  if (cart.value.length === 0) {
    addNotification('warning', 'Giỏ hàng đang trống!');
    return;
  }
  
  const newOrder = {
    id: 'DH' + Math.floor(100 + Math.random() * 900),
    customer: 'Khách lẻ',
    type: mode.value === 'sale' ? 'Bán' : 'Thuê',
    items: cart.value.map(i => i.name).join(', '),
    total: totalAmount.value,
    date: new Date().toLocaleString()
  };
  
  history.value.unshift(newOrder);
  cart.value = [];
  addNotification('success', 'Xác nhận giao dịch thành công!');
};

const filteredProducts = computed(() => {
  return products.value.filter(p => p.name.toLowerCase().includes(searchQuery.value.toLowerCase()));
});
</script>

<template>
  <DefaultLayout>
    <div class="sales-page">
      <div class="main-header">
        <h2 class="title">Bán hàng & Cho thuê</h2>
        <div class="mode-toggle">
          <button 
            :class="{ active: mode === 'sale' }" 
            @click="mode = 'sale'; cart = []"
          >
            🛒 Bán hàng
          </button>
          <button 
            :class="{ active: mode === 'rental' }" 
            @click="mode = 'rental'; cart = []"
          >
            📖 Cho thuê
          </button>
        </div>
      </div>

      <div class="sales-content">
        <!-- Left Section: Search & Products -->
        <div class="products-section">
          <div class="search-container">
            <span class="search-icon">🔍</span>
            <input 
              v-model="searchQuery"
              type="text" 
              placeholder="Tìm kiếm hoặc quét mã vạch truyện..." 
              class="search-input" 
            />
          </div>

          <div class="product-grid">
            <div 
              v-for="p in filteredProducts" 
              :key="p.id" 
              class="product-card"
              @click="addToCart(p)"
            >
              <div class="image-wrapper">
                <img :src="p.image" :alt="p.name" />
                <span class="stock-badge">Kho: {{ p.stock }}</span>
              </div>
              <div class="product-info">
                <span class="product-name">{{ p.name }}</span>
                <span class="product-price">
                  {{ mode === 'sale' ? p.price.toLocaleString() : p.rent_price.toLocaleString() }}đ
                </span>
              </div>
              
            </div>
          </div>
        </div>

        <!-- Right Section: Cart -->
        <div class="cart-section">
          <div class="cart-card">
            <div class="cart-header">
              <h3>{{ mode === 'sale' ? 'Giỏ hàng' : 'Phiếu thuê' }}</h3>
              <span class="item-count">{{ cart.length }} món</span>
            </div>

            <div class="cart-items">
              <div v-if="cart.length === 0" class="empty-cart">
                <div class="empty-icon">🛒</div>
                <p>Chưa có sản phẩm nào</p>
              </div>
              <div v-for="item in cart" :key="item.cartId" class="cart-item">
                <img :src="item.image" class="item-thumb" />
                <div class="item-details">
                  <span class="item-name">{{ item.name }}</span>
                  <span class="item-price">
                    {{ mode === 'sale' ? item.price.toLocaleString() : item.rent_price.toLocaleString() }}đ
                  </span>
                </div>
                <button class="btn-remove" @click="removeFromCart(item.cartId)">✕</button>
              </div>
            </div>

            <div class="cart-footer">
              <div class="summary-line">
                <span>Tạm tính:</span>
                <span>{{ totalAmount.toLocaleString() }}đ</span>
              </div>
              <div class="summary-line total">
                <span>Tổng cộng:</span>
                <span>{{ totalAmount.toLocaleString() }}đ</span>
              </div>
              <button 
                class="btn-checkout" 
                :disabled="cart.length === 0"
                @click="confirmTransaction"
              >
                Xác nhận {{ mode === 'sale' ? 'Thanh toán' : 'Cho thuê' }}
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- History Section -->
      
    </div>
  </DefaultLayout>
</template>

<style scoped>
.sales-page {
  padding: 24px;
  background: #f1f5f9;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  gap: 24px;
  font-family: 'Inter', system-ui, -apple-system, sans-serif;
}

/* Header & Toggle */
.main-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.title {
  font-size: 1.5rem;
  font-weight: 700;
  color: #1e293b;
  margin: 0;
}

.mode-toggle {
  display: flex;
  background: #e2e8f0;
  padding: 4px;
  border-radius: 12px;
  gap: 4px;
}

.mode-toggle button {
  padding: 8px 16px;
  border: none;
  background: transparent;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: 0.3s;
  color: #64748b;
}

.mode-toggle button.active {
  background: white;
  color: #2563eb;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
}

/* Main Content Layout */
.sales-content {
  display: grid;
  grid-template-columns: 1fr 400px;
  gap: 24px;
  align-items: start;
}

/* Products Section */
.products-section {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.search-container {
  position: relative;
  width: 100%;
}

.search-icon {
  position: absolute;
  left: 16px;
  top: 50%;
  transform: translateY(-50%);
  color: #94a3b8;
}

.search-input {
  width: 100%;
  padding: 12px 12px 12px 48px;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  outline: none;
  transition: 0.2s;
  font-size: 0.95rem;
}

.search-input:focus {
  border-color: #2563eb;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
}

.product-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 20px;
}

.product-card {
  background: white;
  border-radius: 16px;
  overflow: hidden;
  border: 1px solid #e2e8f0;
  cursor: pointer;
  position: relative;
  transition: 0.3s;
}

.product-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
}

.image-wrapper {
  position: relative;
  width: 100%;
  height: 200px;
}

.image-wrapper img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.stock-badge {
  position: absolute;
  bottom: 8px;
  right: 8px;
  background: rgba(0, 0, 0, 0.6);
  color: white;
  padding: 2px 8px;
  border-radius: 6px;
  font-size: 0.75rem;
  backdrop-filter: blur(4px);
}

.product-info {
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.product-name {
  font-weight: 600;
  color: #334155;
  font-size: 0.9rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.product-price {
  color: #2563eb;
  font-weight: 700;
  font-size: 1rem;
}

.add-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: 600;
  opacity: 0;
  transition: 0.2s;
}

.product-card:hover .add-overlay {
  opacity: 1;
}

/* Cart Section */
.cart-card {
  background: white;
  border-radius: 20px;
  border: 1px solid #e2e8f0;
  display: flex;
  flex-direction: column;
  min-height: 600px;
  max-height: calc(100vh - 200px);
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
}

.cart-header {
  padding: 24px;
  border-bottom: 1px solid #f1f5f9;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.cart-header h3 {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 700;
}

.item-count {
  background: #eff6ff;
  color: #2563eb;
  padding: 4px 10px;
  border-radius: 8px;
  font-size: 0.8rem;
  font-weight: 600;
}

.cart-items {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.empty-cart {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #94a3b8;
  height: 100%;
}

.empty-icon {
  font-size: 3rem;
  margin-bottom: 12px;
}

.cart-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px;
  background: #f8fafc;
  border-radius: 12px;
}

.item-thumb {
  width: 48px;
  height: 64px;
  object-fit: cover;
  border-radius: 6px;
}

.item-details {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.item-name {
  font-size: 0.85rem;
  font-weight: 600;
  color: #1e293b;
}

.item-price {
  font-size: 0.85rem;
  font-weight: 500;
  color: #64748b;
}

.btn-remove {
  background: none;
  border: none;
  color: #94a3b8;
  cursor: pointer;
  padding: 8px;
  transition: 0.2s;
}

.btn-remove:hover {
  color: #ef4444;
}

.cart-footer {
  padding: 24px;
  border-top: 1px solid #f1f5f9;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.summary-line {
  display: flex;
  justify-content: space-between;
  font-size: 0.9rem;
  color: #64748b;
}

.summary-line.total {
  font-size: 1.2rem;
  font-weight: 800;
  color: #1e293b;
  margin: 4px 0;
}

.btn-checkout {
  background: #2563eb;
  color: white;
  border: none;
  padding: 16px;
  border-radius: 12px;
  font-weight: 700;
  font-size: 1rem;
  cursor: pointer;
  transition: 0.3s;
}

.btn-checkout:hover:not(:disabled) {
  background: #1d4ed8;
  transform: translateY(-2px);
}

.btn-checkout:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* History Section */
.history-section {
  width: 100%;
}

.history-card {
  background: white;
  border-radius: 20px;
  border: 1px solid #e2e8f0;
  padding: 24px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
}

.history-table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 16px;
}

.history-table th {
  text-align: left;
  padding: 12px;
  background: #f8fafc;
  color: #64748b;
  font-size: 0.8rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  font-weight: 600;
}

.history-table td {
  padding: 16px 12px;
  border-bottom: 1px solid #f1f5f9;
  font-size: 0.9rem;
  color: #334155;
}

.order-id {
  font-weight: 700;
  color: #2563eb;
}

.type-badge {
  padding: 4px 10px;
  border-radius: 20px;
  font-size: 0.75rem;
  font-weight: 600;
}

.type-badge.sale { background: #dcfce7; color: #166534; }
.type-badge.rental { background: #fef9c3; color: #854d0e; }

.items-cell {
  max-width: 300px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  color: #64748b;
}

.text-right { text-align: right; }
.total-cell { font-weight: 700; color: #1e293b; }
.date-cell { color: #94a3b8; font-size: 0.85rem; }
</style>