import { defineStore } from 'pinia';
import { ref } from 'vue';
import router from '../router';
import { fetchInventoryItems, checkItemRentalStatus, type InventoryItemListItem } from '../services/storyhubApi';

export const useScannerStore = defineStore('scanner', () => {
  const isProcessing = ref(false);
  const lastScannedCode = ref('');
  const lastScannedItem = ref<InventoryItemListItem | null>(null);
  const pendingCheckoutItems = ref<InventoryItemListItem[]>([]);
  
  // Signal for views to react
  const scanEventCounter = ref(0);

  const normalize = (val: string) => val.replace(/[^A-Za-z0-9]/g, "").toUpperCase();

  function queuePendingCheckoutItem(item: InventoryItemListItem) {
    pendingCheckoutItems.value = [...pendingCheckoutItems.value, { ...item }];
  }

  function consumePendingCheckoutItems(): InventoryItemListItem[] {
    if (pendingCheckoutItems.value.length === 0) {
      return [];
    }

    const queuedItems = pendingCheckoutItems.value.map((item) => ({ ...item }));
    pendingCheckoutItems.value = [];
    return queuedItems;
  }

  async function processGlobalScan(code: string) {
    if (isProcessing.value) return;
    
    // Skip global processing if on the Return page to allow local specialized scanning
    if (router.currentRoute.value.path === '/hoan-tra') return;

    isProcessing.value = true;
    lastScannedCode.value = code;
    
    try {
      // On dashboard: check if item is currently rented
      if (router.currentRoute.value.path === '/') {
        try {
          const rentalStatus = await checkItemRentalStatus(code);
          if (rentalStatus.rental_contract_id) {
            // Item is currently rented, go to return page with contract
            await router.push({ 
              path: '/hoan-tra', 
              query: { scan: rentalStatus.rental_contract_id } 
            });
            return;
          }
          // Item is not rented, continue to checkout/inventory logic below
        } catch {
          // Error checking rental status, continue to search by inventory
        }
      }

      // Search inventory for the code (for checkout or new rental)
      const results = await fetchInventoryItems(code);
      
      // Match exactly by code or ID using normalized comparison
      const normalizedCode = normalize(code);
      
      const exactMatch = results.find(item => 
        normalize(item.code) === normalizedCode || 
        normalize(item.id) === normalizedCode
      );

      if (exactMatch) {
        lastScannedItem.value = exactMatch;
        queuePendingCheckoutItem(exactMatch);
        scanEventCounter.value++;
        
        // Found -> Redirect to Checkout if not there
        if (router.currentRoute.value.path !== '/ban-hang') {
          await router.push('/ban-hang');
        }
      } else {
        lastScannedItem.value = null;
        scanEventCounter.value++;
        
        // Not Found -> Redirect to Inventory and pre-fill creation
        if (router.currentRoute.value.path !== '/kho') {
          await router.push('/kho');
        }
      }
    } catch (error) {
      console.error('Lỗi khi xử lý mã quét toàn cục:', error);
    } finally {
      isProcessing.value = false;
    }
  }

  return {
    isProcessing,
    lastScannedCode,
    lastScannedItem,
    pendingCheckoutItems,
    scanEventCounter,
    processGlobalScan,
    consumePendingCheckoutItems,
  };
});
