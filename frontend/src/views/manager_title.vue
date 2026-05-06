<template>
  <DefaultLayout>
    <div class="manager-container">
      <!-- Loading overlay -->
      <div v-if="isLoading" class="loading-overlay">
        <div class="spinner"></div>
        <span>Đang tải dữ liệu...</span>
      </div>

      <!-- Tabs -->
      <div class="view-tabs">
        <button
          type="button"
          :class="['tab-item', { active: activeTab === 'items' }]"
          @click="activeTab = 'items'"
        >
          <span class="material-icons">inventory_2</span>
          Danh mục kho
        </button>
        <button
          type="button"
          :class="['tab-item', { active: activeTab === 'history' }]"
          @click="activeTab = 'history'"
        >
          <span class="material-icons">history</span>
          Lịch sử cập nhật
        </button>
        <button
          type="button"
          :class="['tab-item', { active: activeTab === 'stats' }]"
          @click="activeTab = 'stats'"
        >
          <span class="material-icons">bar_chart</span>
          Biến động sách
        </button>
      </div>

      <!-- Nội dung Items -->
      <div v-if="activeTab === 'items'">
        <div class="header-card">
          <div class="header-left">
            <h1 class="page-title"> Quản lý đầu truyện</h1>
            <p class="page-subtitle">Danh mục sách, tập, bản sao và chuyển đổi kho</p>
          </div>
          <div class="header-actions">
            <div class="search-group">
              <input v-model="searchQuery" type="text" placeholder="🔍 Tìm kiếm truyện, ISBN..." class="search-input" />
            </div>
            <div class="filters">
              <select v-model="filterAuthor" class="filter-select"><option value="">Tác giả</option><option v-for="a in authors" :key="a" :value="a">{{ a }}</option></select>
              <select v-model="filterGenre" class="filter-select"><option value="">Thể loại</option><option v-for="g in genres" :key="g" :value="g">{{ g }}</option></select>
              <select v-model="filterPublisher" class="filter-select"><option value="">Nhà xuất bản</option><option v-for="p in publishers" :key="p" :value="p">{{ p }}</option></select>
            </div>
            <div class="action-buttons">
              <button class="btn-icon" @click="() => loadTitles()" title="Làm mới"><span class="material-icons">refresh</span></button>
              <button class="btn-primary" @click="openAddBook"><span class="material-icons">library_add</span> Đầu truyện mới</button>
              <button class="btn-secondary" @click="openScanModal()"><span class="material-icons">qr_code_scanner</span> Quét ISBN</button>
            </div>
          </div>
        </div>

        <!-- Books Grid -->
        <div class="books-grid">
          <div v-for="book in filteredBooks" :key="book.id" class="book-card" @click="openVolumeModal(book)">
            <div class="book-cover"><img :src="book.image" :alt="book.name" /></div>
            <div class="book-info">
              <div class="book-title">{{ book.name }}</div>
              <div class="book-meta"><span class="badge-author">✍️ {{ book.author || '?' }}</span><span class="badge-genre">{{ book.genre || 'Chưa phân loại' }}</span></div>
              <div class="book-publisher">{{ book.publisher }}</div>
              <div class="book-code">Mã: {{ book.code }}</div>
              <div class="book-desc">{{ book.description.slice(0, 80) }}...</div>
            </div>
            <div class="book-actions" @click.stop>
              <button class="icon-btn edit" @click="openEditBook(book)"><span class="material-icons">edit</span></button>
              <button class="icon-btn delete" @click="deleteBook(book.id)"><span class="material-icons">delete</span></button>
            </div>
          </div>
          <div v-if="filteredBooks.length === 0" class="empty-state"><span class="material-icons">book_stack</span><p>Không tìm thấy đầu truyện nào.</p></div>
        </div>

        <!-- MODAL: Volumes -->
        <BaseModal :is-open="isModalOpen" :title="selectedBook?.name" @close="isModalOpen = false" custom-class="modal-large">
          <div class="volume-table-wrapper">
            <table class="volume-table">
              <thead><tr><th>Tập</th><th>ISBN</th><th>Giá bán</th><th>Giá thuê</th><th>Tồn kho</th><th>Số lượng thuê</th></tr></thead>
              <tbody>
                <tr v-for="vol in selectedBook?.volumes" :key="vol.id" @click="openItemsModal(vol)">
                  <td>Tập {{ vol.volume }}</td>
                  <td>{{ vol.isbn || '—' }}</td>
                  <td>{{ formatVND(vol.price) }}</td>
                  <td>{{ formatVND(vol.rent_price) }}</td>
                  <td>{{ vol.so_luong }}</td>
                  <td>{{ vol.rental_item_count }}</td>
                  <td class="actions" @click.stop>
                    <button class="icon-small restock" @click="openRestockVolume(vol)" title="Bổ sung"><span class="material-icons">add_box</span></button>
                    <button class="icon-small edit" @click="openEditVolume(vol)"><span class="material-icons">edit</span></button>
                    <button class="icon-small delete" @click="deleteVolume(selectedBook, vol.id)"><span class="material-icons">delete</span></button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <template #footer><button class="btn-secondary" @click="isModalOpen = false">Đóng</button><button class="btn-primary" @click="openAddVolume">+ Thêm tập mới</button></template>
        </BaseModal>

        <!-- MODAL: Items -->
        <BaseModal :is-open="isItemsModalOpen" :title="`${selectedBook?.name} - Tập ${selectedVolume?.volume}`" @close="isItemsModalOpen = false" custom-class="modal-extra-large">
          <div class="items-table-wrapper">
            <table class="items-table">
              <thead><tr><th>Mã vạch</th><th>Loại</th><th>Trạng thái</th><th>Tình trạng</th><th>Ghi chú</th><th>Phiên bản</th><th></th></tr></thead>
              <tbody>
                <tr v-for="it in selectedVolume?.items" :key="it.id">
                  <td class="code-cell">{{ it.id }}</td>
                  <td><span :class="['type-badge', it.item_type === 'retail' ? 'retail' : 'rental']">{{ it.type_label }}</span></td>
                  <td>{{ getStatusText(it.status) }}</td>
                  <td>{{ it.condition }}</td>
                  <td>{{ it.note || '—' }}</td>
                  <td>{{ it.version }}</td>
                  <td class="actions">
                    <button class="icon-small edit" @click="openEditItem(it)"><span class="material-icons">edit</span></button>
                    <button class="icon-small delete" @click="deleteItem(selectedVolume, it.id)"><span class="material-icons">delete</span></button>
                    <button v-if="it.item_type === 'retail'" class="icon-small convert" @click="convertItemToRental(it)" title="Chuyển thuê"><span class="material-icons">sync_alt</span></button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <template #footer>
            <button class="btn-secondary" @click="isItemsModalOpen = false">Đóng</button>
            <button class="btn-primary" @click="openConvertRental" v-if="selectedVolume?.retail_stock > 0">Chuyển thuê (tồn: {{ selectedVolume?.retail_stock }})</button>
            <button class="btn-primary" @click="openAddItem">+ Thêm bản sao mới</button>
          </template>
        </BaseModal>

        <!-- MODAL: Book (Add/Edit) -->
        <BaseModal :is-open="isAddBookModalOpen || isEditBookModalOpen" :title="isEditBookModalOpen ? 'Sửa thông tin truyện' : 'Thêm truyện mới'" @close="isAddBookModalOpen = false; isEditBookModalOpen = false">
          <div class="form-grid">
            <div class="form-group"><label>Mã truyện</label><input v-model="formBook.code" type="text" placeholder="TR001" /></div>
            <div class="form-group"><label>Tên truyện *</label><input v-model="formBook.name" type="text" placeholder="Nhập tên truyện..." /></div>
            <div class="form-group"><label>Tác giả</label><input v-model="formBook.author" type="text" placeholder="Nhập tên tác giả..." /></div>
            <div class="form-group"><label>Thể loại</label><input v-model="formBook.genre" type="text" placeholder="Shonen, Drama..." /></div>
            <div class="form-group"><label>Nhà xuất bản</label><input v-model="formBook.publisher" type="text" placeholder="Nhập tên NXB..." /></div>
            <div class="form-group full-width"><label>Mô tả</label><textarea v-model="formBook.description" rows="3"></textarea></div>
          </div>
          <template #footer><button class="btn-secondary" @click="isAddBookModalOpen = false; isEditBookModalOpen = false">Hủy</button><button class="btn-primary" @click="saveBook">{{ isEditBookModalOpen ? 'Cập nhật' : 'Thêm mới' }}</button></template>
        </BaseModal>

        <!-- MODAL: Volume (Add/Edit) -->
        <BaseModal :is-open="isAddVolumeModalOpen || isEditVolumeModalOpen" :title="isEditVolumeModalOpen ? 'Sửa tập truyện' : 'Thêm tập mới'" @close="isAddVolumeModalOpen = false; isEditVolumeModalOpen = false">
          <div class="form-grid">
            <div class="form-group"><label>ISBN</label><input v-model="formVolume.isbn" type="text" placeholder="978-..." /></div>
            <div class="form-group"><label>Tập số</label><input v-model="formVolume.volume" type="text" placeholder="105" /></div>
            <div class="form-group"><label>Số lượng</label><input v-model="formVolume.so_luong" type="number" /></div>
            <div class="form-group"><label>Giá bán (VND)</label><input v-model="formVolume.price" type="text" placeholder="20.000đ" /></div>
            <div class="form-group"><label>Giá thuê (VND/ngày)</label><input v-model="formVolume.rent_price" type="text" placeholder="5.000đ" /></div>
          </div>
          <template #footer><button class="btn-secondary" @click="isAddVolumeModalOpen = false; isEditVolumeModalOpen = false">Hủy</button><button class="btn-primary" @click="saveVolume">{{ isEditVolumeModalOpen ? 'Cập nhật' : 'Thêm mới' }}</button></template>
        </BaseModal>

        <!-- MODAL: Item (Add/Edit) -->
        <BaseModal :is-open="isAddItemModalOpen || isEditItemModalOpen" :title="isEditItemModalOpen ? 'Sửa bản sao' : 'Thêm bản sao mới'" @close="isAddItemModalOpen = false; isEditItemModalOpen = false">
          <div class="form-grid">
            <div class="form-group" v-if="isEditItemModalOpen"><label>Mã vạch</label><input v-model="formItem.id" type="text" disabled /></div>
            <div class="form-group"><label>Loại hàng</label><select v-model="formItem.item_type"><option value="rental">Sách Thuê</option><option value="retail">Sách Bán</option></select></div>
            <div class="form-group"><label>Trạng thái</label><select v-model="formItem.status"><option>Có sẵn</option><option>Đã thuê</option><option>Bảo trì</option></select></div>
            <div class="form-group"><label>Tình trạng</label><input v-model="formItem.condition" type="text" placeholder="Mới, Cũ..." /></div>
            <div class="form-group full-width"><label>Ghi chú</label><input v-model="formItem.note" type="text" /></div>
          </div>
          <template #footer><button class="btn-secondary" @click="isAddItemModalOpen = false; isEditItemModalOpen = false">Hủy</button><button class="btn-primary" @click="saveItem">{{ isEditItemModalOpen ? 'Cập nhật' : 'Thêm mới' }}</button></template>
        </BaseModal>

        <!-- MODAL: Convert to Rental -->
        <BaseModal :is-open="isConvertRentalModalOpen" title="Chuyển sang truyện thuê" @close="isConvertRentalModalOpen = false">
          <div class="form-grid"><div class="form-group full-width"><label>Số lượng muốn chuyển từ kho bán</label><input v-model.number="formConvert.quantity" type="number" min="1" :max="selectedVolume?.retail_stock" /><small class="hint">Hành động này sẽ trừ hàng tồn bán và tạo mã vạch bản sao mới.</small></div></div>
          <template #footer><button class="btn-secondary" @click="isConvertRentalModalOpen = false">Hủy</button><button class="btn-primary" @click="saveConvertRental">Xác nhận chuyển</button></template>
        </BaseModal>

        <!-- MODAL: Scan ISBN -->
        <BaseModal :is-open="isScanModalOpen" title="Nhập nhanh qua ISBN" @close="isScanModalOpen = false">
          <div class="form-grid">
            <div class="form-group full-width"><label>Mã ISBN</label><div class="isbn-input-group"><input v-model="scanForm.isbn" type="text" placeholder="Quét hoặc nhập ISBN" @keydown.enter="lookupMetadataByIsbn" /><button class="btn-secondary" @click="lookupMetadataByIsbn" :disabled="isScanning">Tra cứu</button></div><small :class="['scan-status', { success: scanError.includes('Thành công'), error: scanError.includes('lỗi') || scanError.includes('Không') }]">{{ scanError }}</small></div>
            <div class="form-group"><label>Tên truyện</label><input v-model="scanForm.name" type="text" /></div>
            <div class="form-group"><label>Tập số</label><input v-model.number="scanForm.volume" type="number" min="1" /></div>
            <div class="form-group"><label>Tác giả</label><input v-model="scanForm.author" type="text" /></div>
            <div class="form-group"><label>Thể loại</label><input v-model="scanForm.genre" type="text" /></div>
            <div class="form-group"><label>Giá bán mới</label><input v-model.number="scanForm.price" type="number" step="1000" min="0" /></div>
            <div class="form-group"><label>Số lượng kho bán</label><input v-model.number="scanForm.retail_stock" type="number" min="1" /></div>
            <div class="form-group full-width" v-if="scanForm.cover_url"><img :src="scanForm.cover_url && !scanForm.cover_url.startsWith('http') ? `${API_BASE_URL}${scanForm.cover_url}` : scanForm.cover_url" class="cover-preview" /></div>
          </div>
          <template #footer><button class="btn-secondary" @click="isScanModalOpen = false">Hủy</button><button class="btn-primary" @click="saveScannedVolume" :disabled="isScanning || !scanForm.isbn || !scanForm.name">Lưu vào kho</button></template>
        </BaseModal>

        <!-- MODAL: Restock -->
        <BaseModal :is-open="isRestockModalOpen" title="Bổ sung tồn kho" @close="isRestockModalOpen = false">
          <div class="form-grid"><div class="form-group full-width"><label>Số lượng bổ sung</label><input v-model.number="restockQuantity" type="number" min="1" /><small class="hint">Số sách bán thêm vào kho.</small></div></div>
          <template #footer><button class="btn-secondary" @click="isRestockModalOpen = false">Hủy</button><button class="btn-primary" @click="saveRestock">Xác nhận</button></template>
        </BaseModal>
      </div>

      <!-- Nội dung History -->
      <div v-else-if="activeTab === 'history'">
        <div v-if="isLogsLoading" class="screen-loading-state">
          <span class="material-icons spin">autorenew</span>
          Đang nạp lịch sử nạp sách...
        </div>
        <div v-else class="logs-container">
          <div v-for="log in logs" :key="log.id" class="log-card">
            <div class="log-icon" :class="log.action_type.toLowerCase()">
              <span class="material-icons">{{ getLogIcon(log.action_type) }}</span>
            </div>
            <div class="log-content">
              <div class="log-header">
                <span class="log-user">{{ log.username || "Hệ thống" }}</span>
                <span class="log-time">{{ formatDateTime(log.created_at) }}</span>
              </div>
              <div class="log-message"> 
                <span class="log-action">{{ formatActionType(log.action_type) }}</span>
                <span class="log-target"> {{ log.title_name }} {{ log.sub_text }}</span>
                <p v-if="log.note" class="log-note">{{ log.note }}</p>
              </div>
              <div v-if="log.change_qty !== 0" class="log-delta">
                Biến động:
                <span :class="log.change_qty > 1 ? 'plus' : 'minus'">
                  {{ log.change_qty > 0 ? "+" : "" }}{{ log.change_qty }}
                </span>
                (Tồn kho: {{ log.old_qty }} → {{ log.new_qty }})
              </div>
            </div>
          </div>
          <div v-if="logs.length === 0" class="empty-state">Chưa có lịch sử cập nhật nào.</div>
        </div>
      </div>


      <!-- Nội dung Stats (Biến động sách) - PREMIUM DASHBOARD -->
      <div v-else-if="activeTab === 'stats'" class="stats-tab-content">
        <!-- KPI Metrics Cards với hiệu ứng hover -->
        <div class="stats-metrics-row">
          <div class="metric-card" data-type="stock">
            <div class="metric-icon stock">
              <span class="material-icons">inventory_2</span>
            </div>
            <div class="metric-info">
              <span class="metric-label">Tổng nhập kho</span>
              <span class="metric-value">+{{ statsTotals.stock_in.toLocaleString() }}</span>
            </div>
            <div class="metric-trend" v-if="statsData.length > 1">
              <span class="trend-up">
                <span class="material-icons">trending_up</span>
                {{ ((statsData[statsData.length-1].stock_in - statsData[0].stock_in) / (statsData[0].stock_in || 1) * 100).toFixed(0) }}%
              </span>
            </div>
          </div>
          <div class="metric-card" data-type="sale">
            <div class="metric-icon sale">
              <span class="material-icons">shopping_cart</span>
            </div>
            <div class="metric-info">
              <span class="metric-label">Tổng bán ra</span>
              <span class="metric-value">-{{ statsTotals.sale.toLocaleString() }}</span>
            </div>
          </div>
          <div class="metric-card" data-type="rental">
            <div class="metric-icon rental">
              <span class="material-icons">menu_book</span>
            </div>
            <div class="metric-info">
              <span class="metric-label">Tổng cho thuê</span>
              <span class="metric-value">-{{ statsTotals.rental.toLocaleString() }}</span>
            </div>
          </div>
          <div class="metric-card" data-type="circulation">
            <div class="metric-icon circulation">
              <span class="material-icons">compare_arrows</span>
            </div>
            <div class="metric-info">
              <span class="metric-label">Tốc độ lưu thông</span>
              <span class="metric-value">{{ circulationRate }}%</span>
            </div>
          </div>
        </div>

        <!-- Bộ lọc Glassmorphism -->
        <div class="stats-filters glass">
          <div class="filter-group">
            <label>Đầu truyện</label>
            <select v-model="statsFilter.titleId" class="glass-select">
              <option :value="''">-- Tất cả đầu truyện --</option>
              <option v-for="t in books" :key="t.id" :value="t.id">{{ t.name }}</option>
            </select>
          </div>
          <div class="filter-group">
            <label>Từ ngày</label>
            <input type="date" v-model="statsFilter.fromDate" class="glass-input"  />
          </div>
          <div class="filter-group">
            <label>Đến ngày</label>
            <input type="date" v-model="statsFilter.toDate" class="glass-input" />
          </div>
          <div class="filter-group">
            <label>Nhóm theo</label>
            <select v-model="statsFilter.groupBy" class="glass-select">
              <option value="day">Ngày</option>
              <option value="week">Tuần</option>
              <option value="month">Tháng</option>
              <option value="year">Năm</option>
            </select>
          </div>
          <div class="filter-actions">
            <button class="btn-refresh" @click="loadStats" :disabled="isStatsLoading" title="Tải lại">
              <span class="material-icons" :class="{ spin: isStatsLoading }">refresh</span>
            </button>
            <button class="btn-export" @click="exportStatsToCSV" title="Xuất CSV">
              <span class="material-icons">file_download</span>
            </button>
          </div>
        </div>

        <!-- Skeleton loading -->
        <div v-if="isStatsLoading" class="skeleton-stats">
          <div class="skeleton-chart"></div>
          <div class="skeleton-table">
            <div class="skeleton-row" v-for="n in 3" :key="n"></div>
          </div>
        </div>

        <!-- Empty state -->
        <div v-else-if="statsData.length === 0" class="empty-state-enhanced">
          <div class="empty-icon">
            <span class="material-icons">insights</span>
          </div>
          <h3>Chưa có dữ liệu</h3>
          <p>Không tìm thấy giao dịch nhập, bán hoặc thuê trong khoảng thời gian đã chọn.</p>
          <button class="btn-outline" @click="loadStats">Thử lại</button>
        </div>

        <!-- Biểu đồ và bảng khi có dữ liệu -->
        <template v-else>
          <div class="stats-visual-container premium">
            <div class="chart-header">
              <h3>Biến động theo thời gian</h3>
              <div class="chart-legend-custom">
                <span><span class="legend-color stock"></span> Nhập kho</span>
                <span><span class="legend-color sale"></span> Bán ra</span>
                <span><span class="legend-color rental"></span> Cho thuê</span>
              </div>
            </div>
            <div class="chart-wrapper">
              <canvas ref="chartCanvas"></canvas>
            </div>
          </div>

          <div class="stats-table-container premium">
            <div class="table-header">
              <h3>Chi tiết biến động</h3>
              <div class="table-controls">
                <input type="month" v-model="tableSearch" placeholder="🔍 Lọc theo thời gian..." class="table-search" />
                <div class="pagination" v-if="totalPages > 1">
                  <button @click="currentPage--" :disabled="currentPage === 1">‹</button>
                  <span>Trang {{ currentPage }} / {{ totalPages }}</span>
                  <button @click="currentPage++" :disabled="currentPage === totalPages">›</button>
                </div>
              </div>
            </div>
            <div class="table-responsive">
              <table class="data-table premium-table">
                <thead>
                  <tr>
                    <th @click="sortBy('period')">Thời gian <span class="sort-icon">{{ sortKey === 'period' ? (sortOrder === 'asc' ? '↑' : '↓') : '' }}</span></th>
                    <th class="text-right" @click="sortBy('stock_in')">Nhập kho (+) <span class="sort-icon">{{ sortKey === 'stock_in' ? (sortOrder === 'asc' ? '↑' : '↓') : '' }}</span></th>
                    <th class="text-right" @click="sortBy('sale')">Bán ra (-) <span class="sort-icon">{{ sortKey === 'sale' ? (sortOrder === 'asc' ? '↑' : '↓') : '' }}</span></th>
                    <th class="text-right" @click="sortBy('rental')">Cho thuê (-) <span class="sort-icon">{{ sortKey === 'rental' ? (sortOrder === 'asc' ? '↑' : '↓') : '' }}</span></th>
                    <th class="text-center" style="width: 80px;">Chi tiết</th>

                  </tr>
                </thead>
                <tbody>
                  <tr v-for="item in paginatedData" :key="item.period" class="hover-row">
                    <td class="period-cell">{{ item.period }}</td>
                    <td class="text-right value-positive">+{{ item.stock_in.toLocaleString() }}</td>
                    <td class="text-right value-negative">-{{ item.sale.toLocaleString() }}</td>
                    <td class="text-right value-warning">-{{ item.rental.toLocaleString() }}</td>
                    <td class="text-center">
                      <button class="icon-detail premium" @click="loadStatsDetail(item.period)" title="Xem chi tiết theo tập">
                        <span class="material-icons">visibility</span>
                      </button>
                    </td>
                  </tr>
                  <tr v-if="paginatedData.length === 0">
                    <td colspan="5" class="text-center">Không có dữ liệu phù hợp</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </template>
      </div>

      <!-- MODAL: Chi tiết biến động -->
      <BaseModal 
        :is-open="isDetailModalOpen" 
        :title="'📊 Chi tiết biến động: ' + drillDownPeriod" 
        @close="isDetailModalOpen = false"
        custom-class="modal-detail"
      >
        <div v-if="isDetailLoading" class="detail-loading">
          <div class="spinner-mini"></div>
          <span>Đang tải dữ liệu chi tiết...</span>
        </div>
        <div v-else>
          <!-- Tóm tắt tổng quan -->
          <div class="detail-summary" v-if="selectedPeriodDetails.length">
            <div class="summary-card">
              <div class="summary-icon stock">
                <span class="material-icons">inventory_2</span>
              </div>
              <div class="summary-info">
                <span class="summary-label">Tổng nhập</span>
                <strong class="summary-value">+{{ selectedPeriodDetails.reduce((a,b)=>a+b.stock_in,0) }}</strong>
              </div>
            </div>
            <div class="summary-card">
              <div class="summary-icon sale">
                <span class="material-icons">shopping_cart</span>
              </div>
              <div class="summary-info">
                <span class="summary-label">Tổng bán</span>
                <strong class="summary-value">-{{ selectedPeriodDetails.reduce((a,b)=>a+b.sale,0) }}</strong>
              </div>
            </div>
            <div class="summary-card">
              <div class="summary-icon rental">
                <span class="material-icons">menu_book</span>
              </div>
              <div class="summary-info">
                <span class="summary-label">Tổng thuê</span>
                <strong class="summary-value">-{{ selectedPeriodDetails.reduce((a,b)=>a+b.rental,0) }}</strong>
              </div>
            </div>
          </div>

          <!-- Bảng chi tiết theo tập -->
          <div class="detail-table-wrapper">
            <table class="detail-table">
              <thead>
                <tr>
                  <th>Tập truyện</th>
                  <th class="text-right">Nhập</th>
                  <th class="text-right">Bán</th>
                  <th class="text-right">Thuê</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="d in selectedPeriodDetails" :key="d.volume_id" class="detail-row">
                  <td>
                    <div class="volume-info">
                      <div class="volume-name">{{ d.volume_name }}</div>
                      <div class="volume-isbn">{{ d.isbn }}</div>
                    </div>
                  </td>
                  <td class="text-right value-positive">+{{ d.stock_in.toLocaleString() }}</td>
                  <td class="text-right value-negative">-{{ d.sale.toLocaleString() }}</td>
                  <td class="text-right value-warning">-{{ d.rental.toLocaleString() }}</td>
                </tr>
                <tr v-if="selectedPeriodDetails.length === 0">
                  <td colspan="4" class="text-center">Không có chi tiết cho khoảng thời gian này.</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
        <template #footer>
          <button class="btn-secondary" @click="isDetailModalOpen = false">Đóng</button>
        </template>
      </BaseModal>
    </div>
  </DefaultLayout>
