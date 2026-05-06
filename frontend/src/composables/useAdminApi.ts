import { computed } from 'vue';
import { useAuthStore } from '../stores/auth';
import {
  applyBulkPriceUpdate,
  buildRequestId,
  createAutoPromotion,
  createSystemBackup,
  createSystemUser,
  createVoucher,
  deleteAutoPromotion,
  deleteVoucher,
  emergencyRefundRentalContract,
  emergencyRefundSaleOrder,
  fetchActivePricingRule,
  fetchAdminTransactions,
  fetchAllCustomersAdmin,
  fetchAuditLogs,
  fetchAutoPromotions,
  fetchLatestSystemBackup,
  fetchSystemConfig,
  fetchSystemUsers,
  fetchVouchers,
  hardDeleteAdminTransaction,
  StoryHubApiError,
  updateActivePricingRule,
  updateAutoPromotion,
  updateSystemConfig,
  updateSystemUser,
  updateVoucher,
  adminOverrideCustomer,
  upsertCustomer,
  fetchPromotionEvents,
  createPromotionEvent,
  updatePromotionEvent,
  deletePromotionEvent,
  fetchPromotionItems,
  addPromotionItem,
  removePromotionItem,
  fetchCustomerSpendingStats,
} from '../services/storyhubApi';
import type {
  AdminCustomerOverrideRequest,
  AutoPromoItem,
  AuditLogItem,
  ActivePriceRulePayload,
  AdminTransactionItem,
  BulkPriceUpdatePayload,
  CustomerListItem,
  EmergencyRefundRentalContractPayload,
  EmergencyRefundSaleOrderPayload,
  LatestBackupPayload,
  SystemUser,
  UpdateActivePriceRuleRequest,
  VoucherCreate,
  VoucherItem,
  PromotionEvent,
  PromotionItem,
  CustomerSpendingItem,
} from '../services/storyhubApi';

type TransactionKind = 'all' | 'sale' | 'rental';
type RefundMethod = 'cash' | 'bank_transfer' | 'e_wallet' | 'original_method';

type UserCreatePayload = {
  username: string;
  password: string;
  full_name?: string;
  role: 'cashier' | 'manager';
};

type UserUpdatePayload = {
  is_active?: boolean;
  full_name?: string;
  role?: 'cashier' | 'manager';
  new_password?: string;
};

type VoucherUpdatePayload = {
  is_active?: boolean;
  value?: number;
  min_spend?: number;
  max_discount?: number | null;
  max_uses?: number | null;
  end_at?: string | null;
};

type AutoPromoCreatePayload = {
  name: string;
  day_of_week: number;
  discount_percent: number;
};

type AutoPromoUpdatePayload = {
  name?: string;
  day_of_week?: number;
  discount_percent?: number;
  is_active?: boolean;
};

