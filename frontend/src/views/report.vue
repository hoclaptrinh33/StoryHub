<template>
  <DefaultLayout>
    <div class="reports-container">
      <!-- Header Section -->
      <div class="header-section">
        <div class="title-meta">
          <h2 class="page-title">📊 Báo cáo Kinh doanh</h2>
          <p class="subtitle">Phân tích chuyên sâu hiệu suất cửa hàng & xu hướng khách hàng</p>
        </div>
        <div class="date-range-glass">
          <div class="date-inputs">
            <div class="input-with-label">
              <label>Từ ngày</label>
              <input type="date" v-model="dateFrom" />
            </div>
            <div class="input-with-label">
              <label>Đến ngày</label>
              <input type="date" v-model="dateTo" />
            </div>
          </div>
          <button class="btn-refresh" @click="refreshData">
            <span class="material-icons" :class="{ rotating: isRefreshing }">sync</span>
          </button>
        </div>
      </div>

      <!-- Hero Stats Grid -->
      <div class="stats-grid-premium">
        <div class="stat-card-lux revenue">
          <div class="card-bg-icon">💰</div>
          <div class="card-content">
            <div class="label">Tổng doanh thu</div>
            <div class="value">{{ formatCurrency(totalRevenue) }}</div>
            <div class="footer">
              <span class="trend up">
                <span class="material-icons">trending_up</span> +12.5%
              </span>
              <span class="meta">so với tháng trước</span>
            </div>
          </div>
        </div>
        <div class="stat-card-lux rental">
          <div class="card-bg-icon">📚</div>
          <div class="card-content">
            <div class="label">Tổng lượt thuê</div>
            <div class="value">{{ totalRentals }}</div>
            <div class="footer">
              <span class="trend up">
                <span class="material-icons">arrow_upward</span> +8.2%
              </span>
              <span class="meta">tăng trưởng</span>
            </div>
          </div>
        </div>
        <div class="stat-card-lux sale">
          <div class="card-bg-icon">🛒</div>
          <div class="card-content">
            <div class="label">Số bản bán ra</div>
            <div class="value">{{ totalSales }}</div>
            <div class="footer">
              <span class="trend down">
                <span class="material-icons">trending_down</span> -2.1%
              </span>
              <span class="meta">biến động</span>
            </div>
          </div>
        </div>
        <div class="stat-card-lux user">
          <div class="card-bg-icon">👥</div>
          <div class="card-content">
            <div class="label">Khách hàng mới</div>
            <div class="value">{{ newCustomers }}</div>
            <div class="footer">
              <span class="trend up">
                <span class="material-icons">person_add</span> +5.4%
              </span>
              <span class="meta">đang mở rộng</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Main Analytics Row -->
      <div class="analytics-row">
        <div class="card-glass main-chart">
          <div class="card-header-lux">
            <h3>📈 Doanh thu & Tăng trưởng</h3>
            <div class="chart-legend">
              <span class="legend-item"><span class="dot primary"></span> Thực tế</span>
              <span class="legend-item"><span class="dot ghost"></span> Dự báo</span>
            </div>
          </div>
          <div class="chart-container">
            <canvas id="revenueChart" ref="revenueChartRef"></canvas>
          </div>
        </div>
        
        <div class="card-glass side-chart">
          <div class="card-header-lux">
            <h3>🔥 Top 5 Bộ truyện</h3>
          </div>
          <div class="chart-container compact">
            <canvas id="topSellingChart" ref="topSellingChartRef"></canvas>
          </div>
        </div>
      </div>

      <div class="analytics-row secondary">
        <div class="card-glass third">
          <div class="card-header-lux">
             <h3>🧩 Cơ cấu Doanh thu</h3>
          </div>
          <div class="chart-container pie">
            <canvas id="contributionChart" ref="contributionChartRef"></canvas>
          </div>
        </div>
        <div class="card-glass third">
          <div class="card-header-lux">
             <h3>📦 Tình trạng Kho hàng</h3>
          </div>
          <div class="chart-container pie">
            <canvas id="inventoryChart" ref="inventoryChartRef"></canvas>
          </div>
        </div>
        <div class="card-glass third extra-metrics">
          <div class="card-header-lux">
            <h3>✨ Chỉ số vận hành</h3>
          </div>
          <div class="metrics-list">
             <div class="metric-item">
               <div class="icon-wrap profit"><span class="material-icons">payments</span></div>
               <div class="info">
                 <span class="lbl">Lợi nhuận ròng</span>
                 <span class="val">{{ formatCurrency(netProfit) }}</span>
               </div>
             </div>
             <div class="metric-item">
               <div class="icon-wrap late"><span class="material-icons">history_toggle_off</span></div>
               <div class="info">
                 <span class="lbl">Tỷ lệ trả trễ</span>
                 <span class="val">{{ lateReturnRate }}%</span>
               </div>
             </div>
             <div class="metric-item">
               <div class="icon-wrap stock"><span class="material-icons">inventory_2</span></div>
               <div class="info">
                 <span class="lbl">Sắp hết hàng</span>
                 <span class="val">{{ lowStockItems }} mặt hàng</span>
               </div>
             </div>
             <div class="metric-item">
               <div class="icon-wrap star"><span class="material-icons">stars</span></div>
               <div class="info">
                 <span class="lbl">Đánh giá chung</span>
                 <span class="val">4.8 / 5.0</span>
               </div>
             </div>
          </div>
        </div>
      </div>

      <!-- Ranking Tables Section -->
      <div class="ranking-section">
        <div class="card-glass ranking-card">
          <div class="card-header-lux">
            <h3>🏆 Khách hàng Thân thiết</h3>
          </div>
          <div class="table-lux">
            <table>
              <thead>
                <tr>
                  <th>Khách hàng</th>
                  <th class="text-center">Số giao dịch</th>
                  <th class="text-right">Tổng chi tiêu</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(c, idx) in topCustomers" :key="c.id">
                  <td>
                    <div class="member-info">
                      <span class="rank" :class="'rank-' + (idx + 1)">#{{ idx + 1 }}</span>
                      <span class="name">{{ c.name }}</span>
                    </div>
                  </td>
                  <td class="text-center"><strong>{{ c.totalTransactions }}</strong></td>
                  <td class="text-right"><span class="amount-tag">{{ formatCurrency(c.totalSpent) }}</span></td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div class="card-glass ranking-card">
          <div class="card-header-lux">
            <h3>🔥 Truyện bán chạy nhất</h3>
          </div>
          <div class="table-lux">
            <table>
              <thead>
                <tr>
                  <th>Bộ truyện</th>
                  <th class="text-center">Thuê / Bán</th>
                  <th class="text-right">Doanh thu</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="book in hotBooks" :key="book.id">
                  <td><strong>{{ book.name }}</strong></td>
                  <td class="text-center">
                    <span class="sub-stats">{{ book.rentCount }} <span class="material-icons xsmall">auto_stories</span></span>
                    <span class="separator">|</span>
                    <span class="sub-stats">{{ book.sellCount }} <span class="material-icons xsmall">shopping_bag</span></span>
                  </td>
                  <td class="text-right"><span class="amount-tag primary">{{ formatCurrency(book.revenue) }}</span></td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  </DefaultLayout>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue';