</template>

<script setup lang="ts">
// ⚠️ PHẦN SCRIPT GIỮ NGUYÊN TUYỆT ĐỐI – KHÔNG THAY ĐỔI BẤT KỲ LOGIC NÀO
import { ref, computed, inject, onMounted, onBeforeUnmount, watch, nextTick } from 'vue';
import DefaultLayout from '../components/layout/defaultLayout.vue'
import BaseModal from '../components/layout/BaseModal.vue'
import { 
  API_BASE_URL,
  fetchTitlesWithVolumes, 
  fetchInventoryLogs,
  createTitle as apiCreateTitle,
  updateTitle as apiUpdateTitle,
  deleteTitle as apiDeleteTitle,
  createVolume as apiCreateVolume,
  updateVolume as apiUpdateVolume,
  deleteVolume as apiDeleteVolume,
  createItem as apiCreateItem,
  updateItem as apiUpdateItem,
  deleteItem as apiDeleteItem,
  convertToRental,
  buildRequestId,
  autofillTitleMetadata,
  importCoverImage,
  request,
  type InventoryLogItem,
} from '../services/storyhubApi';
import { useAuthStore } from '../stores/auth';
import { useScannerStore } from '../stores/scanner';
import Chart from 'chart.js/auto';

const addNotification = inject('addNotification') as any;
const showConfirm = inject('showConfirm') as any;

