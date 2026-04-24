import { watch, type Ref } from "vue";
import type { InventoryItemListItem } from "../services/storyhubApi";

const STORAGE_KEY = "storyhub_checkout_draft";

export interface CheckoutDraft {
  cart: InventoryItemListItem[];
  customerNameInput: string;
  customerPhoneInput: string;
  customerAddressInput: string;
  selectedCustomerId: number | null;
  rentalDays: number;
  paymentMethod: "cash" | "transfer";
  isSplitPayment: boolean;
  cashAmount: number;
  transferAmount: number;
}

export function useCheckoutPersistence(state: {
  cart: Ref<InventoryItemListItem[]>;
  customerNameInput: Ref<string>;
  customerPhoneInput: Ref<string>;
  customerAddressInput: Ref<string>;
  selectedCustomerId: Ref<number | null>;
  rentalDays: Ref<number>;
  paymentMethod: Ref<"cash" | "transfer">;
  isSplitPayment: Ref<boolean>;
  cashAmount: Ref<number>;
  transferAmount: Ref<number>;
}) {
  const saveDraft = () => {
    const draft: CheckoutDraft = {
      cart: state.cart.value,
      customerNameInput: state.customerNameInput.value,
      customerPhoneInput: state.customerPhoneInput.value,
      customerAddressInput: state.customerAddressInput.value,
      selectedCustomerId: state.selectedCustomerId.value,
      rentalDays: state.rentalDays.value,
      paymentMethod: state.paymentMethod.value,
      isSplitPayment: state.isSplitPayment.value,
      cashAmount: state.cashAmount.value,
      transferAmount: state.transferAmount.value,
    };
    localStorage.setItem(STORAGE_KEY, JSON.stringify(draft));
  };

  const loadDraft = () => {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (!saved) return false;

    try {
      const draft: CheckoutDraft = JSON.parse(saved);
      state.cart.value = draft.cart || [];
      state.customerNameInput.value = draft.customerNameInput || "";
      state.customerPhoneInput.value = draft.customerPhoneInput || "";
      state.customerAddressInput.value = draft.customerAddressInput || "";
      state.selectedCustomerId.value = draft.selectedCustomerId;
      state.rentalDays.value = draft.rentalDays || 3;
      state.paymentMethod.value = draft.paymentMethod || "cash";
      state.isSplitPayment.value = !!draft.isSplitPayment;
      state.cashAmount.value = draft.cashAmount || 0;
      state.transferAmount.value = draft.transferAmount || 0;
      return true;
    } catch (e) {
      console.error("Failed to load checkout draft", e);
      return false;
    }
  };

  const clearDraft = () => {
    localStorage.removeItem(STORAGE_KEY);
  };

  // Watch for deep changes
  watch(
    [
      state.cart,
      state.customerNameInput,
      state.customerPhoneInput,
      state.customerAddressInput,
      state.selectedCustomerId,
      state.rentalDays,
      state.paymentMethod,
      state.isSplitPayment,
      state.cashAmount,
      state.transferAmount,
    ],
    () => {
      saveDraft();
    },
    { deep: true }
  );

  return {
    loadDraft,
    clearDraft,
  };
}