import DefaultLayout from '../components/layout/defaultLayout.vue';
import { Chart, registerables } from 'chart.js';
Chart.register(...registerables);

// ================== DATA & STATE ==================

const dateFrom = ref('2026-03-01');
const dateTo = ref('2026-04-17');
const isRefreshing = ref(false);

const totalRevenue = ref(187500000);
const totalRentals = ref(342);
const totalSales = ref(156);
const newCustomers = ref(28);
const netProfit = ref(42500000);
const lateReturnRate = ref(7.2);
const lowStockItems = ref(5);

const topCustomers = ref([
  { id: 1, name: 'Nguyễn Văn A', totalTransactions: 12, totalSpent: 3250000 },
  { id: 2, name: 'Trần Thị B', totalTransactions: 9, totalSpent: 2780000 },
  { id: 3, name: 'Lê Văn C', totalTransactions: 7, totalSpent: 1950000 },
]);

const hotBooks = ref([
  { id: 1, name: 'One Piece Tập 105', rentCount: 45, sellCount: 32, revenue: 12500000 },
  { id: 2, name: 'Conan Tập 98', rentCount: 38, sellCount: 28, revenue: 9800000 },
  { id: 3, name: 'Jujutsu Kaisen Tập 20', rentCount: 30, sellCount: 25, revenue: 8700000 },
  { id: 4, name: 'Spy x Family Tập 10', rentCount: 27, sellCount: 22, revenue: 7600000 },
]);