const authStore = useAuthStore();
const token = computed(() => authStore.token ?? 'manager-demo');

//------- history ---------
const logs = ref<InventoryLogItem[]>([]);
const isLogsLoading = ref(false);

// Helper functions for history
const formatDateTime = (dateStr: string) => {
  if (!dateStr) return '';
  const d = new Date(dateStr);
  return d.toLocaleString('vi-VN');
};
const getLogIcon = (actionType: string) => {
  switch (actionType) {
    case 'STOCK_IN': return 'add_circle';
    case 'CONVERT': return 'sync_alt';
    case 'PRICE_CHANGE': return 'sell';
    case 'ADJUST': return 'tune';
    default: return 'history';
  }
};
const formatActionType = (actionType: string) => {
  switch (actionType) {
    case 'STOCK_IN': return 'Đã nhập thêm';
    case 'CONVERT': return 'Đã chuyển loại';
    case 'PRICE_CHANGE': return 'Đã đổi giá';
    case 'ADJUST': return 'Đã điều chỉnh';
    default: return actionType;
  }
};
const loadLogs = async () => {
  isLogsLoading.value = true;
  try {
    logs.value = await fetchInventoryLogs();
  } catch (error: any) {
    addNotification?.('error', error.message || 'Không thể nạp lịch sử kho.');
  } finally {
    isLogsLoading.value = false;
  }
};

// ─── Modal state ─────────────────────────────────────────────────────────────
const activeTab = ref<"items" | "history" | "stats">("items");


watch(activeTab, (newTab) => {
  if (newTab === 'stats') {
    loadStats();
  } else if (newTab === 'history') {
    loadLogs();
  } else if (newTab === 'items') {
    loadTitles();
  }
});

const isModalOpen = ref(false);
const isItemsModalOpen = ref(false);
const isAddBookModalOpen = ref(false);
const isEditBookModalOpen = ref(false);
const isAddVolumeModalOpen = ref(false);
const isEditVolumeModalOpen = ref(false);
const isAddItemModalOpen = ref(false);
const isEditItemModalOpen = ref(false);
const isConvertRentalModalOpen = ref(false);
const isRestockModalOpen = ref(false);
const restockVolume = ref<any>(null);
const restockQuantity = ref(1);

const selectedBook = ref<any>(null);
const selectedVolume = ref<any>(null);
const scannerStore = useScannerStore();
let stopScannerWatch: (() => void) | null = null;

// ─── Form state ───────────────────────────────────────────────────────────────
const formBook = ref({ id: 0, code: '', name: '', description: '', author: '', genre: '', publisher: '', image: '', volumes: [] as any[] });
const formVolume = ref({ id: 0, volume: 0, isbn: '', so_luong: 0, price: 0 as string | number, rent_price: 0 as string | number });
const formItem = ref({ id: '', status: 'Có sẵn', condition: 'Mới', note: '', item_type: 'rental' });
const formConvert = ref({ quantity: 1 });

