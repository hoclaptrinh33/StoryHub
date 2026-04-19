<template>
  <DefaultLayout>
    <div class="return-container">
      <div class="header-section">
        <div class="title-meta">
          <h2 class="page-title">Kiểm Định Trả Truyện</h2>
          <p class="subtitle">
            Quét hợp đồng, kiểm định tình trạng và kết toán thuê-trả theo thời gian thực
          </p>
        </div>
        <div class="state-pill" :class="screenState">
          <span class="material-icons">monitoring</span>
          {{ screenStateLabel }}
        </div>
      </div>

      <transition name="fade">
        <div v-if="recoverableError" class="retry-banner">
          <span class="material-icons">warning</span>
          <div class="copy">
            <strong>{{ recoverableError.title }}</strong>
            <span>{{ recoverableError.message }}</span>
          </div>
          <button class="btn-retry" @click="retrySettlement">Thử lại</button>
        </div>
      </transition>

      <transition name="fade">
        <div v-if="scannerToast.message" :class="['scanner-toast', scannerToast.type]">
          <span class="material-icons">{{ scannerToast.icon }}</span>
          {{ scannerToast.message }}
        </div>
      </transition>

      <div class="return-grid-layout">
        <section class="card-glass">
          <div class="card-header-lux">
            <h3>
              <span class="material-icons">assignment_return</span>
              Phiếu Thuê
            </h3>
            <p class="hotkey-hint">
              Phím tắt: <kbd>F1</kbd>/<kbd>Enter</kbd> kiểm tra hoặc kết toán,
              <kbd>Esc</kbd> hủy phiên.
            </p>
          </div>

          <div class="contract-search-wrap" :class="{ 'scan-highlight': inputHighlight }">
            <span class="material-icons">manage_search</span>
            <input
              ref="contractInputRef"
              v-model="contractInput"
              type="text"
              placeholder="Quét hoặc nhập mã hợp đồng (ví dụ: 2001)..."
              @keyup.enter="checkOrSubmit"
              data-testid="rental-return-contract-input"
            />
            <button
              class="btn-action"
              type="button"
              :disabled="isCheckingContract || isSettling"
              @click="loadContractPreview"
              data-testid="rental-return-check-button"
            >
              {{ isCheckingContract ? "Đang kiểm tra" : "Kiểm tra" }}
            </button>
          </div>
          <p class="contract-guidance">Gợi ý: mã hợp đồng thường là dạng số, hiển thị ngay sau giao dịch thuê thành công (ví dụ HĐ #1234). Có thể quét trực tiếp phiếu/mã để vào phiên trả mà không cần nhập tay.</p>

          <div class="contract-lookup-panel">
            <div class="contract-lookup-header">
              <strong>Hợp đồng đang thuê</strong>
              <button
                class="lookup-refresh-btn"
                type="button"
                :disabled="isLoadingContractLookup"
                @click="refreshReturnableContracts"
              >
                {{ isLoadingContractLookup ? "Đang tải..." : "Làm mới" }}
              </button>
            </div>

            <div class="contract-lookup-search">
              <span class="material-icons">search</span>
              <input
                v-model="contractLookupQuery"
                type="text"
                placeholder="Tìm theo mã HĐ, tên khách hoặc SĐT..."
                data-testid="rental-return-contract-list-search"
              />
            </div>

            <div class="contract-lookup-filters">
              <button
                v-for="option in contractLookupStatusFilterOptions"
                :key="option.value"
                type="button"
                :class="[
                  'lookup-filter-btn',
                  { active: contractLookupStatusFilter === option.value },
                ]"
                @click="contractLookupStatusFilter = option.value"
              >
                {{ option.label }}
              </button>
            </div>

            <div v-if="contractLookupError" class="lookup-error">
              {{ contractLookupError }}
            </div>
            <div v-else-if="isLoadingContractLookup" class="lookup-loading">
              <span class="material-icons spin">autorenew</span>
              Đang tải danh sách hợp đồng...
            </div>
            <ul v-else-if="filteredReturnableContracts.length > 0" class="contract-lookup-list">
              <li
                v-for="contract in filteredReturnableContracts"
                :key="contract.contract_id"
                class="contract-lookup-item"
                :class="{ active: Number(contract.contract_id) === activeContractId }"
              >
                <button
                  class="contract-lookup-button"
                  type="button"
                  :disabled="isCheckingContract || isSettling"
                  @click="selectContractFromLookup(contract.contract_id)"
                >
                  <div class="lookup-top-row">
                    <strong>HĐ #{{ contract.contract_id }}</strong>
                    <span :class="['lookup-status-chip', contract.statusClass]">
                      {{ contract.statusLabel }}
                    </span>
                  </div>
                  <div class="lookup-bottom-row">
                    <span>{{ contract.customer_name }} • {{ contract.customer_phone }}</span>
                    <span>{{ contract.open_item_count }} item chưa trả</span>
                    <span>Hạn trả {{ contract.dueDate }}</span>
                    <span>Đầu sách: {{ contract.rentedItemsPreview }}</span>
                  </div>
                </button>
              </li>
            </ul>
            <p v-else class="lookup-empty">
              Không có hợp đồng phù hợp với bộ lọc hiện tại.
            </p>
          </div>

          <div v-if="isCheckingContract" class="inline-loading">
            <span class="material-icons spin">autorenew</span>
            Đang tải dữ liệu hợp đồng...
          </div>

          <div v-if="currentContract" class="contract-meta-grid">
            <div class="meta-item">
              <span class="lbl">Hợp đồng</span>
              <strong>#{{ currentContract.id }}</strong>
            </div>
            <div class="meta-item">
              <span class="lbl">Khách hàng</span>
              <strong>{{ currentContract.customer }}</strong>
            </div>
            <div class="meta-item">
              <span class="lbl">Hạn trả</span>
              <strong>{{ currentContract.dueDate }}</strong>
            </div>
            <div class="meta-item">
              <span class="lbl">Cọc còn lại</span>
              <strong>{{ formatCurrency(currentContract.deposit) }}</strong>
            </div>
          </div>

          <div v-if="currentContract" class="line-table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Item</th>
                  <th style="width: 130px">Trạng thái quét</th>
                  <th style="width: 290px">Condition sau trả</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="(line, index) in returnLines"
                  :key="line.item_id"
                  :class="[
                    { active: selectedLineIndex === index },
                    { 'scan-highlight': line.highlight },
                    { duplicate: line.duplicate },
                  ]"
                  @click="selectedLineIndex = index"
                >
                  <td>
                    <div class="line-title-block">
                      <strong>{{ line.title }}</strong>
                      <span class="code">{{ line.item_id }} • {{ line.barcode }}</span>
                    </div>
                  </td>
                  <td>
                    <span :class="['scan-state', lineScanStateClass(line)]">
                      {{ lineScanStateLabel(line) }}
                    </span>
                  </td>
                  <td>
                    <div class="condition-chip-group">
                      <button
                        v-for="option in conditionOptions"
                        :key="option.value"
                        type="button"
                        :class="[
                          'condition-chip',
                          option.className,
                          { active: line.condition_after === option.value },
                        ]"
                        @click.stop="setCondition(index, option.value)"
                      >
                        {{ option.hotkey }}. {{ option.label }}
                      </button>
                    </div>
                  </td>
                </tr>
                <tr v-if="returnLines.length === 0">
                  <td colspan="3" class="empty-row">Chưa có item nào để kiểm định.</td>
                </tr>
              </tbody>
            </table>
          </div>

          <div v-if="currentContract" class="quick-preset-row">
            <button type="button" class="btn-preset good" @click="setAllConditions('good')">
              <span class="material-icons">done_all</span>
              Tất cả tốt
            </button>
            <button type="button" class="btn-preset lost" @click="setAllConditions('lost')">
              <span class="material-icons">remove_circle</span>
              Đánh dấu mất hết
            </button>
          </div>

          <div v-else class="empty-state">
            <span class="material-icons">inventory</span>
            <p>Quét hợp đồng để bắt đầu phiên trả truyện.</p>
          </div>
        </section>

        <aside class="card-glass sticky-panel">
          <div class="card-header-lux">
            <h3>
              <span class="material-icons">receipt_long</span>
              Kết toán
            </h3>
          </div>

          <div class="summary-box">
            <div class="line" :class="summaryFlashClass">
              <span>Phí thuê</span>
              <strong>{{ formatCurrency(summary.rental_fee) }}</strong>
            </div>
            <div class="line" :class="summaryFlashClass">
              <span>Phí trễ hạn</span>
              <strong>{{ formatCurrency(summary.late_fee) }}</strong>
            </div>
            <div class="line" :class="summaryFlashClass">
              <span>Phí hư hỏng</span>
              <strong>{{ formatCurrency(summary.damage_fee) }}</strong>
            </div>
            <div class="line" :class="summaryFlashClass">
              <span>Phí mất</span>
              <strong>{{ formatCurrency(summary.lost_fee) }}</strong>
            </div>

            <div class="divider"></div>

            <div class="line total" :class="summaryFlashClass">
              <span>Tổng phí</span>
              <strong>{{ formatCurrency(summary.total_fee) }}</strong>
            </div>
            <div class="line" :class="summaryFlashClass">
              <span>Trừ vào cọc</span>
              <strong>{{ formatCurrency(summary.deducted_from_deposit) }}</strong>
            </div>
            <div class="line success" :class="summaryFlashClass">
              <span>Hoàn khách</span>
              <strong>{{ formatCurrency(summary.refund_to_customer) }}</strong>
            </div>
            <div class="line warning" :class="summaryFlashClass">
              <span>Nợ còn lại</span>
              <strong>{{ formatCurrency(summary.remaining_debt) }}</strong>
            </div>
          </div>

          <p class="hotkey-hint condition-hotkey">
            Condition nhanh: <kbd>1</kbd> tốt, <kbd>2</kbd> hỏng nhẹ,
            <kbd>3</kbd> hỏng nặng, <kbd>4</kbd> mất.
          </p>

          <button
            class="btn-settle"
            type="button"
            :disabled="!canSubmitSettlement || isSettling"
            @click="submitSettlement"
            data-testid="rental-return-confirm-button"
          >
            <span class="material-icons">task_alt</span>
            {{ isSettling ? "Đang gửi settlement..." : "Xác nhận & Kết toán" }}
          </button>
          <button class="btn-reset" type="button" @click="resetWorkflow">
            Hủy phiên hoàn trả
          </button>
        </aside>
      </div>

      <HotkeyBar :items="hotkeyItems" />

      <div v-if="isSettling" class="overlay-loading">
        <div class="overlay-card">
          <span class="material-icons spin">sync</span>
          Đang thực hiện settlement. Vui lòng chờ...
        </div>
      </div>
    </div>
  </DefaultLayout>
