<script setup lang="ts">
import DefaultLayout from '../components/layout/defaultLayout.vue'
</script>

<template>
  <DefaultLayout>
    <div class="dashboard">
      <div class="actions-container">
        <div class="main-actions">
            <button class="btn-main primary">+ TẠO ĐƠN MỚI (BÁN)</button>
            <button class="btn-main success">+ TẠO PHIẾU THUÊ MỚI</button>
        </div>
        
        <div class="secondary-actions">
            <button class="btn-outline">Quản lý truyện</button>
            <button class="btn-outline">Quản lý khách hàng</button>
        </div>
    </div>
      <div class="content-split">
        <section class="card">
          <h3>TRUYỆN MỚI NHẬP</h3>
        </section>
        <section class="card">
          <h3>TRUYỆN QUÁ HẠN TRẢ</h3>
        </section>
      </div>

      <section class="stats-footer">
        <div class="stat-card"><span>TỔNG SỐ TRUYỆN</span> <strong>1,247</strong></div>
        <div class="stat-card"><span>ĐANG CHO THUÊ</span> <strong>156</strong></div>
        <div class="stat-card"><span>DOANH THU HÔM NAY</span> <strong>2,450,000đ</strong></div>
      </section>
    </div>
  </DefaultLayout>
</template>

<style scoped>
.dashboard { padding: 20px; background: #f8fafc; min-height: 100vh; }

.navbar { display: flex; align-items: center; gap: 20px; padding-bottom: 20px; border-bottom: 1px solid #ddd; }
.search-bar { padding: 8px; width: 300px; border: 1px solid #ccc; border-radius: 4px; }
.actions-container {
  display: flex;
  gap: 20px; /* Khoảng cách giữa nhóm trái và nhóm phải */
  margin: 20px 0;
}

.main-actions, .secondary-actions {
  display: flex;
  flex: 1; /* Chia đôi màn hình: 50% cho nhóm trái, 50% cho nhóm phải */
  gap: 15px;
}

/* Ép tất cả các nút có độ rộng bằng nhau trong nhóm của chúng */
.main-actions button, 
.secondary-actions button {
  flex: 1;
  padding: 15px;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
  font-weight: 600;
  cursor: pointer;
}

/* Tùy chỉnh màu sắc */
.primary { background: #2563eb; color: white; border: none; }
.success { background: #059669; color: white; border: none; }
.btn-outline { background: white; color: #374151; }


/* Tăng trải nghiệm người dùng bằng cách thêm hiệu ứng hover */
.btn-main:hover { opacity: 0.9; transform: translateY(-1px); transition: 0.2s; }
.btn-outline:hover { background: #f0f0f0; }.btn-main { padding: 15px 25px; border-radius: 6px; border: none; color: white; font-weight: bold; cursor: pointer; }
.primary { background: #1e40af; }
.success { background: #059669; }
.btn-outline { padding: 10px 20px; border: 1px solid #ccc; background: white; cursor: pointer; }

.content-split { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px; }
.card { background: white; padding: 20px; border: 1px solid #eee; border-radius: 8px; }

.stats-footer { display: flex; gap: 20px; }
.stat-card { background: white; padding: 20px; flex: 1; border: 1px solid #eee; border-radius: 8px; display: flex; flex-direction: column; }
</style>