// Chart References
let charts: Chart[] = [];
const revenueChartRef = ref<HTMLCanvasElement>();
const topSellingChartRef = ref<HTMLCanvasElement>();
const contributionChartRef = ref<HTMLCanvasElement>();
const inventoryChartRef = ref<HTMLCanvasElement>();

// ================== METHODS ==================

const formatCurrency = (value: number) => {
  return new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(value);
};

const refreshData = async () => {
  isRefreshing.value = true;
  // Giả lập loading
  await new Promise(r => setTimeout(r, 800));
  updateCharts();
  isRefreshing.value = false;
};

const updateCharts = () => {
  // Clear existing charts
  charts.forEach(c => c.destroy());
  charts = [];

  // Common font config
  const fontConfig = { family: "'Plus Jakarta Sans', sans-serif", weight: '600' };

  // 1. Line Chart: Revenue
  if (revenueChartRef.value) {
    const ctx = revenueChartRef.value.getContext('2d');
    if (ctx) {
      const gradient = ctx.createLinearGradient(0, 0, 0, 400);
      gradient.addColorStop(0, 'rgba(37, 99, 235, 0.4)');
      gradient.addColorStop(1, 'rgba(37, 99, 235, 0)');

      const c = new Chart(ctx, {
        type: 'line',
        data: {
          labels: ['10/4', '11/4', '12/4', '13/4', '14/4', '15/4', '16/4'],
          datasets: [{
            label: 'Doanh thu',
            data: [12500000, 18200000, 14700000, 21000000, 19800000, 23500000, 27800000],
            borderColor: '#2563eb',
            borderWidth: 4,
            pointBackgroundColor: '#fff',
            pointBorderColor: '#2563eb',
            pointBorderWidth: 2,
            pointRadius: 6,
            pointHoverRadius: 8,
            fill: true,
            backgroundColor: gradient,
            tension: 0.4
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: { 
            legend: { display: false },
            tooltip: { 
              backgroundColor: '#0f172a',
              padding: 12,
              titleFont: {...fontConfig, size: 14},
              bodyFont: {...fontConfig, size: 13},
              callbacks: { label: (ctx: any) => `Doanh thu: ${formatCurrency(ctx.raw as number)}` } 
            }
          },
          scales: {
            y: {
              grid: { color: 'rgba(0,0,0,0.05)' },
              ticks: { font: fontConfig, callback: (v: any) => v.toLocaleString() + 'đ' }
            },
            x: { grid: { display: false }, ticks: { font: fontConfig } }
          }
        }
      });
      charts.push(c);
    }
  }

  // 2. Bar Chart: Top Selling
  if (topSellingChartRef.value) {
    const c = new Chart(topSellingChartRef.value, {
      type: 'bar',
      data: {
        labels: ['O.Piece', 'Conan', 'Jujutsu', 'Spy x', 'Demon'],
        datasets: [{
          label: 'Số bản',
          data: [32, 28, 25, 22, 18],
          backgroundColor: '#f97316',
          borderRadius: 8,
          barThickness: 24
        }]
      },
      options: {
        indexAxis: 'y',
        responsive: true,
        plugins: { legend: { display: false } },
        scales: { 
          x: { grid: { display: false } }, 
          y: { grid: { display: false }, ticks: { font: fontConfig } } 
        }
      }
    });
    charts.push(c);
  }

  // 3. Doughnut: Genre Contribution
  if (contributionChartRef.value) {
    const c = new Chart(contributionChartRef.value, {
      type: 'doughnut',
      data: {
        labels: ['Hành động', 'Trinh thám', 'Hài hước', 'Kinh dị'],
        datasets: [{
          data: [78000000, 52000000, 34000000, 18000000],
          backgroundColor: ['#3b82f6', '#10b981', '#f59e0b', '#ef4444'],
          borderWidth: 0,
          cutout: '70%'
        }]
      },
      options: {
        responsive: true,
        plugins: { 
          legend: { position: 'bottom', labels: { font: fontConfig, usePointStyle: true, pointStyle: 'circle' } } 
        }
      }
    });
    charts.push(c);
  }

  // 4. Pie: Inventory
  if (inventoryChartRef.value) {
    const c = new Chart(inventoryChartRef.value, {
      type: 'pie',
      data: {
        labels: ['Mới', 'Tốt', 'Cũ', 'Lỗi'],
        datasets: [{
          data: [1240, 560, 230, 45],
          backgroundColor: ['#22c55e', '#eab308', '#f97316', '#ef4444'],
          borderWidth: 0
        }]
      },
      options: {
        responsive: true,
        plugins: { 
          legend: { position: 'bottom', labels: { font: fontConfig, usePointStyle: true, pointStyle: 'circle' } } 
        }
      }
    });
    charts.push(c);
  }
};

onMounted(() => {
  nextTick(() => {
    updateCharts();
  });
});
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

.reports-container { 
  padding: 32px; 
  background: #f8fafc; 
  min-height: 100vh; 
  font-family: 'Plus Jakarta Sans', sans-serif;
}

/* Header & Meta */
.header-section { display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 40px; }
.page-title { font-size: 2.25rem; font-weight: 800; color: #0f172a; letter-spacing: -0.04em; margin-bottom: 4px; }
.subtitle { color: #64748b; font-size: 1rem; margin: 0; }

.date-range-glass { 
  background: white; 
  padding: 12px 24px; 
  border-radius: 24px; 
  display: flex; 
  align-items: center; 
  gap: 20px; 
  box-shadow: 0 10px 15px -3px rgba(0,0,0,0.05);
  border: 1px solid #f1f5f9;
}
.date-inputs { display: flex; gap: 16px; }
.input-with-label label { display: block; font-size: 0.7rem; font-weight: 800; color: #94a3b8; text-transform: uppercase; margin-bottom: 4px; }
.input-with-label input { border: none; background: #f8fafc; padding: 6px 12px; border-radius: 10px; font-weight: 600; font-family: inherit; color: #1e293b; outline: none; }
.btn-refresh { width: 44px; height: 44px; border-radius: 14px; border: none; background: #2563eb; color: white; cursor: pointer; display: flex; align-items: center; justify-content: center; transition: 0.3s; }
.btn-refresh:hover { transform: rotate(180deg); background: #1d4ed8; }
.rotating { animation: spin 1s infinite linear; }

/* Stats Hero */
.stats-grid-premium { display: grid; grid-template-columns: repeat(4, 1fr); gap: 24px; margin-bottom: 40px; }
.stat-card-lux { 
  background: white; border-radius: 28px; padding: 28px; position: relative; overflow: hidden;
  box-shadow: 0 20px 25px -5px rgba(0,0,0,0.03); border: 1px solid #f1f5f9; transition: 0.3s;
}
.stat-card-lux:hover { transform: translateY(-5px); box-shadow: 0 30px 40px -10px rgba(0,0,0,0.08); }

.card-bg-icon { position: absolute; right: -10px; top: -10px; font-size: 6rem; opacity: 0.05; }
.stat-card-lux .label { font-size: 0.85rem; font-weight: 700; color: #64748b; margin-bottom: 12px; }
.stat-card-lux .value { font-size: 2rem; font-weight: 900; color: #0f172a; margin-bottom: 12px; letter-spacing: -0.02em; }
.stat-card-lux .footer { display: flex; align-items: center; gap: 8px; }
.stat-card-lux .trend { font-size: 0.8rem; font-weight: 800; display: flex; align-items: center; gap: 2px; }
.stat-card-lux .trend.up { color: #059669; }
.stat-card-lux .trend.down { color: #dc2626; }
.stat-card-lux .meta { font-size: 0.75rem; color: #94a3b8; font-weight: 500; }

/* Charts Layout */
.analytics-row { display: grid; grid-template-columns: 2fr 1fr; gap: 24px; margin-bottom: 24px; }
.analytics-row.secondary { grid-template-columns: repeat(3, 1fr); }
.card-glass { background: white; border-radius: 32px; padding: 32px; border: 1px solid #f1f5f9; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.04); }

.card-header-lux { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; }
.card-header-lux h3 { font-size: 1.25rem; font-weight: 800; color: #0f172a; margin: 0; }

.chart-legend { display: flex; gap: 16px; }
.legend-item { font-size: 0.8rem; font-weight: 700; display: flex; align-items: center; gap: 6px; color: #64748b; }
.dot { width: 8px; height: 8px; border-radius: 50%; }
.dot.primary { background: #2563eb; }
.dot.ghost { background: #e2e8f0; }

.chart-container { height: 350px; position: relative; }
.chart-container.compact { height: 300px; }
.chart-container.pie { height: 280px; }

/* Metrics List */
.metrics-list { display: flex; flex-direction: column; gap: 16px; }
.metric-item { display: flex; align-items: center; gap: 16px; padding: 12px; background: #f8fafc; border-radius: 20px; transition: 0.2s; }
.metric-item:hover { background: #f1f5f9; }
.icon-wrap { width: 44px; height: 44px; border-radius: 12px; display: flex; align-items: center; justify-content: center; }
.icon-wrap .material-icons { font-size: 20px; }
.icon-wrap.profit { background: #dcfce7; color: #059669; }
.icon-wrap.late { background: #fef3c7; color: #d97706; }
.icon-wrap.stock { background: #fee2e2; color: #dc2626; }
.icon-wrap.star { background: #eff6ff; color: #2563eb; }

.metric-item .lbl { display: block; font-size: 0.75rem; font-weight: 700; color: #94a3b8; text-transform: uppercase; }
.metric-item .val { font-size: 1.1rem; font-weight: 800; color: #0f172a; }

/* Ranking Section */
.ranking-section { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; }
.ranking-card { padding: 32px 0; }
.ranking-card .card-header-lux { padding: 0 32px; }

.table-lux table { width: 100%; border-collapse: collapse; }
.table-lux th { padding: 16px 32px; text-align: left; font-size: 0.75rem; color: #94a3b8; font-weight: 800; text-transform: uppercase; border-bottom: 1px solid #f1f5f9; }
.table-lux td { padding: 16px 32px; color: #1e293b; border-bottom: 1px solid #f1f5f9; font-size: 0.95rem; }
.table-lux tr:last-child td { border-bottom: none; }
.table-lux tr:hover td { background: #f8fafc; }

.member-info { display: flex; align-items: center; gap: 12px; }
.rank { padding: 4px 10px; border-radius: 8px; font-weight: 800; font-size: 0.75rem; }
.rank-1 { background: #fef9c3; color: #a16207; }
.rank-2 { background: #f1f5f9; color: #475569; }
.rank-3 { background: #ffedd5; color: #9a3412; }

.amount-tag { background: #f1f5f9; color: #475569; padding: 6px 12px; border-radius: 12px; font-weight: 700; font-size: 0.85rem; }
.amount-tag.primary { background: #eff6ff; color: #2563eb; }

.sub-stats { font-weight: 800; color: #475569; display: inline-flex; align-items: center; gap: 4px; }
.material-icons.xsmall { font-size: 14px; }
.separator { margin: 0 8px; color: #e2e8f0; }

@keyframes spin { 100% { transform: rotate(360deg); } }

@media (max-width: 1200px) {
  .stats-grid-premium { grid-template-columns: 1fr 1fr; }
  .analytics-row { grid-template-columns: 1fr; }
  .analytics-row.secondary { grid-template-columns: 1fr; }
  .ranking-section { grid-template-columns: 1fr; }
}
</style>