</template>

<script setup lang="ts">
import { computed, inject, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { useRoute } from "vue-router";

import { useWebSocket } from "../composables/useWebSocket";
import DefaultLayout from "../components/layout/defaultLayout.vue";
import HotkeyBar, { type HotkeyItem } from "../components/layout/HotkeyBar.vue";
import {
  fetchRentalSettlementStatus,
  fetchRentalContractPreview,
  fetchReturnableRentalContracts,
  StoryHubApiError,
  buildRequestId,
  returnRentalItems,
  type RentalContractPreviewPayload,
  type ReturnableRentalContractListItem,
  type RentalReturnCondition,
  type ReturnRentalItemsPayload,
} from "../services/storyhubApi";
import type {
  ItemStatusChangedEvent,
  RentalSettlementFinishedEvent,
} from "../types/realtime";
import { toUiErrorMessage } from "../utils/backendErrorMessages";
import { playScanAudio } from "../utils/scanAudio";

interface ScannerScanEventDetail {
  code?: string;
}

interface HotkeyEventDetail {
  name?:
    | "f1"
    | "f2"
    | "escape"
    | "enter"
    | "digit-1"
    | "digit-2"
    | "digit-3"
    | "digit-4"
    | "arrow-up"
    | "arrow-down";
}

interface ScannerToastUi {
  message: string;
  type: "success" | "warning" | "error";
  icon: string;
}

interface ReturnLinePreset {
  item_id: string;
  barcode: string;
  title: string;
  rental_fee: number;
  final_deposit: number;
  overdue_days: number;
}

interface ContractPreviewUi {
  id: number;
  customer: string;
  dueDate: string;
  deposit: number;
  overdueFeePerDay: number;
  damageFeeMinorPercent: number;
  damageFeeMajorPercent: number;
  lines: ReturnLinePreset[];
}

interface ReturnableContractLookupUi {
  contract_id: string;
  customer_name: string;
  customer_phone: string;
  rentedItemsPreview: string;
  status: ReturnableRentalContractListItem["status"];
  statusLabel: string;
  statusClass: "status-active" | "status-partial" | "status-overdue";
  dueDate: string;
  open_item_count: number;
}

type ContractLookupStatusFilter =
  | "all"
  | ReturnableRentalContractListItem["status"];

interface ReturnLineUi extends ReturnLinePreset {
  condition_after: RentalReturnCondition;
  scanned: boolean;
  duplicate: boolean;
  highlight: boolean;
}

interface RecoverableError {
  title: string;
  message: string;
}

const conditionOptions: Array<{
  value: RentalReturnCondition;
  label: string;
  hotkey: string;
  className: string;
}> = [
  { value: "good", label: "Tốt", hotkey: "1", className: "good" },
  {
    value: "minor_damage",
    label: "Hỏng nhẹ",
    hotkey: "2",
    className: "minor",
  },
  {
    value: "major_damage",
    label: "Hỏng nặng",
    hotkey: "3",
    className: "major",
  },
  { value: "lost", label: "Mất", hotkey: "4", className: "lost" },
];

const hotkeyItems: HotkeyItem[] = [
  { key: "F1 / Enter", label: "Kiểm tra hoặc kết toán" },
  { key: "F2", label: "Focus ô nhập hợp đồng" },
  { key: "↑ ↓", label: "Di chuyển dòng item" },
  { key: "1 2 3 4", label: "Đặt condition" },
  { key: "ESC", label: "Về Command Hub" },
];

const addNotification = inject("addNotification") as (
  type: string,
  msg: string,
) => void;
const route = useRoute();
const ws = useWebSocket();

const contractInput = ref("");
const contractInputRef = ref<HTMLInputElement | null>(null);
const contractLookupQuery = ref("");
const contractLookupStatusFilter = ref<ContractLookupStatusFilter>("all");
const returnableContracts = ref<ReturnableContractLookupUi[]>([]);
const isLoadingContractLookup = ref(false);
const contractLookupError = ref("");
const currentContract = ref<ContractPreviewUi | null>(null);
const returnLines = ref<ReturnLineUi[]>([]);
const selectedLineIndex = ref(0);
const isCheckingContract = ref(false);
const isSettling = ref(false);
const settlementResult = ref<ReturnRentalItemsPayload | null>(null);
const recoverableError = ref<RecoverableError | null>(null);
const scannerToast = ref<ScannerToastUi>({
  message: "",
  type: "success",
  icon: "check_circle",
});
const inputHighlight = ref(false);
const summaryFlashClass = ref<"flash-pos" | "flash-neg" | "">("");

let scannerToastTimer: ReturnType<typeof setTimeout> | null = null;
let inputHighlightTimer: ReturnType<typeof setTimeout> | null = null;
let summaryFlashTimer: ReturnType<typeof setTimeout> | null = null;
let contractLookupDebounceTimer: ReturnType<typeof setTimeout> | null = null;
let contractLookupRequestCounter = 0;
let stopRealtimeItemWatch: (() => void) | null = null;
let stopRealtimeSettlementWatch: (() => void) | null = null;

const scannedLines = computed(() => returnLines.value.filter((line) => line.scanned));

const settlementLines = computed(() =>
  scannedLines.value.length > 0 ? scannedLines.value : returnLines.value,
);

const canSubmitSettlement = computed(
  () => currentContract.value !== null && settlementLines.value.length > 0,
);

const isManualSettlementMode = computed(
  () =>
    currentContract.value !== null &&
    scannedLines.value.length === 0 &&
    returnLines.value.length > 0,
);

const formatContractDate = (rawValue: string): string => {
  const parsed = new Date(rawValue);
  if (Number.isNaN(parsed.getTime())) {
    return rawValue;
  }

  return new Intl.DateTimeFormat("vi-VN", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  }).format(parsed);
};

