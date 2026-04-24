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
          <button class="btn-refresh" :disabled="isRefreshing" @click="refreshData">
            <span class="material-icons" :class="{ rotating: isRefreshing }">sync</span>
          </button>
        </div>
      </div>

      <p v-if="reportError" class="report-error-banner">{{ reportError }}</p>

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

      <div class="card-glass backup-panel">
        <div class="card-header-lux">
          <h3>🛡️ Backup hệ thống</h3>
          <button class="backup-btn ghost" :disabled="isBackupLoading" @click="refreshBackupStatus">
            Làm mới trạng thái
          </button>
        </div>

        <div class="backup-actions">
          <button class="backup-btn primary" :disabled="isBackupLoading" @click="triggerBackup('full')">
            Tạo Full Backup
          </button>
          <button
            class="backup-btn"
            :disabled="isBackupLoading"
            @click="triggerBackup('incremental')"
          >
            Tạo Incremental
          </button>
        </div>

        <p v-if="backupNotice" class="backup-banner success">{{ backupNotice }}</p>
        <p v-if="backupError" class="backup-banner error">{{ backupError }}</p>

        <div v-if="latestBackup" class="backup-meta-grid">
          <div>
            <span class="meta-label">Job ID</span>
            <strong>{{ latestBackup.backup_job_id }}</strong>
          </div>
          <div>
            <span class="meta-label">Loại</span>
            <strong>{{ latestBackup.backup_type }}</strong>
          </div>
          <div>
            <span class="meta-label">Trạng thái</span>
            <strong>{{ latestBackup.status }}</strong>
          </div>
          <div>
            <span class="meta-label">Checksum</span>
            <strong>{{ latestBackup.checksum || '-' }}</strong>
          </div>
          <div>
            <span class="meta-label">File</span>
            <strong>{{ latestBackup.file_path || '-' }}</strong>
          </div>
          <div>
            <span class="meta-label">Thời gian</span>
            <strong>{{ formatDateTime(latestBackup.created_at) }}</strong>
          </div>
        </div>
        <p v-else class="backup-empty">Chưa có backup nào được ghi nhận.</p>
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
                <tr v-if="topCustomers.length === 0">
                  <td colspan="3" class="text-center table-empty">Chưa có dữ liệu khách hàng trong giai đoạn đã chọn.</td>
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
                <tr v-if="hotBooks.length === 0">
                  <td colspan="3" class="text-center table-empty">Chưa có dữ liệu bán/thuê trong giai đoạn đã chọn.</td>
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
import { computed, nextTick, onMounted, ref } from "vue";
import DefaultLayout from '../components/layout/defaultLayout.vue';
import { Chart, registerables } from 'chart.js';
import {
  StoryHubApiError,
  buildRequestId,
  createSystemBackup,
  fetchLatestSystemBackup,
  fetchRevenueSummaryReport,
  type LatestBackupPayload,
  type ReportTopCustomer,
  type RevenueTopTitle,
} from "../services/storyhubApi";

Chart.register(...registerables);

type TopCustomer = {
  id: number;
  name: string;
  totalTransactions: number;
  totalSpent: number;
};

type HotBook = {
  id: number;
  name: string;
  rentCount: number;
  sellCount: number;
  revenue: number;
};

// ================== STATE ==================

const toDateInputValue = (date: Date) => {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
};

const today = new Date();
const startOfMonth = new Date(today.getFullYear(), today.getMonth(), 1);

const dateFrom = ref(toDateInputValue(startOfMonth));
const dateTo = ref(toDateInputValue(today));
const isRefreshing = ref(false);
const reportError = ref("");

const sellRevenue = ref(0);
const rentalRevenue = ref(0);
const penaltyRevenue = ref(0);
const totalRevenue = computed(() => sellRevenue.value + rentalRevenue.value + penaltyRevenue.value);

const totalRentals = ref(0);
const totalSales = ref(0);
const newCustomers = ref(0);
const netProfit = computed(() => Math.round(totalRevenue.value * 0.3));
const lateReturnRate = computed(() => {
  if (totalRevenue.value <= 0) {
    return 0;
  }
  return Number(((penaltyRevenue.value / totalRevenue.value) * 100).toFixed(1));
});
const lowStockItems = ref(0);

const backupError = ref("");
const backupNotice = ref("");
const isBackupLoading = ref(false);
const latestBackup = ref<LatestBackupPayload | null>(null);

const topCustomers = ref<TopCustomer[]>([]);

const hotBooks = ref<HotBook[]>([]);

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

const formatDateTime = (value?: string | null) => {
  if (!value) {
    return "-";
  }
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value;
  }
  return parsed.toLocaleString("vi-VN");
};

