<template>
  <header class="navbar">
    <div class="top-row">
      <div class="logo">PHẦN MỀM QUẢN LÝ TRUYỆN TRANH</div>
      
    </div>
    <nav class="nav-links">
      <input type="text" placeholder="Tìm kiếm truyện, khách hàng..." class="search-bar" />
      <router-link to="/">TRANG CHỦ</router-link>
      <router-link to="/quan-ly">QUẢN LÝ</router-link>
      <router-link to="/ban-hang">BÁN HÀNG & CHO THUÊ</router-link>
      <router-link to="/hoan-tra">KIỂM ĐỊNH TRẢ</router-link>
      <router-link to="/khuyen-mai">KHUYẾN MÃI</router-link>
      <router-link to="/kho">KHO</router-link>
      <router-link to="/bao-cao">BÁO CÁO</router-link>
    </nav>
  </header>
</template>

<style scoped>
.navbar { 
  display: flex; 
  flex-direction: column; /* Xếp chồng theo cột */
  gap: 15px; 
  padding: 15px 20px; 
  border-bottom: 1px solid #ddd; 
  background: white; 
}

.top-row {
  display: flex;
  align-items: center;
  gap: 20px;
}

.logo {
  font-weight: 700;
  font-size: 1.1rem;
  color: #1e293b;
  white-space: nowrap; /* Giữ tiêu đề trên 1 dòng */
}

.search-bar { 
  padding: 8px 12px; 
  width: 350px; 
  border: 1px solid #ccc; 
  border-radius: 4px; 
}

.nav-links { 
  display: flex; 
  gap: 25px; 
  font-size: 0.9rem;
  font-weight: 500;
}

.nav-links a {
  text-decoration: none;
  color: #475569;
}

.nav-links a.router-link-exact-active {
  color: #2563eb; /* Màu khi đang ở trang đó */
  border-bottom: 2px solid #2563eb;
}
</style>