const mapContractPreview = (
  payload: RentalContractPreviewPayload,
): ContractPreviewUi => {
  return {
    id: Number(payload.contract_id),
    customer: payload.customer_name,
    dueDate: formatContractDate(payload.due_date),
    deposit: payload.remaining_deposit,
    overdueFeePerDay: payload.overdue_fee_per_day,
    damageFeeMinorPercent: payload.damage_fee_minor_percent,
    damageFeeMajorPercent: payload.damage_fee_major_percent,
    lines: payload.return_lines.map((line) => ({
      item_id: line.item_id,
      barcode: line.barcode || line.item_id,
      title: line.title,
      rental_fee: line.rental_fee,
      final_deposit: line.final_deposit,
      overdue_days: line.overdue_days,
    })),
  };
};

const mapReturnableContract = (
  payload: ReturnableRentalContractListItem,
): ReturnableContractLookupUi => {
  let statusLabel = "Đang thuê";
  let statusClass: ReturnableContractLookupUi["statusClass"] = "status-active";

  if (payload.status === "overdue") {
    statusLabel = "Quá hạn";
    statusClass = "status-overdue";
  } else if (payload.status === "partial_returned") {
    statusLabel = "Trả một phần";
    statusClass = "status-partial";
  }

  return {
    contract_id: payload.contract_id,
    customer_name: payload.customer_name,
    customer_phone: payload.customer_phone,
    rentedItemsPreview: payload.rented_items_preview || "Chưa có tên đầu sách",
    status: payload.status,
    statusLabel,
    statusClass,
    dueDate: formatContractDate(payload.due_date),
    open_item_count: payload.open_item_count,
  };
};

const contractLookupStatusFilterOptions: Array<{
  value: ContractLookupStatusFilter;
  label: string;
}> = [
  { value: "all", label: "Tất cả" },
  { value: "active", label: "Đang thuê" },
  { value: "partial_returned", label: "Trả một phần" },
  { value: "overdue", label: "Quá hạn" },
];

