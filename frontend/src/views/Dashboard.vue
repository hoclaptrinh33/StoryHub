<script setup lang="ts">
import { useRouter } from 'vue-router';
import DefaultLayout from '../components/layout/defaultLayout.vue';

const router = useRouter();

const navigateTo = (path: string) => {
  router.push(path);
};
</script>

<template>
  <DefaultLayout>
    <div class="dashboard-premium">
      <!-- Welcome Header -->
      <div class="welcome-header">
        <div class="title-meta">
          <h1 class="page-title">👋 Xin chào, AD!</h1>
          <p class="subtitle">Chào mừng bạn quay lại với hệ thống quản lý StoryHub</p>
        </div>
        
      </div>

      <!-- Quick Actions Glass Grid -->
      <div class="quick-actions-grid">
        <div class="action-card-lux sale" @click="navigateTo('/ban-hang')">
           <div class="card-glow"></div>
           <div class="icon-wrap"><span class="material-icons">shopping_bag</span></div>
           <div class="text">
              <span class="title">TẠO ĐƠN BÁN</span>
              <span class="desc">Bán truyện trực tiếp cho khách</span>
           </div>
           <span class="material-icons arrow">east</span>
        </div>
        <div class="action-card-lux rent" @click="navigateTo('/phieu-thue')">
           <div class="card-glow"></div>
           <div class="icon-wrap"><span class="material-icons">library_add</span></div>
           <div class="text">
              <span class="title">LẬP PHIẾU THUÊ</span>
              <span class="desc">Tạo hợp đồng thuê truyện mới</span>
           </div>
           <span class="material-icons arrow">east</span>
        </div>
        <div class="action-card-lux inventory" @click="navigateTo('/quan-ly')">
           <div class="card-glow"></div>
           <div class="icon-wrap"><span class="material-icons">inventory_2</span></div>
           <div class="text">
              <span class="title">QUẢN LÝ KHO</span>
              <span class="desc">Cập nhật danh mục truyện</span>
           </div>
           <span class="material-icons arrow">east</span>
        </div>
        <div class="action-card-lux customer" @click="navigateTo('/khach-hang')">
           <div class="card-glow"></div>
           <div class="icon-wrap"><span class="material-icons">groups</span></div>
           <div class="text">
              <span class="title">KHÁCH HÀNG</span>
              <span class="desc">Quản lý thông tin hội viên</span>
           </div>
           <span class="material-icons arrow">east</span>
        </div>
      </div>

      <!-- Overview Analytics Content -->
      <div class="analytics-row-dashboard">
        <div class="card-glass content-box main-report">
          <div class="box-header">
             <h3>🆕 Truyện Mới Cập Nhật</h3>
             <button class="btn-text">Xem tất cả</button>
          </div>
          <div class="mini-list">
             <div class="list-item-lux" v-for="i in 4" :key="i">
                <div class="book-preview"></div>
                <div class="info">
                   <span class="name">One Piece - Tập {{ 100 + i }}</span>
                   <span class="meta">Vừa nhập 2 giờ trước • 20 quyển</span>
                </div>
                <span class="tag-status new">Mới</span>
             </div>
          </div>
        </div>
        
        <div class="card-glass content-box alert-box">
          <div class="box-header">
             <h3>⚠️ Cảnh Báo Quá Hạn</h3>
             <span class="badge-alert">12 phiếu</span>
          </div>
          <div class="compact-alerts">
             <div class="alert-item-lux" v-for="i in 3" :key="i">
                <div class="alert-icon"><span class="material-icons">history_toggle_off</span></div>
                <div class="info">
                   <span class="user">Nguyễn Văn A - 0912xxx</span>
                   <span class="detail">Quá hạn 3 ngày (3 quyển)</span>
                </div>
                <button class="btn-contact"><span class="material-icons">call</span></button>
             </div>
          </div>
        </div>
      </div>

      <!-- Stats Footer Row -->
      <div class="stats-footer-glass">
        <div class="stat-item-lux">
           <span class="lbl">TỔNG SỐ TRUYỆN</span>
           <span class="val">1,247</span>
           <span class="trend pos">+12</span>
        </div>
        <div class="stat-item-lux">
           <span class="lbl">ĐANG CHO THUÊ</span>
           <span class="val">156</span>
           <span class="trend pos">+5</span>
        </div>
        <div class="stat-item-lux">
           <span class="lbl">PHIẾU ĐẶT HÔM NAY</span>
           <span class="val">42</span>
           <span class="trend neg">-2</span>
        </div>
        <div class="stat-item-lux highlight">
           <span class="lbl">DOANH THU NGÀY</span>
           <span class="val">2,450,000đ</span>
           <span class="indicator"></span>
        </div>
      </div>
    </div>
  </DefaultLayout>
</template>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

.dashboard-premium { 
  padding: 32px; 
  background: #fdfdfd; 
  min-height: 100vh;
  font-family: 'Plus Jakarta Sans', sans-serif;
}

