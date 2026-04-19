import { storeToRefs } from "pinia";

import { useRealtimeEventsStore } from "../stores/realtimeEvents";

export const useWebSocket = () => {
  const realtimeStore = useRealtimeEventsStore();
  const {
    connectionStatus,
    lastError,
    isConnected,
    latestItemStatusEvent,
    latestSettlementEvent,
    itemStatusUpdates,
    settlementSnapshots,
  } = storeToRefs(realtimeStore);

  return {
    connectionStatus,
    lastError,
    isConnected,
    latestItemStatusEvent,
    latestSettlementEvent,
    itemStatusUpdates,
    settlementSnapshots,
    connect: realtimeStore.connect,
    disconnect: realtimeStore.disconnect,
    subscribe: realtimeStore.subscribe,
    unsubscribe: realtimeStore.unsubscribe,
    setTrackedItems: realtimeStore.setTrackedItems,
    setTrackedContracts: realtimeStore.setTrackedContracts,
    clearTrackedTargets: realtimeStore.clearTrackedTargets,
    getLatestItemStatus: realtimeStore.getLatestItemStatus,
    getLatestSettlementSnapshot: realtimeStore.getLatestSettlementSnapshot,
  };
};