const estimatedSummary = computed(() => {
  const contract = currentContract.value;
  if (!contract) {
    return {
      rental_fee: 0,
      late_fee: 0,
      damage_fee: 0,
      lost_fee: 0,
      total_fee: 0,
      deducted_from_deposit: 0,
      refund_to_customer: 0,
      remaining_debt: 0,
    };
  }

  const rentalFee = settlementLines.value.reduce((sum, line) => sum + line.rental_fee, 0);
  const lateFee = settlementLines.value.reduce(
    (sum, line) => sum + line.overdue_days * contract.overdueFeePerDay,
    0,
  );
  const damageFee = settlementLines.value
    .filter(
      (line) =>
        line.condition_after === "minor_damage" ||
        line.condition_after === "major_damage",
    )
    .reduce((sum, line) => {
      if (line.condition_after === "minor_damage") {
        return (
          sum +
          Math.floor(
            (line.final_deposit * contract.damageFeeMinorPercent) / 100,
          )
        );
      }

      return (
        sum +
        Math.floor(
          (line.final_deposit * contract.damageFeeMajorPercent) / 100,
        )
      );
    }, 0);
  const lostFee = settlementLines.value
    .filter((line) => line.condition_after === "lost")
    .reduce((sum, line) => sum + line.final_deposit, 0);

  const totalFee = rentalFee + lateFee + damageFee + lostFee;
  const hasSettlementLine = settlementLines.value.length > 0;
  const deductedFromDeposit = hasSettlementLine
    ? Math.min(totalFee, contract.deposit)
    : 0;
  const refundToCustomer = hasSettlementLine
    ? Math.max(contract.deposit - totalFee, 0)
    : 0;
  const remainingDebt = hasSettlementLine
    ? Math.max(totalFee - contract.deposit, 0)
    : 0;

  return {
    rental_fee: rentalFee,
    late_fee: lateFee,
    damage_fee: damageFee,
    lost_fee: lostFee,
    total_fee: totalFee,
    deducted_from_deposit: deductedFromDeposit,
    refund_to_customer: refundToCustomer,
    remaining_debt: remainingDebt,
  };
});

const summary = computed(() => settlementResult.value ?? estimatedSummary.value);

const screenState = computed(() => {
  if (isSettling.value) {
    return "settling";
  }
  if (isCheckingContract.value) {
    return "loading";
  }
  if (recoverableError.value) {
    return "error";
  }
  if (!currentContract.value) {
    return "empty";
  }
  return "success";
});

const screenStateLabel = computed(() => {
  if (screenState.value === "settling") {
    return "Đang kết toán";
  }
  if (screenState.value === "loading") {
    return "Đang kiểm tra";
  }
  if (screenState.value === "error") {
    return "Cần xử lý lỗi";
  }
  if (screenState.value === "empty") {
    return "Chờ quét hợp đồng";
  }
  return "Sẵn sàng thao tác";
});

const formatCurrency = (value: number) =>
  new Intl.NumberFormat("vi-VN", { style: "currency", currency: "VND" }).format(
    value,
  );

const lineScanStateClass = (line: ReturnLineUi) => {
  if (line.scanned) {
    return "ok";
  }
  if (isManualSettlementMode.value) {
    return "manual";
  }
  return "pending";
};

const lineScanStateLabel = (line: ReturnLineUi) => {
  if (line.scanned) {
    return "Đã quét";
  }
  if (isManualSettlementMode.value) {
    return "Thủ công";
  }
  return "Chờ quét";
};

const normalizeContractId = (rawValue: string): number | null => {
  const digits = rawValue.replace(/\D/g, "");
  if (!digits) {
    return null;
  }

  const parsed = Number(digits);
  if (!Number.isInteger(parsed) || parsed <= 0) {
    return null;
  }

  return parsed;
};

const activeContractId = computed(
  () => currentContract.value?.id ?? normalizeContractId(contractInput.value),
);

const filteredReturnableContracts = computed(() => {
  if (contractLookupStatusFilter.value === "all") {
    return returnableContracts.value;
  }

  return returnableContracts.value.filter(
    (contract) => contract.status === contractLookupStatusFilter.value,
  );
});

const normalizeScanToken = (rawValue: string) =>
  rawValue.replace(/[^A-Za-z0-9]/g, "").toUpperCase();

const flashScannerToast = (
  message: string,
  type: ScannerToastUi["type"] = "success",
) => {
  const iconMap: Record<ScannerToastUi["type"], string> = {
    success: "check_circle",
    warning: "search",
    error: "error",
  };

  scannerToast.value = {
    message,
    type,
    icon: iconMap[type],
  };

  if (scannerToastTimer) {
    clearTimeout(scannerToastTimer);
  }
  scannerToastTimer = setTimeout(() => {
    scannerToast.value.message = "";
    scannerToastTimer = null;
  }, 1300);
};

const flashInputHighlight = () => {
  inputHighlight.value = true;
  if (inputHighlightTimer) {
    clearTimeout(inputHighlightTimer);
  }
  inputHighlightTimer = setTimeout(() => {
    inputHighlight.value = false;
    inputHighlightTimer = null;
  }, 800);
};

const clearDuplicateFlags = () => {
  returnLines.value.forEach((line) => {
    line.duplicate = false;
  });
};

const setCondition = (index: number, condition: RentalReturnCondition) => {
  const target = returnLines.value[index];
  if (!target) {
    return;
  }

  target.condition_after = condition;
  selectedLineIndex.value = index;
};

const setConditionFromHotkey = (hotkeyName: HotkeyEventDetail["name"]) => {
  if (selectedLineIndex.value < 0 || selectedLineIndex.value >= returnLines.value.length) {
    return;
  }

  if (hotkeyName === "digit-1") {
    setCondition(selectedLineIndex.value, "good");
    return;
  }
  if (hotkeyName === "digit-2") {
    setCondition(selectedLineIndex.value, "minor_damage");
    return;
  }
  if (hotkeyName === "digit-3") {
    setCondition(selectedLineIndex.value, "major_damage");
    return;
  }
  if (hotkeyName === "digit-4") {
    setCondition(selectedLineIndex.value, "lost");
  }
};

const setAllConditions = (condition: RentalReturnCondition) => {
  returnLines.value.forEach((line) => {
    line.condition_after = condition;
  });

  if (condition === "good") {
    addNotification("success", "Đã đặt condition tất cả item = Tốt.");
    return;
  }

  addNotification("warning", "Đã đặt condition tất cả item = Mất.");
};

const moveSelectedLine = (delta: number) => {
  if (returnLines.value.length === 0) {
    return;
  }

  if (selectedLineIndex.value < 0) {
    selectedLineIndex.value = 0;
    return;
  }

  selectedLineIndex.value = Math.min(
    returnLines.value.length - 1,
    Math.max(0, selectedLineIndex.value + delta),
  );
};

const loadReturnableContracts = async (queryValue = contractLookupQuery.value) => {
  const requestCounter = ++contractLookupRequestCounter;
  isLoadingContractLookup.value = true;
  contractLookupError.value = "";

  try {
    const records = await fetchReturnableRentalContracts(queryValue, 30);
    if (requestCounter !== contractLookupRequestCounter) {
      return;
    }

    returnableContracts.value = records.map(mapReturnableContract);
  } catch (error) {
    if (requestCounter !== contractLookupRequestCounter) {
      return;
    }

    returnableContracts.value = [];
    if (error instanceof StoryHubApiError) {
      contractLookupError.value = toUiErrorMessage(error.code, error.message);
      return;
    }

    contractLookupError.value =
      "Không thể tải danh sách hợp đồng đang thuê. Vui lòng thử lại.";
  } finally {
    if (requestCounter === contractLookupRequestCounter) {
      isLoadingContractLookup.value = false;
    }
  }
};

