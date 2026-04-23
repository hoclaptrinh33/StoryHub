<template>
  <header class="navbar">
    <div class="top-row">
      <div class="logo">STORY<span>HUB</span> PRO</div>
      <div class="user-info" v-if="authStore.user">
        <div class="user-avatar">
          {{ authStore.user.username.charAt(0).toUpperCase() }}
        </div>
        <div class="user-details">
          <span class="user-name">{{ authStore.user.full_name || authStore.user.username }}</span>
          <span class="user-role">{{ getRoleText(authStore.user.role) }}</span>
        </div>
        <button @click="handleLogout" class="logout-btn" title="Đăng xuất">
          <span class="material-icons">logout</span>
        </button>
      </div>
    </div>
    <nav class="nav-links">
      <input type="text" placeholder="Tìm kiếm truyện, khách hàng..." class="search-bar" />
      <!-- Tất cả role đều thấy -->
      <router-link to="/">TRANG CHỦ</router-link>
      <router-link to="/ban-hang">BÁN HÀNG & CHO THUÊ</router-link>
      <router-link to="/hoan-tra">KIỂM ĐỊNH TRẢ</router-link>
      <!-- Chỉ manager và owner -->
      <router-link v-if="isManagerOrOwner" to="/khuyen-mai">KHUYẾN MÃI</router-link>
      <router-link v-if="isManagerOrOwner" to="/kho">KHO</router-link>
      <router-link v-if="isManagerOrOwner" to="/bao-cao">BÁO CÁO</router-link>
      <router-link v-if="isManagerOrOwner" to="/khach-hang">KHÁCH HÀNG</router-link>
      <router-link v-if="isManagerOrOwner" to="/quan-ly">QUẢN LÝ</router-link>
    </nav>
  </header>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../../stores/auth'

const router = useRouter()
const authStore = useAuthStore()

// Kiểm tra role để ẩn/hiện menu
const isManagerOrOwner = computed(() =>
  authStore.user?.role === 'manager' || authStore.user?.role === 'owner'
)
const isOwner = computed(() =>
  authStore.user?.role === 'owner'
)

function getRoleText(role: string) {
  const map: Record<string, string> = {
    owner: 'Chủ sở hữu',
    manager: 'Quản lý',
    cashier: 'Thu ngân'
  }
  return map[role] || role
}

function handleLogout() {
  authStore.clearAuth()
  router.push('/login')
}
</script>

<style scoped>
.navbar { 
  display: flex; 
  flex-direction: column; 
  gap: 15px; 
  padding: 15px 25px; 
  border-bottom: 1px solid #e2e8f0; 
  background: white; 
  box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}

.top-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
}

.logo {
  font-weight: 800;
  font-size: 1.25rem;
  color: #1e293b;
  letter-spacing: -0.5px;
}

.logo span {
  color: #4f46e5;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 4px 4px 4px 12px;
  background: #f8fafc;
  border-radius: 999px;
  border: 1px solid #f1f5f9;
}

.user-avatar {
  width: 32px;
  height: 32px;
  background: #4f46e5;
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 14px;
}

.user-details {
  display: flex;
  flex-direction: column;
}

.user-name {
  font-size: 14px;
  font-weight: 600;
  color: #1e293b;
}

.user-role {
  font-size: 11px;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.logout-btn {
  background: white;
  border: 1px solid #e2e8f0;
  color: #64748b;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
}

.logout-btn:hover {
  background: #fef2f2;
  border-color: #fecaca;
  color: #ef4444;
}

.logout-btn .material-icons {
  font-size: 18px;
}

.search-bar { 
  padding: 10px 16px; 
  width: 350px; 
  border: 1px solid #e2e8f0; 
  border-radius: 10px; 
  background: #f8fafc;
  font-size: 14px;
  outline: none;
  transition: border-color 0.2s;
}

.search-bar:focus {
  border-color: #4f46e5;
  background: white;
}

.nav-links { 
  display: flex; 
  align-items: center;
  gap: 30px; 
  font-size: 0.85rem;
  font-weight: 700;
}

.nav-links a {
  text-decoration: none;
  color: #64748b;
  transition: color 0.2s;
}

.nav-links a:hover {
  color: #1e293b;
}

.nav-links a.router-link-exact-active {
  color: #4f46e5; 
  position: relative;
}

.nav-links a.router-link-exact-active::after {
  content: '';
  position: absolute;
  bottom: -4px;
  left: 0;
  right: 0;
  height: 2px;
  background: #4f46e5;
  border-radius: 2px;
}
</style>