const toUtcIsoRange = (dateValue: string, endOfDay: boolean) => {
  const normalized = dateValue.trim();
  if (!normalized) {
    return "";
  }
  return endOfDay
    ? `${normalized}T23:59:59Z`
    : `${normalized}T00:00:00Z`;
};

const toHotBooks = (topSellTitles: RevenueTopTitle[], topRentTitles: RevenueTopTitle[]) => {
  const map = new Map<string, HotBook>();

  const ensure = (title: string) => {
    const key = title.trim();
    if (!map.has(key)) {
      map.set(key, {
        id: map.size + 1,
        name: key,
        rentCount: 0,
        sellCount: 0,
        revenue: 0,
      });
    }
    return map.get(key)!;
  };

  for (const item of topSellTitles) {
    const entry = ensure(item.title);
    entry.sellCount = item.qty;
    entry.revenue += item.revenue;
  }

  for (const item of topRentTitles) {
    const entry = ensure(item.title);
    entry.rentCount = item.qty;
    entry.revenue += item.revenue;
  }

  return Array.from(map.values())
    .sort((a, b) => b.revenue - a.revenue || b.sellCount + b.rentCount - (a.sellCount + a.rentCount))
    .slice(0, 5)
    .map((item, index) => ({ ...item, id: index + 1 }));
};

const toTopCustomers = (rows: ReportTopCustomer[]) => {
  return rows.map((row) => ({
    id: row.id,
    name: row.name,
    totalTransactions: row.total_transactions,
    totalSpent: row.total_spent,
  }));
};

const getApiErrorMessage = (error: unknown, fallback: string) => {
  if (error instanceof StoryHubApiError) {
    return error.message;
  }
  return fallback;
};

const refreshData = async () => {
  reportError.value = "";

  if (dateFrom.value > dateTo.value) {
    reportError.value = "Khoảng ngày báo cáo không hợp lệ.";
    return;
  }

  isRefreshing.value = true;
  try {
    const payload = await fetchRevenueSummaryReport({
      from_date: toUtcIsoRange(dateFrom.value, false),
      to_date: toUtcIsoRange(dateTo.value, true),
      group_by: "day",
      include_top_titles: true,
      include_inventory_alert: true,
      request_id: buildRequestId("report-revenue-summary"),
    });

    sellRevenue.value = payload.sell_revenue;
    rentalRevenue.value = payload.rental_revenue;
    penaltyRevenue.value = payload.penalty_revenue;

    totalSales.value = payload.sold_items;
    totalRentals.value = payload.rented_items;
    newCustomers.value = payload.new_customers;
    lowStockItems.value = payload.inventory_alerts.length;
    hotBooks.value = toHotBooks(payload.top_sell_titles, payload.top_rent_titles);
    topCustomers.value = toTopCustomers(payload.top_customers);

    await nextTick();
    updateCharts();
  } catch (error: unknown) {
    reportError.value = getApiErrorMessage(error, "Không thể tải dữ liệu báo cáo.");
  } finally {
    isRefreshing.value = false;
  }
};

const refreshBackupStatus = async () => {
  backupError.value = "";
  try {
    latestBackup.value = await fetchLatestSystemBackup();
  } catch (error: unknown) {
    if (error instanceof StoryHubApiError && error.code === "BACKUP_NOT_FOUND") {
      latestBackup.value = null;
      return;
    }
    backupError.value = getApiErrorMessage(error, "Không thể đọc trạng thái backup gần nhất.");
  }
};

const triggerBackup = async (backupType: "full" | "incremental") => {
  backupError.value = "";
  backupNotice.value = "";
  isBackupLoading.value = true;
  try {
    const payload = await createSystemBackup({
      backup_type: backupType,
      request_id: buildRequestId(`backup-${backupType}`),
    });
    backupNotice.value = `Đã tạo ${payload.backup_job_id} (${backupType}) thành công.`;
    await refreshBackupStatus();
  } catch (error: unknown) {
    backupError.value = getApiErrorMessage(error, "Không thể tạo backup ở thời điểm hiện tại.");
  } finally {
    isBackupLoading.value = false;
  }
};