const refreshReturnableContracts = async () => {
  await loadReturnableContracts();
};

const selectContractFromLookup = async (contractId: string) => {
  if (isCheckingContract.value || isSettling.value) {
    return;
  }

  contractInput.value = contractId;
  contractInputRef.value?.focus();
  await loadContractPreview();
};

const loadContractPreview = async () => {
  const normalizedId = normalizeContractId(contractInput.value);
  if (normalizedId === null) {
    addNotification("warning", "Mã hợp đồng không hợp lệ. Vui lòng nhập hoặc quét lại.");
    return;
  }

  isCheckingContract.value = true;
  settlementResult.value = null;
  recoverableError.value = null;

  try {
    const contractPreview = mapContractPreview(
      await fetchRentalContractPreview(normalizedId),
    );

    currentContract.value = contractPreview;
    returnLines.value = contractPreview.lines.map((line) => ({
      ...line,
      condition_after: "good",
      scanned: false,
      duplicate: false,
      highlight: false,
    }));
    selectedLineIndex.value = returnLines.value.length > 0 ? 0 : -1;

    if (returnLines.value.length === 0) {
      addNotification(
        "warning",
        `Hợp đồng #${normalizedId} không còn item đang thuê để hoàn trả.`,
      );
      playScanAudio("error");
      return;
    }

    addNotification(
      "success",
      `Đã nạp hợp đồng #${normalizedId}. Có thể quét item hoặc kết toán thủ công.`,
    );
    playScanAudio("success");
  } catch (error) {
    currentContract.value = null;
    returnLines.value = [];
    selectedLineIndex.value = 0;

    if (error instanceof StoryHubApiError) {
      addNotification("error", toUiErrorMessage(error.code, error.message));
    } else {
      addNotification("error", "Không thể tải dữ liệu hợp đồng lúc này. Vui lòng thử lại.");
    }

    playScanAudio("error");
  } finally {
    isCheckingContract.value = false;
  }
};

const markLineHighlight = (line: ReturnLineUi) => {
  line.highlight = true;
  setTimeout(() => {
    line.highlight = false;
  }, 900);
};

const scanReturnItem = (rawCode: string): boolean => {
  const normalizedCode = normalizeScanToken(rawCode);
  if (!normalizedCode) {
    return false;
  }

  clearDuplicateFlags();

  const foundIndex = returnLines.value.findIndex((line) => {
    return (
      normalizeScanToken(line.item_id) === normalizedCode ||
      normalizeScanToken(line.barcode) === normalizedCode
    );
  });

  if (foundIndex === -1) {
    return false;
  }

  const target = returnLines.value[foundIndex];
  selectedLineIndex.value = foundIndex;
  markLineHighlight(target);

  if (target.scanned) {
    target.duplicate = true;
    playScanAudio("error");
    addNotification("warning", "Item đã được quét trước đó. Không ghi nhận trùng.");
    return true;
  }

  target.scanned = true;
  playScanAudio("success");
  addNotification("success", `Đã nhận item trả: ${target.title}`);
  return true;
};

const submitSettlement = async () => {
  if (!currentContract.value) {
    addNotification("warning", "Vui lòng kiểm tra hợp đồng trước khi kết toán.");
    return;
  }

  if (!canSubmitSettlement.value) {
    addNotification("warning", "Không có item nào để kết toán trong hợp đồng này.");
    return;
  }

  isSettling.value = true;
  recoverableError.value = null;
  settlementResult.value = null;

  try {
    const payload = await returnRentalItems(currentContract.value.id, {
      return_lines: settlementLines.value.map((line) => ({
        item_id: line.item_id,
        condition_after: line.condition_after,
      })),
      request_id: buildRequestId("rental-return"),
    });

    settlementResult.value = payload;
    addNotification(
      "success",
      `Kết toán thành công hợp đồng #${payload.contract_id}. Hoàn khách ${formatCurrency(payload.refund_to_customer)}.`,
    );
    void loadReturnableContracts();
  } catch (error) {
    if (error instanceof StoryHubApiError) {
      if (error.code === "NETWORK_ERROR" || error.code === "LOCK_CONFLICT") {
        recoverableError.value = {
          title: "Sự cố kết nối hoặc khóa dữ liệu",
          message:
            "Giữ nguyên phiên hiện tại và thử lại khi backend ổn định hoặc lock đã được giải phóng.",
        };
      }

      addNotification("error", toUiErrorMessage(error.code, error.message));
    } else {
      addNotification("error", "Không thể hoàn tất kết toán lúc này. Vui lòng thử lại.");
    }
  } finally {
    isSettling.value = false;
  }
};

const checkOrSubmit = async () => {
  if (!currentContract.value) {
    await loadContractPreview();
    return;
  }
  await submitSettlement();
};

const retrySettlement = async () => {
  if (isSettling.value) {
    return;
  }
  await submitSettlement();
};

const applyRealtimeSettlementSnapshot = async (contractId: number) => {
  try {
    const snapshot = await fetchRentalSettlementStatus(contractId);
    if (!snapshot.settlement_id) {
      return;
    }

    settlementResult.value = {
      settlement_id: snapshot.settlement_id,
      contract_id: snapshot.contract_id,
      rental_fee: snapshot.rental_fee,
      late_fee: snapshot.late_fee,
      damage_fee: snapshot.damage_fee,
      lost_fee: snapshot.lost_fee,
      total_fee: snapshot.total_fee,
      deducted_from_deposit: snapshot.deducted_from_deposit,
      refund_to_customer: snapshot.refund_to_customer,
      remaining_debt: snapshot.remaining_debt,
      contract_status:
        snapshot.contract_status === "closed" ? "closed" : "partial_returned",
    };
  } catch {
    // Ignore snapshot refresh errors; UI keeps previous values.
  }
};

const handleRealtimeSettlementEvent = (event: RentalSettlementFinishedEvent) => {
  if (!currentContract.value) {
    return;
  }

  const activeContractId = String(currentContract.value.id);
  if (event.contract_id !== activeContractId) {
    return;
  }

  void applyRealtimeSettlementSnapshot(Number(event.contract_id));
  addNotification(
    "success",
    `Settlement đã được cập nhật realtime cho HĐ #${event.contract_id}.`,
  );
};

