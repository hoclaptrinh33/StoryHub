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
  const canonicalizeScannedCode = (val: string) => {
    const compact = val.trim().replace(/\s+/g, '');
    if (!compact) {
      return '';
    }

    const upperCompact = compact.toUpperCase();
    if (upperCompact.startsWith('RTN-')) {
      return `RNT-${compact.slice(4)}`;
    }

    return compact;
  };

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
    console.log('[SCANNER] processGlobalScan called with:', code);
    if (isProcessing.value) {
      console.log('[SCANNER] BLOCKED: isProcessing is true');
      return;
    }
    
    // Skip global processing if on the Return page to allow local specialized scanning
    if (router.currentRoute.value.path === '/hoan-tra') return;

    const scannedCode = canonicalizeScannedCode(code);
    if (!scannedCode) {
      console.log('[SCANNER] BLOCKED: scannedCode is empty after canonicalize');
      return;
    }
    console.log('[SCANNER] canonicalized:', scannedCode);

      isProcessing.value = true;
      lastScannedCode.value = scannedCode;
      
      try {
        // On dashboard: check if item is currently rented
        if (router.currentRoute.value.path === '/') {
          try {
            const rentalStatus = await checkItemRentalStatus(scannedCode);
            if (rentalStatus.rental_contract_id) {
              // Item is currently rented, go to return page with contract
              await router.push({ 
                path: '/hoan-tra', 
                query: { scan: rentalStatus.rental_contract_id } 
              });
              return;
            }
          } catch {
            // Skip
          }
        }

        // Search inventory
        console.log('[SCANNER] Fetching inventory for:', scannedCode);
        const results = await fetchInventoryItems(scannedCode);
        console.log('[SCANNER] Search results count:', results.length, results.map(r => r.id));
        
        const normalizedCode = normalize(scannedCode);
        const exactMatch = results.find(item => 
          normalize(canonicalizeScannedCode(item.code)) === normalizedCode || 
          normalize(canonicalizeScannedCode(item.id)) === normalizedCode
        ) || (results.length === 1 ? results[0] : null);

        console.log('[SCANNER] exactMatch:', exactMatch ? exactMatch.id : 'NULL');

        if (exactMatch) {
          lastScannedItem.value = exactMatch;
          queuePendingCheckoutItem(exactMatch);
          console.log('[SCANNER] Queued item, pending count:', pendingCheckoutItems.value.length);
        } else {
          lastScannedItem.value = null;
          console.log('[SCANNER] No match found');
        }

        // Alert views
        const oldCounter = scanEventCounter.value;
        scanEventCounter.value++;
        console.log('[SCANNER] scanEventCounter:', oldCounter, '->', scanEventCounter.value);
        
        const upperScannedCode = scannedCode.toUpperCase();
        const isInternalSku = upperScannedCode.startsWith('RNT-') || upperScannedCode.startsWith('RTN-') || upperScannedCode.startsWith('ITM-');
        const isPotentialIsbn = /^[0-9-]{10,20}$/.test(scannedCode);

        if (exactMatch) {
          if (router.currentRoute.value.path !== '/ban-hang') {
            console.log('[SCANNER] Redirecting to /ban-hang (exactMatch)');
            await router.push('/ban-hang');
            // Sau khi redirect, tăng counter lần nữa để checkout mới mount có thể nhận
            console.log('[SCANNER] Post-redirect: bumping counter again');
            scanEventCounter.value++;
          }
        } else {
          if ((isInternalSku || isPotentialIsbn) && router.currentRoute.value.path !== '/ban-hang') {
            console.log('[SCANNER] Redirecting to /ban-hang (isbn/sku)');
            await router.push('/ban-hang');
            scanEventCounter.value++;
          } else if (!isInternalSku && !isPotentialIsbn && router.currentRoute.value.path !== '/kho') {
            console.log('[SCANNER] Redirecting to /kho');
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