// ─── Scan state ───────────────────────────────────────────────────────────────
const isScanModalOpen = ref(false);
const isScanning = ref(false);
const scanError = ref('');
const scanForm = ref({ isbn: '', name: '', author: '', description: '', cover_url: '', genre: '', publisher: '', volume: 1, price: 0, retail_stock: 1 });

const openScanModal = (initialIsbn = '') => {
  scanForm.value = { 
    isbn: initialIsbn, 
    name: '', author: '', description: '', cover_url: '', 
    genre: '', publisher: '', volume: 1, price: 0, retail_stock: 1 
  };
  scanError.value = '';
  isScanModalOpen.value = true;
  if (initialIsbn) {
    lookupMetadataByIsbn();
  }
};

const extractTitleAndVolume = (rawTitle: string) => {
  const cleaned = rawTitle.trim();
  const volumeMatch = cleaned.match(/(?:\b(?:t\.?|tap|tập|vol(?:ume)?\.?)[\s#:.-]*)(\d{1,4})/i);
  if (!volumeMatch) return { title: cleaned, volume: 1 };
  const volume = Number(volumeMatch[1]) || 1;
  const title = cleaned.replace(volumeMatch[0], "").replace(/[-:()\s]+$/g, "").trim();
  return { title: title || cleaned, volume };
};

const lookupMetadataByIsbn = async () => {
  const isbn = scanForm.value.isbn.replace(/[^0-9Xx]/g, "").toUpperCase();
  if (isbn.length < 10) {
    scanError.value = "ISBN quá ngắn để tra metadata.";
    return;
  }
  isScanning.value = true;
  scanError.value = "Đang tra cứu từ backend...";
  try {
    const response = await autofillTitleMetadata({
      isbn,
      request_id: buildRequestId("scan-metadata"),
    });
    const parsed = extractTitleAndVolume(response.metadata.name);
    scanForm.value.name = parsed.title;
    scanForm.value.volume = parsed.volume;
    scanForm.value.author = response.metadata.author;
    scanForm.value.genre = response.metadata.genre;
    scanForm.value.description = response.metadata.description;
    scanForm.value.publisher = response.metadata.publisher;

    if (response.metadata.cover_url && /^https?:\/\//i.test(response.metadata.cover_url)) {
      scanError.value = "Đạng tải ảnh bìa...";
      try {
        const coverPayload = await importCoverImage({
          isbn,
          image_url: response.metadata.cover_url,
          request_id: buildRequestId("import-cover")
        });
        scanForm.value.cover_url = coverPayload.cover_url;
      } catch (e: any) {}
    }
    scanError.value = "Thành công!";
  } catch (error: unknown) {
    scanError.value = "Không tìm thấy thông tin tự động, vui lòng nhập tay.";
  } finally {
    isScanning.value = false;
  }
};

// ─── Stats logic ─────────────────────────────────────────────────────────────
const statsData = ref<Array<{ period: string; stock_in: number; sale: number; rental: number }>>([]);
const statsTotals = ref({ stock_in: 0, sale: 0, rental: 0 });
const isStatsLoading = ref(false);
const statsFilter = ref({
  titleId: '' as string | number,
  fromDate: new Date(new Date().setDate(new Date().getDate() - 30)).toISOString().split('T')[0],
  toDate: new Date().toISOString().split('T')[0],
  groupBy: 'month' as 'day' | 'week' | 'month' | 'year'
});

const circulationRate = computed(() => {
  if (statsTotals.value.stock_in === 0) return (statsTotals.value.sale + statsTotals.value.rental) > 0 ? '100+' : '0';
  return ((statsTotals.value.sale + statsTotals.value.rental) / statsTotals.value.stock_in * 100).toFixed(1);
});

const isDetailModalOpen = ref(false);
const selectedPeriodDetails = ref<any[]>([]);
const isDetailLoading = ref(false);
const drillDownPeriod = ref('');

let chartInstance: Chart | null = null;
const chartCanvas = ref<HTMLCanvasElement | null>(null);

const loadStats = async () => {
  isStatsLoading.value = true;
  try {
    const response = await request<any>('/api/v1/reports/inventory-fluctuations', {
      method: 'POST',
      body: JSON.stringify({
        from_date: statsFilter.value.fromDate,
        to_date: statsFilter.value.toDate,
        group_by: statsFilter.value.groupBy,
        title_id: statsFilter.value.titleId ? Number(statsFilter.value.titleId) : null,
        request_id: buildRequestId('stats')
      }),
      token: token.value
    });
    
    // Updated backend returns { data: [...], totals: {...} }
    statsData.value = response?.data || [];
    statsTotals.value = response?.totals || { stock_in: 0, sale: 0, rental: 0 };
    
  } catch (e: any) {
    addNotification?.('error', e.message || 'Lỗi tải thống kê');
    statsData.value = [];
  } finally {
    isStatsLoading.value = false;
    // Đảm bảo DOM đã render xog (v-if) trước khi vẽ biểu đồ
    nextTick(() => {
      renderChart();
    });
  }
};

const loadStatsDetail = async (period: string) => {
  drillDownPeriod.value = period;
  isDetailModalOpen.value = true;
  isDetailLoading.value = true;
  selectedPeriodDetails.value = [];
  try {
    const response = await request<any>('/api/v1/reports/inventory-fluctuations/detail', {
      method: 'POST',
      body: JSON.stringify({
        from_date: statsFilter.value.fromDate,
        to_date: statsFilter.value.toDate,
        group_by: statsFilter.value.groupBy,
        title_id: statsFilter.value.titleId ? Number(statsFilter.value.titleId) : null,
        period: period,
        request_id: buildRequestId('stats-detail')
      }),
      token: token.value
    });
    selectedPeriodDetails.value = response?.data || [];
  } catch (e: any) {
    addNotification?.('error', e.message || 'Lỗi tải chi tiết biến động');
  } finally {
    isDetailLoading.value = false;
  }
};

const exportStatsToCSV = () => {
  if (statsData.value.length === 0) return;
  const headers = ['Thời gian', 'Nhập kho', 'Bán ra', 'Cho thuê'];
  const rows = statsData.value.map(d => [d.period, d.stock_in, d.sale, d.rental]);
  const csvContent = "data:text/csv;charset=utf-8," 
    + [headers, ...rows].map(e => e.join(",")).join("\n");
  const encodedUri = encodeURI(csvContent);
  const link = document.createElement("a");
  link.setAttribute("href", encodedUri);
  link.setAttribute("download", `storyhub_bien_dong_${statsFilter.value.fromDate}_${statsFilter.value.toDate}.csv`);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
};

const renderChart = () => {
  if (!chartCanvas.value) return;
  if (chartInstance) chartInstance.destroy();

  const labels = statsData.value.map(d => d.period);
  const stockIn = statsData.value.map(d => d.stock_in);
  const sale = statsData.value.map(d => d.sale);
  const rental = statsData.value.map(d => d.rental);

  const ctx = chartCanvas.value.getContext('2d');
  if (!ctx) return;

  const gradStock = ctx.createLinearGradient(0, 0, 0, 400);
  gradStock.addColorStop(0, 'rgba(34, 197, 94, 0.4)');
  gradStock.addColorStop(1, 'rgba(34, 197, 94, 0)');

  const gradSale = ctx.createLinearGradient(0, 0, 0, 400);
  gradSale.addColorStop(0, 'rgba(239, 68, 68, 0.4)');
  gradSale.addColorStop(1, 'rgba(239, 68, 68, 0)');

  const gradRental = ctx.createLinearGradient(0, 0, 0, 400);
  gradRental.addColorStop(0, 'rgba(245, 158, 11, 0.4)');
  gradRental.addColorStop(1, 'rgba(245, 158, 11, 0)');

  chartInstance = new Chart(ctx, {
    type: 'bar',
    data: {
      labels,
      datasets: [
        {
          label: 'Nhập kho',
          data: stockIn,
          backgroundColor: gradStock,
          borderColor: '#22c55e',
          borderWidth: 2,
          borderRadius: 6,
        },
        {
          label: 'Bán ra',
          data: sale,
          backgroundColor: gradSale,
          borderColor: '#ef4444',
          borderWidth: 2,
          borderRadius: 6,
        },
        {
          label: 'Cho thuê',
          data: rental,
          backgroundColor: gradRental,
          borderColor: '#f59e0b',
          borderWidth: 2,
          borderRadius: 6,
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { intersect: false, mode: 'index' },
      plugins: {
        legend: { position: 'top', labels: { usePointStyle: true, font: { family: 'Inter', weight: 'bold' } } },
        tooltip: {
          backgroundColor: 'rgba(255, 255, 255, 0.95)',
          titleColor: '#1e293b',
          bodyColor: '#475569',
          borderColor: '#e2e8f0',
          borderWidth: 1,
          padding: 10,
          boxPadding: 4,
          usePointStyle: true
        }
      },
      scales: {
        x: { grid: { display: false } },
        y: { 
          beginAtZero: true, 
          grid: { color: 'rgba(0,0,0,0.03)' },
          ticks: { callback: (val: any) => Number(val) > 0 ? '+' + val : val }
        }
      },
      animation: {
        duration: 2000,
        easing: 'easeOutQuart'
      },
      // Thêm hiệu ứng phát sáng cho bars
      elements: {
        bar: {
          backgroundColor: 'rgba(255,255,255,0.1)',
          hoverBackgroundColor: 'rgba(255,255,255,0.2)'
        }
      }
    }
  });
};

const saveScannedVolume = async () => {
   isScanning.value = true;
   try {
     await apiCreateVolume(
       {
         title_name: scanForm.value.name || "Unknown Title",
         author: scanForm.value.author || "Unknown",
         volume_number: scanForm.value.volume || 1,
         isbn: scanForm.value.isbn,
         retail_stock: scanForm.value.retail_stock || 1,
         p_sell_new: scanForm.value.price || 0,
         description: scanForm.value.description || '',
         cover_url: scanForm.value.cover_url || null,
         categories: scanForm.value.genre ? scanForm.value.genre.split(',').map(s => s.trim()) : [],
         published_date: null,
         request_id: buildRequestId('add-volume-scan'),
       },
       token.value,
     );
     addNotification('success', 'Đã lưu truyện quét mã thành công!');
     isScanModalOpen.value = false;
     await loadTitles();
   } catch(e: any) {
     scanError.value = e?.message || 'Lỗi lưu thông tin';
   } finally {
     isScanning.value = false;
   }
};

// Thêm vào phần stats logic
// Sorting, pagination, search for table
const tableSearch = ref('');
const sortKey = ref('period');
const sortOrder = ref<'asc'|'desc'>('asc');
const currentPage = ref(1);
const itemsPerPage = 10;

const filteredSortedData = computed(() => {
  let data = [...statsData.value];
  if (tableSearch.value) {
    const lowerSearch = tableSearch.value.toLowerCase();
    data = data.filter(item => item.period.toLowerCase().includes(lowerSearch));
  }
  data.sort((a, b) => {
    let aVal: any = (a as any)[sortKey.value];
    let bVal: any = (b as any)[sortKey.value];
    if (sortKey.value === 'period') {
      return sortOrder.value === 'asc' ? String(aVal).localeCompare(String(bVal)) : String(bVal).localeCompare(String(aVal));
    }
    return sortOrder.value === 'asc' ? Number(aVal) - Number(bVal) : Number(bVal) - Number(aVal);
  });
  return data;
});

const totalPages = computed(() => Math.ceil(filteredSortedData.value.length / itemsPerPage));
const paginatedData = computed(() => {
  const start = (currentPage.value - 1) * itemsPerPage;
  return filteredSortedData.value.slice(start, start + itemsPerPage);
});

function sortBy(key: string) {
  if (sortKey.value === key) {
    sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc';
  } else {
    sortKey.value = key;
    sortOrder.value = 'asc';
  }
  currentPage.value = 1;
}

// Reset page khi bộ lọc thay đổi
watch([statsFilter, tableSearch], () => {
  currentPage.value = 1;
});

// ─── API data & loading ───────────────────────────────────────────────────────
const isLoading = ref(false);
const apiError = ref('');
const books = ref<any[]>([]);

async function loadTitles(q?: string) {
  isLoading.value = true;
  apiError.value = '';
  try {
    const data = await fetchTitlesWithVolumes(q, token.value);
    books.value = data.map(title => ({
      id: title.id,
      code: `TR${String(title.id).padStart(3, '0')}`,
      name: title.name,
      description: title.description ?? '',
      author: title.author ?? '',
      genre: title.genre ?? '',
      publisher: title.publisher ?? '',
      image: (() => {
        if (!title.cover_url) return 'https://via.placeholder.com/50x70';
        if (title.cover_url.startsWith('http')) return title.cover_url;
        return `${API_BASE_URL}${title.cover_url}`;
      })(),
      _raw: title,
      volumes: title.volumes.map(vol => ({
        id: vol.id,
        code: vol.isbn ?? `VOL-${vol.id}`,
        name: title.name,
        volume: String(vol.volume_number),
        isbn: vol.isbn ?? '',
        so_luong: vol.retail_stock,
        rental_item_count: vol.rental_item_count,
        retail_stock: vol.retail_stock,
        price: vol.p_sell_new,
        rent_price: vol.price_rental,
        deposit: vol.price_deposit,
        items: vol.items.filter(it => it.status === 'available' || it.status === 'maintenance').map(it => ({
          id: it.id,
          volume: String(vol.volume_number),
          status: it.status,
          item_type: it.item_type || 'rental',
          type_label: it.item_type === 'retail' ? 'Sách Bán' : 'Sách Thuê',
          condition: it.condition_level >= 80 ? 'Tốt' : it.condition_level >= 50 ? 'Trung bình' : 'Kém',
          note: it.notes ?? '',
          has_barcode: it.has_barcode,
          can_rent: it.has_barcode, 
          version: `Bản in lần ${it.version_no}`,
          start_date: it.reserved_at ? new Date(it.reserved_at).toLocaleDateString() : '—',
          end_date: it.reservation_expire_at ? new Date(it.reservation_expire_at).toLocaleDateString() : '—',
        })),
      })),
    }));
  } catch (e: any) {
    apiError.value = e?.message ?? 'Không tải được danh sách truyện.';
    addNotification?.('error', apiError.value);
  } finally {
    isLoading.value = false;
  }
}

onMounted(() => {
  loadTitles();
  stopScannerWatch = watch(
    () => scannerStore.scanEventCounter,
    () => {
      const scanned = scannerStore.lastScannedCode;
      if (!scanned) return;
      if (scanned.toUpperCase().startsWith('RNT-')) {
        scannerStore.lastScannedCode = '';
        return;
      }
      openScanModal(scanned);
      scannerStore.lastScannedCode = '';
    },
    { immediate: true }
  );
  // Stats Filter Reactive Loading
  watch(statsFilter, () => {
    if (activeTab.value === 'stats') {
      loadStats();
    }
  }, { deep: true });
});
onBeforeUnmount(() => {
  if (stopScannerWatch) stopScannerWatch();
});

// ─── Search & Filter ──────────────────────────────────────────────────────────
const searchQuery = ref('');
const filterAuthor = ref('');
const filterPublisher = ref('');
const filterGenre = ref('');

const authors = computed(() => [...new Set(books.value.map(b => b.author).filter(Boolean))]);
const publishers = computed(() => [...new Set(books.value.map(b => b.publisher).filter(Boolean))]);
const genres = computed(() => [...new Set(books.value.map(b => b.genre).filter(Boolean))]);

const filteredBooks = computed(() => {
  return books.value.filter(book => {
    const matchesSearch = (book.name || '').toLowerCase().includes((searchQuery.value || '').toLowerCase()) || 
                          (book.code || '').toLowerCase().includes((searchQuery.value || '').toLowerCase());
    const matchesAuthor = !filterAuthor.value || book.author === filterAuthor.value;
    const matchesPublisher = !filterPublisher.value || book.publisher === filterPublisher.value;
    const matchesGenre = !filterGenre.value || book.genre === filterGenre.value;
    return matchesSearch && matchesAuthor && matchesPublisher && matchesGenre;
  });
});

const openRestockVolume = (vol: any) => {
  restockVolume.value = vol;
  restockQuantity.value = 1;
  isRestockModalOpen.value = true;
};

const openVolumeModal = (book: any) => {
  selectedBook.value = book;
  isModalOpen.value = true;
};
const openItemsModal = (vol: any) => {
  selectedVolume.value = vol; 
  isItemsModalOpen.value = true;
};

// ─── CRUD Books ──────────────────
const openAddBook = () => {
  formBook.value = { id: 0, code: '', name: '', description: '', author: '', genre: '', publisher: '', image: '', volumes: [] };
  isAddBookModalOpen.value = true;
};
const openEditBook = (book: any) => {
  formBook.value = { ...book };
  isEditBookModalOpen.value = true;
};
const saveBook = async () => {
  try {
    const payload = {
      name: formBook.value.name,
      description: formBook.value.description,
      author: formBook.value.author,
      genre: formBook.value.genre,
      publisher: formBook.value.publisher,
      request_id: buildRequestId('book'),
    };
    if (formBook.value.id) {
       await apiUpdateTitle(formBook.value.id, payload, token.value);
       addNotification('success', 'Đã cập nhật Truyện!');
    } else {
       await apiCreateTitle(payload, token.value);
       addNotification('success', 'Đã tạo Truyện mới!');
    }
    isAddBookModalOpen.value = false;
    isEditBookModalOpen.value = false;
    await loadTitles();
  } catch (err: any) {
    addNotification('error', err.message || 'Lỗi lưu sách');
  }
};
const deleteBook = async (id: number) => {
  if (await showConfirm('Bạn có chắc muốn xóa đầu truyện này? Tất cả các tập và bản sao bên trong sẽ bị xóa theo.')) {
    try {
      await apiDeleteTitle(id, token.value);
      addNotification('success', 'Đã xóa đầu truyện thành công!');
      await loadTitles();
    } catch(err: any) {
      addNotification('error', 'Lỗi: ' + err.message);
    }
  }
};

const saveRestock = async () => {
  if (!restockVolume.value || !selectedBook.value) return;
  try {
    await apiCreateVolume(
      {
        title_name: selectedBook.value.name,
        author: selectedBook.value.author ?? '',
        volume_number: restockVolume.value.volume_number,
        isbn: restockVolume.value.isbn,
        retail_stock: restockQuantity.value,
        p_sell_new: restockVolume.value.price,
        description: selectedBook.value.description || '',
        cover_url: null,
        categories: selectedBook.value.genre ? [selectedBook.value.genre] : [],
        page_count: null,
        published_date: null,
        request_id: buildRequestId('restock-volume'),
      },
      token.value,
    );
    addNotification('success', `Đã bổ sung ${restockQuantity.value} bản cho tập ${restockVolume.value.volume_number}`);
    isRestockModalOpen.value = false;
    await loadTitles();
    const updatedBook = books.value.find(b => b.id === selectedBook.value?.id);
    if (updatedBook) selectedBook.value = updatedBook;
  } catch(e: any) {
    addNotification('error', e?.message ?? 'Bổ sung thất bại');
  }
};

// ─── CRUD Volumes ──────────────────────────────────────────────────────────────
const openAddVolume = () => {
  formVolume.value = { id: 0, volume: 0, isbn: '', so_luong: 0, price: '', rent_price: '' };
  isAddVolumeModalOpen.value = true;
};
const openEditVolume = (vol: any) => {
  formVolume.value = {
    id: vol.id,
    volume: Number(vol.volume),
    isbn: vol.isbn,
    so_luong: vol.retail_stock,
    price: vol.price,
    rent_price: vol.rent_price,
  };
  isEditVolumeModalOpen.value = true;
};
const isSavingVolume = ref(false);
const saveVolume = async () => {
  if (!selectedBook.value) return;
  if (!formVolume.value.isbn || !formVolume.value.volume) {
    addNotification('error', 'Vui lòng nhập ISBN và số tập.');
    return;
  }
  isSavingVolume.value = true;
  try {
    if (formVolume.value.id) {
        await apiUpdateVolume(formVolume.value.id, {
            volume_number: Number(String(formVolume.value.volume).replace(/\D/g, '')),
            isbn: formVolume.value.isbn,
            retail_stock: Number(formVolume.value.so_luong),
            p_sell_new: Number(String(formVolume.value.price).replace(/\D/g, '')),
            request_id: buildRequestId('update-vol')
        }, token.value);
        addNotification('success', 'Đã cập nhật tập truyện!');
    } else {
        await apiCreateVolume(
          {
            title_name: selectedBook.value.name,
            author: selectedBook.value.author ?? '',
            volume_number: Number(String(formVolume.value.volume).replace(/\D/g, '')),
            isbn: formVolume.value.isbn,
            retail_stock: Number(formVolume.value.so_luong),
            p_sell_new: Number(String(formVolume.value.price).replace(/\D/g, '')),
            description: selectedBook.value.description || '',
            cover_url: null,
            categories: selectedBook.value.genre ? [selectedBook.value.genre] : [],
            page_count: null,
            published_date: null,
            request_id: buildRequestId('add-volume'),
          },
          token.value,
        );
        addNotification('success', 'Đã tạo tập truyện thành công!');
    }
    isAddVolumeModalOpen.value = false;
    isEditVolumeModalOpen.value = false;
    await loadTitles();
    const updatedBook = books.value.find(b => b.id === selectedBook.value?.id);
    if (updatedBook) selectedBook.value = updatedBook;
  } catch (e: any) {
    addNotification('error', e?.message ?? 'Lưu tập thất bại.');
  } finally {
    isSavingVolume.value = false;
  }
};
const deleteVolume = async (book: any, volId: number) => {
  if (await showConfirm('Xóa tập này khỏi hệ thống?')) {
    try {
      await apiDeleteVolume(volId);
      addNotification('success', 'Thành công!');
      await loadTitles();
      const updatedBook = books.value.find(b => b.id === book.id);
      if (updatedBook) selectedBook.value = updatedBook;
    } catch(err: any) {
      addNotification('error', 'Lỗi: ' + err.message);
    }
  }
};

// ─── CRUD Items ────────────────────────────────────────────────────────────────
const openAddItem = () => {
  if(!selectedVolume.value) return;
  const defaultType = selectedVolume.value.retail_stock > 0 ? 'retail' : 'rental';
  formItem.value = { id: '', status: 'Có sẵn', condition: 'Mới', note: '', item_type: defaultType };
  isAddItemModalOpen.value = true;
};
const openEditItem = (item: any) => {
  if(!selectedVolume.value) return;
  formItem.value = { id: item.id, status: item.status, condition: item.condition, note: item.note, item_type: item.item_type };
  isEditItemModalOpen.value = true;
};

const convertItemToRental = async (item: any) => {
  if (!confirm(`Bạn chắc chắn muốn chuyển bản sao ${item.id} thành sách thuê?`)) return;
  try {
    await apiUpdateItem(item.id, {
      status: 'available',
      condition_level: 100,
      item_type: 'rental',
      notes: item.note,
    }, token.value);
    addNotification('success', `Đã chuyển ${item.id} sang sách thuê.`);
    await loadTitles();
    if(selectedBook.value) {
        selectedBook.value = books.value.find(b => b.id === selectedBook.value.id) || null;
        if(selectedVolume.value) {
            selectedVolume.value = selectedBook.value?.volumes.find((v:any) => v.id === selectedVolume.value.id) || null;
        }
    }
  } catch(e:any) {
    addNotification('error', e?.message || 'Lỗi chuyển đổi.');
  }
};

const saveItem = async () => {
  try {
    const payload = {
      status: reverseStatusMap[formItem.value.status] || formItem.value.status,
      item_type: formItem.value.item_type,
      condition_level: formItem.value.condition === 'Mới' ? 100 : formItem.value.condition === 'Tốt' ? 80 : formItem.value.condition === 'Trung bình' ? 50 : 20,
      notes: formItem.value.note,
    };
    if (isEditItemModalOpen.value) {
       await apiUpdateItem(formItem.value.id, payload, token.value);
       addNotification('success', 'Cập nhật bản sao thành công!');
    } else {
       await apiCreateItem({ ...payload, volume_id: selectedVolume.value.id, id: null, version_no: 1 }, token.value);
       addNotification('success', 'Tạo bản sao thành công!');
    }
    isAddItemModalOpen.value = false;
    isEditItemModalOpen.value = false;
    await loadTitles();
    const updatedBook = books.value.find(b => b.id === selectedBook.value?.id);
    if (updatedBook) selectedVolume.value = updatedBook.volumes.find((v: any) => v.id === selectedVolume.value?.id);
  } catch (err: any) {
    addNotification('error', err.message || 'Lỗi lưu bản sao');
  }
};
const deleteItem = async (volume: any, itemId: string) => {
  if (await showConfirm('Xóa bản sao này khỏi hệ thống?')) {
     try {
       await apiDeleteItem(itemId, token.value);
       addNotification('success', 'Thành công!');
       await loadTitles();
       const updatedBook = books.value.find(b => b.id === selectedBook.value?.id);
       if (updatedBook) selectedVolume.value = updatedBook.volumes.find((v: any) => v.id === volume.id);
     } catch(e: any) {
       addNotification('error', 'Lỗi: ' + e.message);
     }
  }
};

const openConvertRental = () => {
  formConvert.value.quantity = 1;
  isConvertRentalModalOpen.value = true;
};

const saveConvertRental = async () => {
  if (!selectedVolume.value) return;
  try {
    await convertToRental({
      volume_id: selectedVolume.value.id,
      quantity: formConvert.value.quantity,
      request_id: buildRequestId('convert'),
    }, token.value);
    addNotification('success', 'Chuyển truyện thuê thành công!');
    isConvertRentalModalOpen.value = false;
    await loadTitles();
    const updatedBook = books.value.find(b => b.id === selectedBook.value?.id);
    if (updatedBook) selectedVolume.value = updatedBook.volumes.find((v: any) => v.id === selectedVolume.value?.id);
  } catch(err: any) {
    addNotification('error', err.message || 'Lỗi lưu bản sao');
  }
};

// ─── Format helpers ───────────────────────────────────────────────────────────
const statusMap: Record<string, string> = {
  'available': 'Có sẵn',
  'rented': 'Đang thuê',
  'maintenance': 'Bảo trì',
  'lost': 'Bị mất',
  'damaged': 'Hư hỏng',
  'sold': 'Đã bán'
};
const reverseStatusMap: Record<string, string> = {
  'Có sẵn': 'available',
  'Đã thuê': 'rented',
  'Bảo trì': 'maintenance'
};
const getStatusText = (status: string): string => statusMap[status] || status;
const formatVND = (val: number) => {
  if (typeof val !== 'number') return '—';
  return val.toLocaleString('vi-VN') + 'đ';
};
</script>
<style scoped>
/* ----- RESET & CONTAINER ----- */
.manager-container {
  padding: 20px 24px;
  background: #f8fafc;
  min-height: 100vh;
  font-family: 'Inter', system-ui, -apple-system, sans-serif;
}
.loading-overlay {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(255,255,255,0.8);
  backdrop-filter: blur(4px);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  z-index: 1000;
  font-weight: 600;
  color: #1e293b;
}
.spinner {
  width: 40px; height: 40px;
  border: 4px solid #e2e8f0;
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* ----- HEADER CARD ----- */
.header-card {
  background: white;
  border-radius: 28px;
  padding: 20px 28px;
  margin-bottom: 32px;
  border: 1px solid #eef2f6;
  box-shadow: 0 4px 12px rgba(0,0,0,0.02);
}
.header-left { margin-bottom: 16px; }
.page-title { font-size: 1.9rem; font-weight: 700; color: #0f172a; margin: 0 0 4px; }
.page-subtitle { color: #5b6e8c; margin: 0; font-size: 0.9rem; }
.header-actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}
.search-group { flex: 2; min-width: 240px; }
.search-input {
  width: 100%;
  padding: 12px 16px;
  border: 1px solid #e2e8f0;
  border-radius: 40px;
  font-size: 0.9rem;
  background: #fefefe;
  transition: 0.2s;
}
.search-input:focus { outline: none; border-color: #3b82f6; box-shadow: 0 0 0 3px rgba(59,130,246,0.1); }
.filters { display: flex; gap: 12px; flex-wrap: wrap; }
.filter-select {
  padding: 10px 14px;
  border: 1px solid #e2e8f0;
  border-radius: 40px;
  background: white;
  font-size: 0.85rem;
  cursor: pointer;
}
.action-buttons { display: flex; gap: 12px; }
.btn-icon {
  background: #f1f5f9;
  border: none;
  border-radius: 40px;
  width: 46px;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  transition: 0.2s;
}
.btn-icon:hover { background: #e2e8f0; }
.btn-primary, .btn-secondary {
  border: none;
  border-radius: 40px;
  padding: 10px 20px;
  font-weight: 600;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  transition: 0.2s;
}
.btn-primary { background: #3b82f6; color: white; box-shadow: 0 2px 4px rgba(59,130,246,0.2); }
.btn-secondary { background: white; border: 1px solid #cbd5e1; color: #334155; }
.btn-primary:hover, .btn-secondary:hover { opacity: 0.9; transform: translateY(-1px); }

.btn-refresh, .btn-export {
  background: linear-gradient(135deg, #ffffff, #f8fafc);
  border: 1px solid #e2e8f0;
  border-radius: 60px;
  width: 48px;
  height: 48px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.25s cubic-bezier(0.2, 0.9, 0.4, 1.1);
  box-shadow: 0 1px 2px rgba(0,0,0,0.02);
}

.btn-refresh:hover, .btn-export:hover {
  transform: translateY(-2px);
  background: white;
  border-color: #cbd5e1;
  box-shadow: 0 10px 20px -8px rgba(0,0,0,0.12);
}

.btn-refresh:active, .btn-export:active {
  transform: translateY(1px);
}

.btn-refresh .material-icons, .btn-export .material-icons {
  font-size: 1.4rem;
  color: #475569;
  transition: color 0.2s;
}

.btn-refresh:hover .material-icons {
  color: #3b82f6;
}

.btn-export:hover .material-icons {
  color: #10b981;
}
/* ─── Input Date (lịch) ───────────────────────────────────────────────── */
.glass-input[type="date"] {
  position: relative;
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 60px;
  padding: 0.8rem 2.8rem 0.8rem 1.2rem; /* chừa chỗ icon */
  font-size: 0.9rem;
  color: #1e293b;
  width: 100%;
}

.glass-input[type="date"]:hover {
  border-color: #cbd5e1;
  background: #ffffff;
  box-shadow: 0 2px 6px rgba(0,0,0,0.02);
}

.glass-input[type="date"]:focus {
  border-color: #3b82f6;
  box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.1);
  outline: none;
}

/* Tùy chỉnh icon lịch trên Chrome/Edge */
.glass-input[type="date"]::-webkit-calendar-picker-indicator {
   position: absolute;
   right: 12px;
  background: transparent;
  color: #4d8de8;
  cursor: pointer;
  padding: 6px;
  border-radius: 30px;
  transition: background 0.2s;
}

.glass-input[type="date"]::-webkit-calendar-picker-indicator:hover {
  background: #c1d3eb;
  color: #4d8de8;

}

/* Khi chưa có giá trị (hiển thị placeholder ảo) */
.glass-input[type="date"]:invalid {
  color: #94a3b8;
}

/* Hiển thị popup lịch (trình duyệt hỗ trợ) với padding đẹp hơn */
.glass-input[type="date"]::-webkit-datetime-edit {
  padding: 0 0.2rem;
}
.glass-input[type="date"]::-webkit-datetime-edit-fields-wrapper {
  color: #1e293b;
}
/* ----- BOOKS GRID ----- */
.books-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  gap: 24px;
}
.book-card {
  background: white;
  border-radius: 20px;
  border: 1px solid #eef2f8;
  padding: 16px;
  display: flex;
  gap: 16px;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 2px 5px rgba(0,0,0,0.02);
}
.book-card:hover { transform: translateY(-4px); box-shadow: 0 16px 28px -12px rgba(0,0,0,0.12); border-color: #d9e2ef; }
.book-cover { flex-shrink: 0; width: 85px; height: 120px; border-radius: 12px; overflow: hidden; background: #f8fafc; }
.book-cover img { width: 100%; height: 100%; object-fit: cover; }
.book-info { flex: 1; }
.book-title { font-weight: 700; font-size: 1.1rem; color: #0f172a; margin-bottom: 6px; }
.book-meta { display: flex; gap: 12px; margin-bottom: 6px; font-size: 0.75rem; }
.badge-author, .badge-genre { background: #f1f5f9; padding: 2px 10px; border-radius: 40px; color: #334155; }
.book-publisher { font-size: 0.8rem; color: #5b6e8c; margin-bottom: 4px; }
.book-code { font-family: monospace; font-size: 0.7rem; color: #3b82f6; margin-bottom: 8px; }
.book-desc { font-size: 0.8rem; color: #475569; line-height: 1.4; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.book-actions { display: flex; flex-direction: column; gap: 8px; justify-content: flex-start; }
.icon-btn { background: none; border: none; cursor: pointer; font-size: 1.2rem; padding: 6px; border-radius: 12px; }
.icon-btn.edit:hover { background: #e0f2fe; color: #0284c7; }
.icon-btn.delete:hover { background: #fee2e2; color: #dc2626; }
.empty-state { grid-column: 1/-1; text-align: center; padding: 60px 20px; color: #94a3b8; background: white; border-radius: 32px; }

/* ----- TABLES (Volume & Items) ----- */
.volume-table-wrapper, .items-table-wrapper { overflow-x: auto; width: 100%; }
.volume-table, .items-table { width: 100%; border-collapse: collapse; font-size: 0.85rem; min-width: 600px; }
.volume-table th, .items-table th { text-align: left; padding: 12px 8px; background: #f8fafc; color: #475569; font-weight: 600; }
.volume-table td, .items-table td { padding: 12px 8px; border-bottom: 1px solid #eef2f8; }
.actions { display: flex; gap: 6px; justify-content: flex-end; }
.icon-small {
  background: none; border: none; cursor: pointer; padding: 4px; border-radius: 8px;
  display: inline-flex; font-size: 1.1rem;
}
.icon-small.edit:hover { background: #e0f2fe; }
.icon-small.delete:hover { background: #fee2e2; }
.icon-small.restock:hover { background: #dcfce7; }
.icon-small.convert:hover { background: #fef3c7; }
.type-badge { display: inline-block; padding: 4px 10px; border-radius: 30px; font-size: 0.7rem; font-weight: 600; }
.type-badge.retail { background: #dbeafe; color: #1e40af; }
.type-badge.rental { background: #fef3c7; color: #b45309; }
.code-cell { font-family: monospace; font-weight: 500; }

/* ----- FORMS ----- */
.form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
.form-group.full-width { grid-column: span 2; }
.form-group label { display: block; font-weight: 600; font-size: 0.8rem; color: #334155; margin-bottom: 6px; }
.form-group input, .form-group textarea, .form-group select {
  width: 100%; padding: 10px 12px; border: 1px solid #e2e8f0; border-radius: 14px;
  font-family: inherit; background: white;
}
.isbn-input-group { display: flex; gap: 10px; }
.scan-status.success { color: #15803d; }
.scan-status.error { color: #b91c1c; }
.hint { display: block; font-size: 0.7rem; color: #6c757d; margin-top: 4px; }
.cover-preview { max-width: 120px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }

/* ----- RESPONSIVE ----- */
@media (max-width: 768px) {
  .manager-container { padding: 16px; }
  .header-card { padding: 16px; }
  .header-actions { flex-direction: column; align-items: stretch; }
  .filters { justify-content: space-between; }
  .action-buttons { justify-content: flex-end; }
  .books-grid { grid-template-columns: 1fr; }
  .book-card { flex-direction: column; align-items: center; text-align: center; }
  .book-cover { width: 120px; height: 160px; }
  .book-actions { flex-direction: row; justify-content: center; }
  .form-grid { grid-template-columns: 1fr; }
  .form-group.full-width { grid-column: span 1; }
}
.modal-large :deep(.modal-content) { width: 90%; max-width: 1000px; }
.modal-extra-large :deep(.modal-content) { width: 1100px; max-width: 95vw; }
@media (max-width: 640px) {
  .modal-large :deep(.modal-content), .modal-extra-large :deep(.modal-content) { width: 95vw; }
}

.view-tabs {
  display: flex;
  gap: 16px;
  margin-bottom: 20px;
  border-bottom: 1px solid #e2e8f0;
  padding-bottom: 2px;
}

.tab-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  border: none;
  background: transparent;
  color: #64748b;
  font-weight: 700;
  font-size: 0.95rem;
  cursor: pointer;
  position: relative;
  transition: all 0.2s;
}

.tab-item:hover {
  color: #2563eb;
}

.tab-item.active {
  color: #2563eb;
}

.tab-item.active::after {
  content: "";
  position: absolute;
  bottom: -2px;
  left: 0;
  width: 100%;
  height: 3px;
  background: #2563eb;
  border-radius: 999px;
}
.screen-loading-state {
  border-radius: 14px;
  border: 1px solid #dbeafe;
  background: white;
  color: #1e3a8a;
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 8px;
  padding: 18px;
  font-weight: 700;
}
.spin {
  animation: spin 1s linear infinite;
}
@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
.logs-container {
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-height: calc(100vh - 280px);
  overflow-y: auto;
  padding-right: 4px;
}
.log-card {
  display: flex;
  gap: 16px;
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 16px;
  transition: transform 0.2s, box-shadow 0.2s;
}
.log-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.05);
}
.log-icon {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.log-icon.stock_in { background: #ecfdf5; color: #10b981; }
.log-icon.convert { background: #eff6ff; color: #3b82f6; }
.log-icon.price_change { background: #fff7ed; color: #f97316; }
.log-icon.adjust { background: #fef2f2; color: #ef4444; }
.log-icon.default { background: #f8fafc; color: #64748b; }
.log-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.log-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.log-user {
  font-weight: 800;
  color: #1e293b;
  font-size: 0.9rem;
}
.log-time {
  font-size: 0.75rem;
  color: #94a3b8;
}
.log-message {
  font-size: 0.95rem;
  line-height: 1.4;
}
.log-action {
  font-weight: 700;
  color: #1e293b;
}
.log-target {
  color: #475569;
}
.log-note {
  margin: 4px 0 0;
  font-size: 0.85rem;
  color: #64748b;
  font-style: italic;
  background: #f8fafc;
  padding: 6px 10px;
  border-radius: 6px;
}
.log-delta {
  margin-top: 6px;
  font-size: 0.85rem;
  color: #475569;
  font-weight: 600;
  background: #f1f5f9;
  padding: 4px 10px;
  border-radius: 6px;
  align-self: flex-start;
}
.log-delta .plus { color: #10b981; }
.log-delta .minus { color: #ef4444; }

/* ─── Stats Tab Premium Enhancements ────────────────────────────────────────── */
.stats-tab-content {
  padding: 1.5rem 0;
  display: flex;
  flex-direction: column;
  gap: 2.5rem;
  animation: fadeSlideUp 0.6s cubic-bezier(0.2, 0.8, 0.2, 1);
}

@keyframes fadeSlideUp {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

/* KPI Metrics Row */
.stats-metrics-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 1.5rem;
}

.metric-card {
  background: white;
  border-radius: 28px;
  padding: 1.5rem;
  display: flex;
  gap: 1.2rem;
  align-items: center;
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
  border: 1px solid #f1f5f9;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
  position: relative;
  overflow: hidden;
}

.metric-card:hover {
  transform: translateY(-8px);
  box-shadow: 0 20px 40px -12px rgba(0, 0, 0, 0.1);
}

.metric-icon {
  width: 60px; height: 60px;
  border-radius: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.metric-icon span { font-size: 2rem; color: white; }

.metric-icon.stock { background: linear-gradient(135deg, #22c55e, #16a34a); }
.metric-icon.sale { background: linear-gradient(135deg, #ef4444, #dc2626); }
.metric-icon.rental { background: linear-gradient(135deg, #f59e0b, #d97706); }
.metric-icon.circulation { background: linear-gradient(135deg, #8b5cf6, #7c3aed); }

.metric-info { display: flex; flex-direction: column; gap: 4px; }
.metric-label { font-size: 0.75rem; color: #64748b; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; }
.metric-value { font-size: 1.75rem; font-weight: 900; color: #0f172a; font-variant-numeric: tabular-nums; }
.metric-trend { margin-top: 8px; font-size: 0.8rem; font-weight: 700; }

/* Filter Bar */
.stats-filters.glass {
  display: flex;
  flex-wrap: wrap;
  gap: 1.5rem;
  background: rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(12px);
  padding: 1.5rem 2rem;
  border-radius: 36px;
  border: 1px solid rgba(255, 255, 255, 0.8);
  box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.04);
  align-items: flex-end;
}

.filter-group { display: flex; flex-direction: column; gap: 8px; flex: 1; min-width: 180px; }
.filter-group label { font-size: 0.8rem; font-weight: 700; color: #475569; padding-left: 4px; }

.glass-select, .glass-input {
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 40px;
  padding: 0.8rem 1.2rem;
  font-size: 0.9rem;
  transition: all 0.2s;
  color: #1e293b;
}

.glass-select:focus, .glass-input:focus {
  border-color: #3b82f6;
  box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.1);
  outline: none;
}

.filter-actions { display: flex; gap: 12px; }

/* Visual Containers */
/* Premium Table Refinements */
.premium-table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0 8px;
  table-layout: fixed; /* Quan trọng: kiểm soát độ rộng cột */
}
.premium-table th,
.premium-table td {
  padding: 1rem 0.8rem;
  vertical-align: middle;
  overflow: hidden;
  text-overflow: ellipsis;
}
.premium-table tr.hover-row { 
  background: white; 
  box-shadow: 0 2px 4px rgba(0,0,0,0.02); 
  transition: all 0.3s ease; 
}
.premium-table tr.hover-row:hover { 
  transform: scale(1.01); 
  box-shadow: 0 12px 20px -10px rgba(0,0,0,0.08); 
  z-index: 10;
}

.premium-table th:nth-child(1),
.premium-table td:nth-child(1) {
  width: 35%; /* Cột Thời gian */
}
.premium-table th:nth-child(2),
.premium-table td:nth-child(2) {
  width: 20%; /* Nhập kho */
}
.premium-table th:nth-child(3),
.premium-table td:nth-child(3) {
  width: 20%; /* Bán ra */
}
.premium-table th:nth-child(4),
.premium-table td:nth-child(4) {
  width: 20%; /* Cho thuê */
}
.premium-table th:nth-child(5),
.premium-table td:nth-child(5) {
  width: 5%; /* Chi tiết - cố định nhỏ */
  text-align: center;
}

/* Căn chỉnh nội dung */
.premium-table th.text-right,
.premium-table td.text-right {
  text-align: right;
}
.premium-table th.text-center,
.premium-table td.text-center {
  text-align: center;
}

/* Giữ nguyên hover và border-radius nếu có */
.premium-table tr.hover-row {
  background: white;
  transition: all 0.2s ease;
  border-radius: 16px;
}
.premium-table tr.hover-row:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px -8px rgba(0, 0,  0, 0.1);
  background: #ffffff;
}
.premium-table td:first-child {
  border-top-left-radius: 16px;
  border-bottom-left-radius: 16px;
}
.premium-table td:last-child {
  border-top-right-radius: 16px;
  border-bottom-right-radius: 16px;
}
.icon-detail.premium {
  background: linear-gradient(135deg, #f8fafc, #f1f5f9);
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  width: 42px; height: 42px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: #3b82f6;
  transition: all 0.2s;
}

.icon-detail.premium:hover {
  background: #3b82f6;
  color: white;
  border-color: #3b82f6;
  transform: translateY(-2px) rotate(5deg);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
}

.icon-detail.premium span { font-size: 1.3rem; }


/* Detail modal refinements - EXPANDED */
.modal-large :deep(.modal-content) { 
  border-radius: 32px; 
  overflow: hidden; 
  width: 90%;
  max-width: 1000px;
}

.detail-summary { 
  display: grid; 
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); 
  gap: 1.5rem; 
  background: #f8fafc; 
  padding: 2rem; 
  border-radius: 28px; 
  margin-bottom: 2.5rem; 
  border: 1px solid #f1f5f9;
}


.detail-stat { 
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.detail-stat span { font-size: 0.7rem; color: #64748b; font-weight: 700; text-transform: uppercase; }
.detail-stat strong { font-size: 1.4rem; font-weight: 800; color: #1e293b; }

.volume-name { font-weight: 700; color: #1e293b; margin-bottom: 2px; }
.volume-isbn { font-size: 0.75rem; color: #94a3b8; font-family: monospace; }

.value-positive { color: #22c55e; font-weight: 700; }
.value-negative { color: #ef4444; font-weight: 700; }
.value-warning { color: #f59e0b; font-weight: 700; }

.modal-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 3rem;
  gap: 1rem;
  color: #64748b;
}

.spinner-mini { 
  width: 32px; height: 32px; 
  border: 3px solid #e2e8f0; 
  border-top-color: #3b82f6; 
  border-radius: 50%; 
  animation: spin 0.8s linear infinite; 
}

.stats-visual-container, .stats-table-container {
  background: white;
  border-radius: 36px;
  padding: 2.5rem;
  box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.04);
  border: 1px solid #f8fafc;
  width: 100%;
}

.chart-header, .table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
}

.chart-header h3, .table-header h3 { font-size: 1.25rem; font-weight: 800; color: #0f172a; margin: 0; }

.chart-wrapper { height: 400px; position: relative; }

/* Table Controls */
.table-controls { display: flex; gap: 1.5rem; align-items: center; }
.table-search {
  padding: 0.8rem 1.4rem;
  border: 1px solid #e2e8f0;
  border-radius: 40px;
  background: #f8fafc;
  font-size: 0.9rem;
  width: 280px;
  transition: all 0.2s;
}
.table-search:focus { background: white; border-color: #3b82f6; width: 320px; outline: none; }

/* Skeleton */
.skeleton-stats { display: flex; flex-direction: column; gap: 2rem; }
.skeleton-chart { height: 400px; background: linear-gradient(90deg, #f1f5f9 25%, #e2e8f0 50%, #f1f5f9 75%); background-size: 200% 100%; animation: shimmer 1.5s infinite; border-radius: 36px; }
@keyframes shimmer { 0% { background-position: -200% 0; } 100% { background-position: 200% 0; } }

/* Pagination */
.pagination { display: flex; gap: 0.8rem; align-items: center; }
.pagination button {
  width: 38px; height: 38px;
  border-radius: 50%;
  border: none;
  background: #f1f5f9;
  color: #475569;
  font-size: 1.2rem;
  cursor: pointer;
  transition: all 0.2s;
}
.pagination button:hover:not(:disabled) { background: #3b82f6; color: white; transform: scale(1.1); }
.pagination button:disabled { opacity: 0.4; cursor: not-allowed; }

/* ─── Modal chi tiết cải tiến ──────────────────────────────────────────────── */
.modal-detail :deep(.modal-content) {
  border-radius: 32px;
  overflow: hidden;
  width: 90%;
  max-width: 900px;
  background: linear-gradient(145deg, #ffffff, #fefefe);
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
}

.detail-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem;
  gap: 1rem;
  color: #3b82f6;
  font-weight: 600;
}

/* Tóm tắt tổng quan */
.detail-summary {
  display: flex;
  flex-wrap: wrap;
  gap: 1.5rem;
  margin-bottom: 2.5rem;
  justify-content: center;
}

.summary-card {
  background: white;
  border-radius: 24px;
  padding: 1.2rem 1.8rem;
  display: flex;
  align-items: center;
  gap: 1.2rem;
  box-shadow: 0 8px 20px -6px rgba(0, 0, 0, 0.05);
  border: 1px solid #f1f5f9;
  transition: all 0.25s ease;
  min-width: 160px;
}

.summary-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 20px 30px -12px rgba(0, 0, 0, 0.1);
}

.summary-icon {
  width: 48px;
  height: 48px;
  border-radius: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.summary-icon.stock { background: linear-gradient(135deg, #22c55e, #16a34a); }
.summary-icon.sale { background: linear-gradient(135deg, #ef4444, #dc2626); }
.summary-icon.rental { background: linear-gradient(135deg, #f59e0b, #d97706); }

.summary-icon span { font-size: 1.6rem; color: white; }

.summary-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.summary-label {
  font-size: 0.7rem;
  font-weight: 700;
  text-transform: uppercase;
  color: #64748b;
  letter-spacing: 0.03em;
}

.summary-value {
  font-size: 1.6rem;
  font-weight: 800;
  color: #0f172a;
  line-height: 1.2;
  font-variant-numeric: tabular-nums;
}

/* Bảng chi tiết */
.detail-table-wrapper {
  overflow-x: auto;
  border-radius: 20px;
  border: 1px solid #eef2f6;
  background: white;
}

.detail-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.9rem;
}

.detail-table th {
  text-align: left;
  padding: 1rem 1.2rem;
  background: #f8fafc;
  color: #475569;
  font-weight: 700;
  font-size: 0.8rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  border-bottom: 1px solid #e2e8f0;
}

.detail-table td {
  padding: 1rem 1.2rem;
  border-bottom: 1px solid #f1f5f9;
  vertical-align: middle;
}

.detail-row:hover {
  background: #fafcff;
}

.volume-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.volume-name {
  font-weight: 700;
  color: #1e293b;
}

.volume-isbn {
  font-size: 0.7rem;
  color: #94a3b8;
  font-family: monospace;
}

/* Các class text-right đã có, chỉ bổ sung nếu thiếu */
.text-right {
  text-align: right;
}

/* Responsive */
@media (max-width: 640px) {
  .detail-summary {
    flex-direction: column;
    align-items: stretch;
  }
  .summary-card {
    justify-content: center;
  }
  .detail-table th, .detail-table td {
    padding: 0.75rem 0.8rem;
  }
}
</style>