const handleRealtimeItemStatus = (event: ItemStatusChangedEvent) => {
  if (!currentContract.value) {
    return;
  }

  const normalizedEventItem = normalizeScanToken(event.item_id);
  if (!normalizedEventItem) {
    return;
  }

  const line = returnLines.value.find((candidate) => {
    return (
      normalizeScanToken(candidate.item_id) === normalizedEventItem ||
      normalizeScanToken(candidate.barcode) === normalizedEventItem
    );
  });

  if (!line) {
    return;
  }

  const nextStatus = event.new_status.toLowerCase();
  if (nextStatus !== "available" && nextStatus !== "lost") {
    return;
  }

  line.scanned = true;
  line.duplicate = false;
  if (nextStatus === "lost") {
    line.condition_after = "lost";
  }
  markLineHighlight(line);
};

const resetWorkflow = () => {
  contractInput.value = "";
  currentContract.value = null;
  returnLines.value = [];
  selectedLineIndex.value = 0;
  recoverableError.value = null;
  settlementResult.value = null;
  scannerToast.value.message = "";
  inputHighlight.value = false;
  addNotification("info", "Đã hủy phiên hoàn trả hiện tại.");
};

const handleScannerScan = (event: Event) => {
  const customEvent = event as CustomEvent<ScannerScanEventDetail>;
  const rawCode = customEvent.detail?.code?.trim() ?? "";
  if (!rawCode) {
    return;
  }

  flashInputHighlight();

  if (!currentContract.value) {
    contractInput.value = rawCode;
    flashScannerToast(`Đã quét hợp đồng: ${rawCode}`, "success");
    void loadContractPreview();
    return;
  }

  const matched = scanReturnItem(rawCode);
  if (matched) {
    flashScannerToast(`Đã quét item: ${rawCode}`, "success");
    return;
  }

  playScanAudio("error");
  addNotification("error", "Item quét không thuộc hợp đồng hiện tại.");
  flashScannerToast(`Từ chối item: ${rawCode}`, "warning");
};

const handleGlobalHotkey = (event: Event) => {
  const customEvent = event as CustomEvent<HotkeyEventDetail>;
  const hotkey = customEvent.detail?.name;

  if (hotkey === "escape") {
    resetWorkflow();
    return;
  }

  if (hotkey === "f1" || hotkey === "enter") {
    void checkOrSubmit();
    return;
  }

  if (hotkey === "f2") {
    contractInputRef.value?.focus();
    return;
  }

  if (hotkey === "arrow-up") {
    moveSelectedLine(-1);
    return;
  }

  if (hotkey === "arrow-down") {
    moveSelectedLine(1);
    return;
  }

  if (
    hotkey === "digit-1" ||
    hotkey === "digit-2" ||
    hotkey === "digit-3" ||
    hotkey === "digit-4"
  ) {
    setConditionFromHotkey(hotkey);
  }
};

onMounted(() => {
  ws.connect("cashier-demo", "main");
  ws.subscribe(["item_status_changed", "rental_settlement_finished"]);
  stopRealtimeItemWatch = watch(
    () => ws.latestItemStatusEvent.value,
    (event) => {
      if (!event) {
        return;
      }
      handleRealtimeItemStatus(event);
    },
    { immediate: true },
  );
  stopRealtimeSettlementWatch = watch(
    () => ws.latestSettlementEvent.value,
    (event) => {
      if (!event) {
        return;
      }
      handleRealtimeSettlementEvent(event);
    },
    { immediate: true },
  );

  window.addEventListener("storyhub:scan", handleScannerScan as EventListener);
  window.addEventListener("storyhub:hotkey", handleGlobalHotkey as EventListener);
  void loadReturnableContracts();

  const scannedContract = String(route.query.scan ?? "").trim();
  if (scannedContract) {
    contractInput.value = scannedContract;
    void loadContractPreview();
  }
});

onBeforeUnmount(() => {
  ws.unsubscribe(["item_status_changed", "rental_settlement_finished"]);
  ws.setTrackedItems([]);
  ws.setTrackedContracts([]);

  if (stopRealtimeItemWatch) {
    stopRealtimeItemWatch();
    stopRealtimeItemWatch = null;
  }

  if (stopRealtimeSettlementWatch) {
    stopRealtimeSettlementWatch();
    stopRealtimeSettlementWatch = null;
  }

  window.removeEventListener("storyhub:scan", handleScannerScan as EventListener);
  window.removeEventListener("storyhub:hotkey", handleGlobalHotkey as EventListener);

  if (scannerToastTimer) {
    clearTimeout(scannerToastTimer);
    scannerToastTimer = null;
  }

  if (inputHighlightTimer) {
    clearTimeout(inputHighlightTimer);
    inputHighlightTimer = null;
  }

  if (summaryFlashTimer) {
    clearTimeout(summaryFlashTimer);
    summaryFlashTimer = null;
  }

  if (contractLookupDebounceTimer) {
    clearTimeout(contractLookupDebounceTimer);
    contractLookupDebounceTimer = null;
  }
});

watch(contractLookupQuery, (nextValue) => {
  if (contractLookupDebounceTimer) {
    clearTimeout(contractLookupDebounceTimer);
  }

  contractLookupDebounceTimer = setTimeout(() => {
    void loadReturnableContracts(nextValue);
    contractLookupDebounceTimer = null;
  }, 280);
});

watch(
  () => returnLines.value.map((line) => line.item_id),
  (itemIds) => {
    ws.setTrackedItems(itemIds);
  },
  { immediate: true },
);

watch(
  () => currentContract.value?.id ?? null,
  (contractId) => {
    if (!contractId) {
      ws.setTrackedContracts([]);
      return;
    }
    ws.setTrackedContracts([contractId]);
  },
  { immediate: true },
);

watch(
  () => summary.value.total_fee,
  (next, prev) => {
    if (prev === undefined || next === prev) {
      return;
    }

    summaryFlashClass.value = next > prev ? "flash-neg" : "flash-pos";
    if (summaryFlashTimer) {
      clearTimeout(summaryFlashTimer);
    }
    summaryFlashTimer = setTimeout(() => {
      summaryFlashClass.value = "";
      summaryFlashTimer = null;
    }, 480);
  },
);
</script>

<style scoped>
@import url("https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap");