export function useAdminApi() {
  const authStore = useAuthStore();

  const ownerToken = computed(() => {
    if (!authStore.token || !authStore.user) {
      throw new StoryHubApiError({
        code: 'AUTH_REQUIRED',
        message: 'Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.',
        status: 401,
      });
    }

    if (authStore.user.role !== 'owner') {
      throw new StoryHubApiError({
        code: 'FORBIDDEN',
        message: 'Khu vực /quan-ly chi danh cho owner.',
        status: 403,
      });
    }

    return authStore.token;
  });

  const token = () => ownerToken.value;

  return {
    fetchCustomers(q?: string, blacklistedOnly?: boolean): Promise<CustomerListItem[]> {
      return fetchAllCustomersAdmin(token(), q, blacklistedOnly);
    },

    overrideCustomer(customerId: number, payload: AdminCustomerOverrideRequest) {
      return adminOverrideCustomer(customerId, payload, token());
    },

    upsertCustomer(phone: string, payload: any) {
      return upsertCustomer(phone, payload, token());
    },

    fetchTransactions(params?: {
      q?: string;
      kind?: TransactionKind;
      limit?: number;
      offset?: number;
    }): Promise<AdminTransactionItem[]> {
      return fetchAdminTransactions(token(), params);
    },

    hardDeleteTransaction(transactionType: 'sale' | 'rental', referenceId: string | number, reason: string) {
      return hardDeleteAdminTransaction(
        transactionType,
        referenceId,
        { reason },
        token(),
      );
    },

    emergencyRefundSale(
      orderId: number,
      reason: string,
      refundMethod: RefundMethod = 'original_method',
      requestId = buildRequestId('admin-sale-refund'),
    ): Promise<EmergencyRefundSaleOrderPayload> {
      return emergencyRefundSaleOrder(
        orderId,
        {
          reason,
          refund_method: refundMethod,
          request_id: requestId,
        },
        token(),
      );
    },

    emergencyRefundRental(
      contractId: number,
      reason: string,
      refundMethod: RefundMethod = 'original_method',
      requestId = buildRequestId('admin-rental-refund'),
    ): Promise<EmergencyRefundRentalContractPayload> {
      return emergencyRefundRentalContract(
        contractId,
        {
          reason,
          refund_method: refundMethod,
          request_id: requestId,
        },
        token(),
      );
    },

    fetchAuditLogs(params?: { limit?: number; offset?: number; action?: string }): Promise<AuditLogItem[]> {
      return fetchAuditLogs(token(), params);
    },

    fetchVouchers(): Promise<VoucherItem[]> {
      return fetchVouchers(token());
    },

    createVoucher(payload: VoucherCreate) {
      return createVoucher(payload, token());
    },

    updateVoucher(id: number, payload: VoucherUpdatePayload) {
      return updateVoucher(id, payload, token());
    },

    deleteVoucher(id: number) {
      return deleteVoucher(id, token());
    },

    fetchAutoPromotions(): Promise<AutoPromoItem[]> {
      return fetchAutoPromotions(token());
    },

    createAutoPromotion(payload: AutoPromoCreatePayload) {
      return createAutoPromotion(payload, token());
    },

    updateAutoPromotion(id: number, payload: AutoPromoUpdatePayload) {
      return updateAutoPromotion(id, payload, token());
    },

    deleteAutoPromotion(id: number) {
      return deleteAutoPromotion(id, token());
    },

    fetchSystemUsers(): Promise<SystemUser[]> {
      return fetchSystemUsers(token());
    },

    createSystemUser(payload: UserCreatePayload) {
      return createSystemUser(payload, token());
    },

    updateSystemUser(userId: number, payload: UserUpdatePayload) {
      return updateSystemUser(userId, payload, token());
    },

    fetchActivePricingRule(): Promise<ActivePriceRulePayload> {
      return fetchActivePricingRule(token());
    },

    updateActivePricingRule(payload: UpdateActivePriceRuleRequest): Promise<ActivePriceRulePayload> {
      return updateActivePricingRule(payload, token());
    },

    applyBulkPriceUpdate(percentDelta: number, reason: string): Promise<BulkPriceUpdatePayload> {
      return applyBulkPriceUpdate(
        {
          percent_delta: percentDelta,
          reason,
        },
        token(),
      );
    },

    fetchSystemConfig(): Promise<Record<string, string>> {
      return fetchSystemConfig(token());
    },

    updateSystemConfig(configs: Record<string, string>): Promise<Record<string, string>> {
      return updateSystemConfig(configs, token());
    },

    fetchLatestBackup(): Promise<LatestBackupPayload> {
      return fetchLatestSystemBackup(token());
    },

    triggerBackup() {
      return createSystemBackup(
        {
          backup_type: 'full',
          include_media: true,
          request_id: buildRequestId('admin-backup'),
        },
        token(),
      );
    },

    fetchPromotionEvents(): Promise<PromotionEvent[]> {
      return fetchPromotionEvents(token());
    },

    createPromotionEvent(payload: Partial<PromotionEvent>) {
      return createPromotionEvent(payload, token());
    },

    updatePromotionEvent(promoId: number, payload: Partial<PromotionEvent>) {
      return updatePromotionEvent(promoId, payload, token());
    },

    deletePromotionEvent(promoId: number) {
      return deletePromotionEvent(promoId, token());
    },

    fetchPromotionItems(promoId: number): Promise<PromotionItem[]> {
      return fetchPromotionItems(promoId, token());
    },

    addPromotionItem(promoId: number, targetType: 'title' | 'volume', targetId: number) {
      return addPromotionItem(promoId, { target_type: targetType, target_id: targetId }, token());
    },

    removePromotionItem(promoId: number, itemId: number) {
      return removePromotionItem(promoId, itemId, token());
    },

    fetchCustomerSpendingStats(): Promise<CustomerSpendingItem[]> {
      return fetchCustomerSpendingStats(token());
    },
  };
}
