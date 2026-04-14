<template>
  <header class="navbar">
    <div class="logo">PHẦN MỀM QUẢN LÝ TRUYỆN TRANH</div>
    <input type="text" placeholder="Tìm kiếm truyện, khách hàng..." class="search-bar" />
    <nav class="nav-links">
      <router-link to="/">TRANG CHỦ</router-link>
      <router-link to="/manage">QUẢN LÝ</router-link>
      </nav>
  </header>
</template>

<style scoped>
.navbar { 
  display: flex; align-items: center; gap: 20px; 
  padding: 15px 20px; border-bottom: 1px solid #ddd; 
  background: white; 
}
.search-bar { padding: 8px; width: 300px; border: 1px solid #ccc; border-radius: 4px; }
.nav-links { display: flex; gap: 15px; cursor: pointer; }
</style>