.return-container {
  padding: 32px;
  background: #fdfdfd;
  min-height: 100vh;
  font-family: "Plus Jakarta Sans", sans-serif;
}

.header-section {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  margin-bottom: 24px;
}

.page-title {
  font-size: 2.2rem;
  font-weight: 800;
  letter-spacing: -0.04em;
  color: #0f172a;
  margin: 0;
}

.subtitle {
  margin: 4px 0 0;
  color: #64748b;
}

.state-pill {
  border-radius: 999px;
  border: 1px solid #cbd5e1;
  background: #f8fafc;
  color: #334155;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  font-size: 0.8rem;
  font-weight: 800;
  text-transform: uppercase;
}

.state-pill.success {
  background: #ecfdf3;
  border-color: #bbf7d0;
  color: #166534;
}

.state-pill.loading,
.state-pill.settling {
  background: #eff6ff;
  border-color: #bfdbfe;
  color: #1d4ed8;
}

.state-pill.error {
  background: #fef2f2;
  border-color: #fecaca;
  color: #991b1b;
}

.retry-banner,
.scanner-toast {
  border-radius: 14px;
  padding: 10px 12px;
  border: 1px solid;
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 14px;
}

.retry-banner {
  border-color: #fecaca;
  background: #fff1f2;
  color: #9f1239;
}

.retry-banner .copy {
  display: flex;
  flex-direction: column;
  gap: 2px;
  flex: 1;
}

.btn-retry {
  border: none;
  border-radius: 10px;
  padding: 8px 12px;
  background: #0f172a;
  color: white;
  font-weight: 700;
  cursor: pointer;
}

.scanner-toast {
  border-color: #bfdbfe;
  background: #eff6ff;
  color: #1d4ed8;
  font-weight: 700;
}

.scanner-toast.success {
  border-color: #86efac;
  background: #ecfdf3;
  color: #166534;
}

.scanner-toast.warning {
  border-color: #fde68a;
  background: #fffbeb;
  color: #92400e;
}

.scanner-toast.error {
  border-color: #fecaca;
  background: #fff1f2;
  color: #991b1b;
}

.return-grid-layout {
  display: grid;
  grid-template-columns: 1fr 380px;
  gap: 24px;
  align-items: start;
}

.card-glass {
  border-radius: 28px;
  border: 1px solid #f1f5f9;
  background: white;
  padding: 26px;
  box-shadow: 0 20px 30px -20px rgba(15, 23, 42, 0.24);
}

.sticky-panel {
  position: sticky;
  top: 24px;
}