/* Welcome Header */
.welcome-header { display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 40px; }
.page-title { font-size: 2.5rem; font-weight: 800; color: #0f172a; margin: 0; letter-spacing: -0.04em; }
.subtitle { color: #64748b; font-size: 1.1rem; margin-top: 6px; }
.current-shift-badge { background: white; padding: 12px 20px; border-radius: 16px; font-weight: 700; color: #6366f1; display: flex; align-items: center; gap: 10px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); border: 1px solid #f1f5f9; }

/* Quick Actions Grid */
.quick-actions-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 24px; margin-bottom: 40px; }
.action-card-lux { 
  background: white; border-radius: 28px; padding: 24px; position: relative; overflow: hidden;
  border: 1px solid #f1f5f9; cursor: pointer; transition: 0.4s cubic-bezier(0.2, 0.8, 0.2, 1);
  display: flex; flex-direction: column; gap: 16px; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.02);
}
.action-card-lux:hover { transform: translateY(-8px); box-shadow: 0 30px 40px -10px rgba(0,0,0,0.08); }

.card-glow { position: absolute; top: -50%; left: -50%; width: 200%; height: 200%; background: radial-gradient(circle, rgba(99, 102, 241, 0.05) 0%, transparent 70%); opacity: 0; transition: 0.3s; }
.action-card-lux:hover .card-glow { opacity: 1; }

.icon-wrap { width: 48px; height: 48px; border-radius: 14px; display: flex; align-items: center; justify-content: center; transition: 0.3s; }
.icon-wrap .material-icons { font-size: 24px; }

.action-card-lux.sale .icon-wrap { background: #eff6ff; color: #2563eb; }
.action-card-lux.rent .icon-wrap { background: #dcfce7; color: #059669; }
.action-card-lux.inventory .icon-wrap { background: #fef3c7; color: #d97706; }
.action-card-lux.customer .icon-wrap { background: #fdf2f8; color: #db2777; }

.action-card-lux .title { display: block; font-weight: 800; font-size: 1.15rem; color: #0f172a; letter-spacing: -0.02em; }
.action-card-lux .desc { font-size: 0.85rem; color: #94a3b8; font-weight: 600; }
.action-card-lux .arrow { position: absolute; right: 24px; bottom: 24px; color: #cbd5e1; transition: 0.3s; }
.action-card-lux:hover .arrow { color: #2563eb; transform: translateX(5px); }

/* Analytics Content */
.analytics-row-dashboard { display: grid; grid-template-columns: 2fr 1fr; gap: 24px; margin-bottom: 40px; }
.card-glass { background: white; border-radius: 32px; padding: 32px; border: 1px solid #f1f5f9; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.02); }

.box-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; }
.box-header h3 { font-size: 1.25rem; font-weight: 800; color: #1e293b; margin: 0; }
.btn-text { background: none; border: none; color: #6366f1; font-weight: 700; cursor: pointer; font-size: 0.85rem; }

.list-item-lux { display: flex; align-items: center; gap: 20px; padding: 12px; border-radius: 18px; transition: 0.2s; cursor: pointer; margin-bottom: 8px; }
.list-item-lux:hover { background: #f8fafc; }
.book-preview { width: 50px; height: 70px; border-radius: 8px; background: #f1f5f9; border: 1px solid #e2e8f0; }
.list-item-lux .info { flex: 1; display: flex; flex-direction: column; }
.list-item-lux .name { font-weight: 750; color: #1e293b; font-size: 0.95rem; }
.list-item-lux .meta { font-size: 0.75rem; color: #94a3b8; font-weight: 600; margin-top: 4px; }
.tag-status.new { background: #dcfce7; color: #059669; padding: 4px 10px; border-radius: 8px; font-size: 0.7rem; font-weight: 800; }

.badge-alert { background: #fee2e2; color: #dc2626; padding: 4px 12px; border-radius: 20px; font-size: 0.75rem; font-weight: 800; }
.alert-item-lux { display: flex; align-items: center; gap: 16px; padding: 14px; border-radius: 18px; border: 1.5px solid #f1f5f9; margin-bottom: 12px; }
.alert-icon { width: 40px; height: 40px; border-radius: 12px; background: #fff5f5; color: #ef4444; display: flex; align-items: center; justify-content: center; }
.alert-item-lux .info { flex: 1; }
.alert-item-lux .user { display: block; font-weight: 750; color: #1e293b; font-size: 0.85rem; }
.alert-item-lux .detail { font-size: 0.75rem; color: #94a3b8; font-weight: 600; }
.btn-contact { background: #f1f5f9; border: none; width: 32px; height: 32px; border-radius: 10px; color: #64748b; cursor: pointer; display: flex; align-items: center; justify-content: center; transition: 0.2s; }
.btn-contact:hover { background: #2563eb; color: white; }

/* Stats Footer */
.stats-footer-glass { display: grid; grid-template-columns: repeat(4, 1fr); gap: 24px; background: #0f172a; border-radius: 32px; padding: 40px; color: white; box-shadow: 0 30px 60px -12px rgba(15, 23, 42, 0.3); }
.stat-item-lux { display: flex; flex-direction: column; gap: 8px; position: relative; }
.stat-item-lux .lbl { font-size: 0.75rem; font-weight: 750; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em; }
.stat-item-lux .val { font-size: 1.8rem; font-weight: 900; letter-spacing: -0.02em; }
.stat-item-lux .trend { font-size: 0.75rem; font-weight: 800; display: inline-flex; align-items: center; gap: 4px; }
.stat-item-lux .trend.pos { color: #10b981; }
.stat-item-lux .trend.neg { color: #f43f5e; }

.stat-item-lux.highlight { background: rgba(255, 255, 255, 0.05); padding: 16px 24px; border-radius: 20px; margin: -16px; border: 1px solid rgba(255, 255, 255, 0.1); }
.stat-item-lux.highlight .lbl { color: #cbd5e1; }
.stat-item-lux.highlight .val { color: #38bdf8; }
.indicator { width: 8px; height: 8px; border-radius: 50%; background: #38bdf8; box-shadow: 0 0 15px #38bdf8; position: absolute; right: 0; top: 0; }

@media (max-width: 1200px) {
  .quick-actions-grid { grid-template-columns: 1fr 1fr; }
  .analytics-row-dashboard { grid-template-columns: 1fr; }
  .stats-footer-glass { grid-template-columns: 1fr 1fr; }
}
</style>