const updateCharts = () => {
  // Clear existing charts
  charts.forEach(c => c.destroy());
  charts = [];

  // Common font config
  const fontConfig = { family: "'Plus Jakarta Sans', sans-serif", weight: 600 };

  const chartRevenueSeries = [
    sellRevenue.value,
    rentalRevenue.value,
    penaltyRevenue.value,
    totalRevenue.value,
  ];

  // 1. Line Chart: Revenue overview
  if (revenueChartRef.value) {
    const ctx = revenueChartRef.value.getContext('2d');
    if (ctx) {
      const gradient = ctx.createLinearGradient(0, 0, 0, 400);
      gradient.addColorStop(0, 'rgba(37, 99, 235, 0.4)');
      gradient.addColorStop(1, 'rgba(37, 99, 235, 0)');

      const c = new Chart(ctx, {
        type: 'line',
        data: {
          labels: ['Bán', 'Thuê', 'Phạt', 'Tổng'],
          datasets: [{
            label: 'Doanh thu tổng hợp',
            data: chartRevenueSeries,
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
    const topBooks = hotBooks.value.slice(0, 5);
    const c = new Chart(topSellingChartRef.value, {
      type: 'bar',
      data: {
        labels: topBooks.map((item) => item.name),
        datasets: [{
          label: 'Bản bán',
          data: topBooks.map((item) => item.sellCount),
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
        labels: ['Doanh thu bán', 'Doanh thu thuê', 'Phạt'],
        datasets: [{
          data: [sellRevenue.value, rentalRevenue.value, penaltyRevenue.value],
          backgroundColor: ['#3b82f6', '#10b981', '#f59e0b'],
          borderWidth: 0
        }]
      },
      options: {
        responsive: true,
        cutout: '70%',
        plugins: { 
          legend: { position: 'bottom', labels: { font: fontConfig, usePointStyle: true, pointStyle: 'circle' } } 
        }
      }
    });
    charts.push(c);
  }

  // 4. Pie: Inventory
  if (inventoryChartRef.value) {
    const availableEstimate = Math.max(totalSales.value + totalRentals.value, 1);
    const lowStock = Math.max(lowStockItems.value, 0);
    const healthyStock = Math.max(availableEstimate - lowStock, 0);
    const c = new Chart(inventoryChartRef.value, {
      type: 'pie',
      data: {
        labels: ['Ổn định', 'Sắp hết hàng'],
        datasets: [{
          data: [healthyStock, lowStock],
          backgroundColor: ['#22c55e', '#ef4444'],
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

onMounted(async () => {
  await refreshData();
  await refreshBackupStatus();
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
.btn-refresh:disabled { cursor: not-allowed; opacity: 0.65; transform: none; }
.rotating { animation: spin 1s infinite linear; }

.report-error-banner {
  margin: -20px 0 24px;
  padding: 10px 14px;
  border-radius: 12px;
  border: 1px solid #fecaca;
  background: #fff1f2;
  color: #b91c1c;
  font-weight: 700;
}

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

.backup-panel {
  margin-bottom: 24px;
}

.backup-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 14px;
}

.backup-btn {
  border: 1px solid #cbd5e1;
  background: #ffffff;
  color: #1e293b;
  border-radius: 12px;
  padding: 9px 14px;
  font-weight: 700;
  cursor: pointer;
}

.backup-btn:hover {
  border-color: #94a3b8;
}

.backup-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.backup-btn.primary {
  background: #1d4ed8;
  color: #ffffff;
  border-color: #1d4ed8;
}

.backup-btn.ghost {
  background: #eff6ff;
  color: #1d4ed8;
  border-color: #bfdbfe;
}

.backup-banner {
  margin: 8px 0;
  padding: 9px 12px;
  border-radius: 10px;
  font-weight: 700;
}

.backup-banner.success {
  border: 1px solid #86efac;
  background: #f0fdf4;
  color: #166534;
}

.backup-banner.error {
  border: 1px solid #fecaca;
  background: #fff1f2;
  color: #b91c1c;
}

.backup-meta-grid {
  margin-top: 8px;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.backup-meta-grid div {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 10px 12px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.meta-label {
  font-size: 0.72rem;
  text-transform: uppercase;
  font-weight: 800;
  color: #64748b;
}

.backup-empty {
  margin: 8px 0 0;
  color: #64748b;
  font-weight: 600;
}

.table-lux table { width: 100%; border-collapse: collapse; }
.table-lux th { padding: 16px 32px; text-align: left; font-size: 0.75rem; color: #94a3b8; font-weight: 800; text-transform: uppercase; border-bottom: 1px solid #f1f5f9; }
.table-lux td { padding: 16px 32px; color: #1e293b; border-bottom: 1px solid #f1f5f9; font-size: 0.95rem; }
.table-lux tr:last-child td { border-bottom: none; }
.table-lux tr:hover td { background: #f8fafc; }

.table-empty {
  color: #94a3b8;
  font-weight: 600;
}

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
  .backup-meta-grid { grid-template-columns: 1fr; }
}
</style>