.card-header-lux {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.card-header-lux h3 {
  margin: 0;
  color: #1e293b;
  font-size: 1.2rem;
  font-weight: 800;
  display: inline-flex;
  align-items: center;
  gap: 10px;
}

.hotkey-hint {
  margin: 0;
  font-size: 0.8rem;
  color: #475569;
  border: 1px solid #e2e8f0;
  background: #f8fafc;
  border-radius: 10px;
  padding: 8px 10px;
}

.hotkey-hint kbd {
  border-radius: 6px;
  border: 1px solid #cbd5e1;
  background: white;
  color: #1e293b;
  padding: 2px 6px;
  font-weight: 800;
}

.contract-search-wrap {
  display: flex;
  gap: 10px;
  align-items: center;
  border: 1.5px solid #e2e8f0;
  border-radius: 16px;
  padding: 10px 12px;
  transition: 0.2s;
}

.contract-search-wrap.scan-highlight {
  border-color: #16a34a;
  box-shadow: 0 0 0 3px rgba(22, 163, 74, 0.2);
}

.contract-search-wrap input {
  border: none;
  outline: none;
  flex: 1;
  font-family: inherit;
  font-size: 0.92rem;
  font-weight: 600;
}

.contract-guidance {
  margin: 8px 0 0;
  color: #64748b;
  font-size: 0.82rem;
  font-weight: 600;
}

.contract-lookup-panel {
  margin-top: 14px;
  border: 1px solid #dbeafe;
  background: linear-gradient(180deg, #f8fbff 0%, #ffffff 100%);
  border-radius: 14px;
  padding: 12px;
}

.contract-lookup-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.contract-lookup-header strong {
  color: #1e293b;
  font-size: 0.9rem;
}

.lookup-refresh-btn {
  border: 1px solid #bfdbfe;
  background: #eff6ff;
  color: #1d4ed8;
  border-radius: 8px;
  padding: 6px 10px;
  font-size: 0.76rem;
  font-weight: 700;
  cursor: pointer;
}

.lookup-refresh-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.contract-lookup-search {
  margin-top: 10px;
  border: 1px solid #dbeafe;
  background: white;
  border-radius: 10px;
  padding: 8px 10px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.contract-lookup-search .material-icons {
  font-size: 1rem;
  color: #64748b;
}

.contract-lookup-search input {
  border: none;
  outline: none;
  width: 100%;
  font-size: 0.84rem;
  font-family: inherit;
  font-weight: 600;
  color: #0f172a;
}

.contract-lookup-filters {
  margin-top: 8px;
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.lookup-filter-btn {
  border: 1px solid #cbd5e1;
  background: white;
  color: #475569;
  border-radius: 999px;
  padding: 4px 10px;
  font-size: 0.74rem;
  font-weight: 700;
  cursor: pointer;
}

.lookup-filter-btn.active {
  border-color: #2563eb;
  background: #eff6ff;
  color: #1d4ed8;
}

.lookup-loading,
.lookup-error,
.lookup-empty {
  margin-top: 10px;
  border-radius: 10px;
  padding: 8px 10px;
  font-size: 0.8rem;
  font-weight: 600;
}

.lookup-loading {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  border: 1px solid #bfdbfe;
  color: #1d4ed8;
  background: #eff6ff;
}

.lookup-error {
  border: 1px solid #fecaca;
  color: #991b1b;
  background: #fff1f2;
}

.lookup-empty {
  border: 1px dashed #cbd5e1;
  color: #64748b;
  background: #f8fafc;
  margin-bottom: 0;
}

.contract-lookup-list {
  list-style: none;
  margin: 10px 0 0;
  padding: 0;
  max-height: 220px;
  overflow: auto;
  display: grid;
  gap: 8px;
}

.contract-lookup-item {
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  background: white;
}

.contract-lookup-item.active {
  border-color: #60a5fa;
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.15);
}

.contract-lookup-button {
  width: 100%;
  border: none;
  background: transparent;
  text-align: left;
  cursor: pointer;
  padding: 10px;
  display: grid;
  gap: 6px;
}

.contract-lookup-button:disabled {
  cursor: not-allowed;
  opacity: 0.8;
}

.lookup-top-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  color: #0f172a;
}

.lookup-bottom-row {
  display: grid;
  gap: 2px;
  color: #475569;
  font-size: 0.76rem;
  font-weight: 600;
}

.lookup-status-chip {
  border-radius: 999px;
  padding: 4px 8px;
  font-size: 0.7rem;
  font-weight: 800;
  border: 1px solid transparent;
}

.lookup-status-chip.status-active {
  background: #dcfce7;
  color: #166534;
  border-color: #86efac;
}

.lookup-status-chip.status-partial {
  background: #fef3c7;
  color: #92400e;
  border-color: #fcd34d;
}

.lookup-status-chip.status-overdue {
  background: #fee2e2;
  color: #991b1b;
  border-color: #fca5a5;
}

.btn-action {
  border: none;
  border-radius: 10px;
  background: #2563eb;
  color: white;
  font-weight: 800;
  padding: 10px 14px;
  cursor: pointer;
}

.btn-action:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.inline-loading {
  margin-top: 12px;
  border-radius: 10px;
  border: 1px solid #bfdbfe;
  background: #eff6ff;
  color: #1d4ed8;
  padding: 10px 12px;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-weight: 700;
}

.contract-meta-grid {
  margin-top: 14px;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.meta-item {
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  background: #f8fafc;
  padding: 10px 12px;
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.meta-item .lbl {
  font-size: 0.72rem;
  text-transform: uppercase;
  color: #64748b;
  font-weight: 700;
}

.line-table-wrap {
  margin-top: 16px;
}

table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0 10px;
}

th {
  text-align: left;
  font-size: 0.74rem;
  color: #64748b;
  text-transform: uppercase;
  font-weight: 800;
  padding: 0 10px;
}

td {
  background: #f8fafc;
  border-top: 1px solid #e2e8f0;
  border-bottom: 1px solid #e2e8f0;
  padding: 12px 10px;
  vertical-align: top;
}

td:first-child {
  border-left: 1px solid #e2e8f0;
  border-radius: 12px 0 0 12px;
}

td:last-child {
  border-right: 1px solid #e2e8f0;
  border-radius: 0 12px 12px 0;
}

tbody tr.active td {
  border-color: #93c5fd;
  background: #eff6ff;
}

tbody tr.scan-highlight td {
  border-color: #16a34a;
  background: #ecfdf3;
}

tbody tr.duplicate td {
  border-color: #fb923c;
  background: #fff7ed;
}

.line-title-block {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.line-title-block .code {
  font-size: 0.75rem;
  color: #64748b;
}

.scan-state {
  border-radius: 999px;
  padding: 4px 8px;
  font-size: 0.75rem;
  font-weight: 800;
}

.scan-state.pending {
  background: #e2e8f0;
  color: #475569;
}

.scan-state.ok {
  background: #dcfce7;
  color: #166534;
}

.scan-state.manual {
  background: #fef3c7;
  color: #92400e;
}

.condition-chip-group {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.condition-chip {
  border: 1px solid #cbd5e1;
  border-radius: 999px;
  background: white;
  padding: 5px 9px;
  font-size: 0.73rem;
  font-weight: 700;
  color: #334155;
  cursor: pointer;
}

.condition-chip.active.good {
  border-color: #22c55e;
  background: #dcfce7;
  color: #166534;
}

.condition-chip.active.minor {
  border-color: #f59e0b;
  background: #fef3c7;
  color: #92400e;
}

.condition-chip.active.major {
  border-color: #f97316;
  background: #ffedd5;
  color: #9a3412;
}

.condition-chip.active.lost {
  border-color: #ef4444;
  background: #fee2e2;
  color: #991b1b;
}

.empty-state,
.empty-row {
  text-align: center;
  color: #94a3b8;
}

.empty-state {
  border: 1px dashed #cbd5e1;
  border-radius: 14px;
  padding: 20px;
  margin-top: 16px;
}

.empty-state .material-icons {
  font-size: 2rem;
  margin-bottom: 6px;
}

.quick-preset-row {
  margin-top: 14px;
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.btn-preset {
  border: none;
  border-radius: 10px;
  padding: 9px 12px;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-weight: 800;
  cursor: pointer;
}

.btn-preset.good {
  background: #dcfce7;
  color: #166534;
}

.btn-preset.lost {
  background: #fee2e2;
  color: #991b1b;
}

.summary-box {
  border-radius: 16px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  padding: 14px;
}

.summary-box .line {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 7px 0;
  color: #334155;
  font-size: 0.9rem;
}

.summary-box .line.total {
  color: #0f172a;
  font-weight: 800;
}

.summary-box .line.success strong {
  color: #166534;
}

.summary-box .line.warning strong {
  color: #9a3412;
}

.summary-box .line.flash-pos {
  animation: summaryFlashPositive 0.45s ease;
}

.summary-box .line.flash-neg {
  animation: summaryFlashNegative 0.45s ease;
}

.divider {
  border-top: 1px dashed #cbd5e1;
  margin: 8px 0;
}

.condition-hotkey {
  margin-top: 12px;
}

.btn-settle {
  margin-top: 12px;
  width: 100%;
  border: none;
  border-radius: 14px;
  background: #16a34a;
  color: white;
  font-weight: 800;
  padding: 14px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  cursor: pointer;
}

.btn-settle:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.btn-reset {
  margin-top: 10px;
  width: 100%;
  border: none;
  border-radius: 12px;
  background: transparent;
  color: #64748b;
  font-weight: 700;
  padding: 10px;
  cursor: pointer;
}

.btn-reset:hover {
  color: #b91c1c;
}

.overlay-loading {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.35);
  display: grid;
  place-items: center;
  z-index: 44;
}

.overlay-card {
  border-radius: 16px;
  border: 1px solid #cbd5e1;
  background: white;
  padding: 18px 20px;
  color: #1e293b;
  font-weight: 700;
  display: flex;
  align-items: center;
  gap: 10px;
}

.spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

@keyframes summaryFlashPositive {
  0% {
    background: #ecfdf3;
  }
  100% {
    background: transparent;
  }
}

@keyframes summaryFlashNegative {
  0% {
    background: #fff1f2;
  }
  100% {
    background: transparent;
  }
}

@media (max-width: 1200px) {
  .return-grid-layout {
    grid-template-columns: 1fr;
  }

  .sticky-panel {
    position: static;
  }
}
</style>
