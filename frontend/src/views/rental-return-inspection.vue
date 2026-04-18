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
        <div v-if="scannerToast" class="scanner-toast">
          <span class="material-icons">qr_code_scanner</span>
          {{ scannerToast }}
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
                    <span :class="['scan-state', line.scanned ? 'ok' : 'pending']">
                      {{ line.scanned ? "Đã quét" : "Chờ quét" }}
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
            <div class="line">
              <span>Phí thuê</span>
              <strong>{{ formatCurrency(summary.rental_fee) }}</strong>
            </div>
            <div class="line">
              <span>Phí trễ hạn</span>
              <strong>{{ formatCurrency(summary.late_fee) }}</strong>
            </div>
            <div class="line">
              <span>Phí hư hỏng</span>
              <strong>{{ formatCurrency(summary.damage_fee) }}</strong>
            </div>
            <div class="line">
              <span>Phí mất</span>
              <strong>{{ formatCurrency(summary.lost_fee) }}</strong>
            </div>

            <div class="divider"></div>

            <div class="line total">
              <span>Tổng phí</span>
              <strong>{{ formatCurrency(summary.total_fee) }}</strong>
            </div>
            <div class="line">
              <span>Trừ vào cọc</span>
              <strong>{{ formatCurrency(summary.deducted_from_deposit) }}</strong>
            </div>
            <div class="line success">
              <span>Hoàn khách</span>
              <strong>{{ formatCurrency(summary.refund_to_customer) }}</strong>
            </div>
            <div class="line warning">
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
import { computed, inject, onBeforeUnmount, onMounted, ref } from "vue";

import DefaultLayout from "../components/layout/defaultLayout.vue";
import {
  fetchRentalContractPreview,
  StoryHubApiError,
  buildRequestId,
  returnRentalItems,
  type RentalContractPreviewPayload,
  type RentalReturnCondition,
  type ReturnRentalItemsPayload,
} from "../services/storyhubApi";
import { toUiErrorMessage } from "../utils/backendErrorMessages";
import { playScanAudio } from "../utils/scanAudio";

interface ScannerScanEventDetail {
  code?: string;
}

interface HotkeyEventDetail {
  name?: "f1" | "escape" | "enter" | "digit-1" | "digit-2" | "digit-3" | "digit-4";
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

const addNotification = inject("addNotification") as (
  type: string,
  msg: string,
) => void;

const contractInput = ref("");
const currentContract = ref<ContractPreviewUi | null>(null);
const returnLines = ref<ReturnLineUi[]>([]);
const selectedLineIndex = ref(0);
const isCheckingContract = ref(false);
const isSettling = ref(false);
const settlementResult = ref<ReturnRentalItemsPayload | null>(null);
const recoverableError = ref<RecoverableError | null>(null);
const scannerToast = ref("");
const inputHighlight = ref(false);

let scannerToastTimer: ReturnType<typeof setTimeout> | null = null;
let inputHighlightTimer: ReturnType<typeof setTimeout> | null = null;

const scannedLines = computed(() => returnLines.value.filter((line) => line.scanned));

const canSubmitSettlement = computed(
  () => currentContract.value !== null && scannedLines.value.length > 0,
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

  const rentalFee = scannedLines.value.reduce((sum, line) => sum + line.rental_fee, 0);
  const lateFee = scannedLines.value.reduce(
    (sum, line) => sum + line.overdue_days * contract.overdueFeePerDay,
    0,
  );
  const damageFee = scannedLines.value
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
  const lostFee = scannedLines.value
    .filter((line) => line.condition_after === "lost")
    .reduce((sum, line) => sum + line.final_deposit, 0);

  const totalFee = rentalFee + lateFee + damageFee + lostFee;
  const hasScannedLine = scannedLines.value.length > 0;
  const deductedFromDeposit = hasScannedLine
    ? Math.min(totalFee, contract.deposit)
    : 0;
  const refundToCustomer = hasScannedLine
    ? Math.max(contract.deposit - totalFee, 0)
    : 0;
  const remainingDebt = hasScannedLine
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

const normalizeScanToken = (rawValue: string) =>
  rawValue.replace(/[^A-Za-z0-9]/g, "").toUpperCase();

const flashScannerToast = (message: string) => {
  scannerToast.value = message;
  if (scannerToastTimer) {
    clearTimeout(scannerToastTimer);
  }
  scannerToastTimer = setTimeout(() => {
    scannerToast.value = "";
    scannerToastTimer = null;
  }, 1000);
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
      `Đã nạp hợp đồng #${normalizedId}. Bắt đầu quét item trả.`,
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
    addNotification("warning", "Cần quét ít nhất một item trước khi kết toán.");
    return;
  }

  isSettling.value = true;
  recoverableError.value = null;
  settlementResult.value = null;

  try {
    const payload = await returnRentalItems(currentContract.value.id, {
      return_lines: scannedLines.value.map((line) => ({
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

const resetWorkflow = () => {
  contractInput.value = "";
  currentContract.value = null;
  returnLines.value = [];
  selectedLineIndex.value = 0;
  recoverableError.value = null;
  settlementResult.value = null;
  scannerToast.value = "";
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
    flashScannerToast(`Đã quét hợp đồng: ${rawCode}`);
    void loadContractPreview();
    return;
  }

  const matched = scanReturnItem(rawCode);
  if (matched) {
    flashScannerToast(`Đã quét item: ${rawCode}`);
    return;
  }

  playScanAudio("error");
  addNotification("error", "Item quét không thuộc hợp đồng hiện tại.");
  flashScannerToast(`Từ chối item: ${rawCode}`);
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
  window.addEventListener("storyhub:scan", handleScannerScan as EventListener);
  window.addEventListener("storyhub:hotkey", handleGlobalHotkey as EventListener);
});

onBeforeUnmount(() => {
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
});
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

@media (max-width: 1200px) {
  .return-grid-layout {
    grid-template-columns: 1fr;
  }

  .sticky-panel {
    position: static;
  }
}
</style>
