import { defineStore } from "pinia";
import { computed, ref } from "vue";

import {
  fetchInventoryItemStatus,
  fetchRentalSettlementStatus,
  resolveRealtimeWsUrl,
  type RentalSettlementStatusPayload,
} from "../services/storyhubApi";
import { WebSocketManager } from "../services/wsManager";
import type {
  ItemStatusChangedEvent,
  RealtimeConnectionStatus,
  RealtimeMessage,
  RentalSettlementFinishedEvent,
} from "../types/realtime";

const wsManager = new WebSocketManager();
const trackedItemIds = new Set<string>();
const trackedContractIds = new Set<number>();

let initialized = false;
let statusUnsubscribe: (() => void) | null = null;
let messageUnsubscribe: (() => void) | null = null;
let fallbackStartTimer: number | null = null;
let fallbackPollTimer: number | null = null;
let fallbackStartedAt = 0;
let currentToken = "cashier-demo";

export const useRealtimeEventsStore = defineStore("realtime-events", () => {
  const connectionStatus = ref<RealtimeConnectionStatus>("disconnected");
  const lastError = ref<string | null>(null);
  const lastConnectedAt = ref<string | null>(null);

  const latestItemStatusEvent = ref<ItemStatusChangedEvent | null>(null);
  const latestSettlementEvent = ref<RentalSettlementFinishedEvent | null>(null);

  const itemStatusUpdates = ref<Record<string, ItemStatusChangedEvent>>({});
  const settlementSnapshots = ref<Record<string, RentalSettlementStatusPayload>>({});

  const recentEventIds = ref<string[]>([]);

  const isConnected = computed(() => connectionStatus.value === "connected");

  const ensureInitialized = () => {
    if (initialized) {
      return;
    }

    statusUnsubscribe = wsManager.onStatusChange((status, error) => {
      connectionStatus.value = status;
      lastError.value = error;

      if (status === "connected") {
        lastConnectedAt.value = new Date().toISOString();
        stopFallbackPolling();
        clearFallbackStartTimer();
        return;
      }

      scheduleFallbackStart();
    });

    messageUnsubscribe = wsManager.onMessage((message) => {
      handleRealtimeMessage(message);
    });

    initialized = true;
  };

  const handleRealtimeMessage = (message: RealtimeMessage) => {
    if (message.type === "connection_established") {
      lastConnectedAt.value = message.server_time;
      return;
    }

    if (message.type === "error") {
      lastError.value = `${message.code}: ${message.message}`;
      return;
    }

    if (message.type === "server_shutdown") {
      lastError.value = message.message;
      return;
    }

    if (message.type === "item_status_changed") {
      upsertItemEvent(message);
      return;
    }

    if (message.type === "rental_settlement_finished") {
      upsertSettlementEvent(message);
    }
  };

  const rememberEventId = (eventId: string): boolean => {
    if (!eventId) {
      return false;
    }

    if (recentEventIds.value.includes(eventId)) {
      return true;
    }

    recentEventIds.value.push(eventId);
    if (recentEventIds.value.length > 300) {
      recentEventIds.value.splice(0, recentEventIds.value.length - 300);
    }

    return false;
  };

  const upsertItemEvent = (event: ItemStatusChangedEvent) => {
    if (rememberEventId(event.event_id)) {
      return;
    }

    itemStatusUpdates.value = {
      ...itemStatusUpdates.value,
      [event.item_id]: event,
    };
    latestItemStatusEvent.value = event;
  };

  const upsertSettlementEvent = (event: RentalSettlementFinishedEvent) => {
    if (rememberEventId(event.event_id)) {
      return;
    }

    latestSettlementEvent.value = event;
  };

  const connect = (token = "cashier-demo", branchId?: string) => {
    ensureInitialized();

    currentToken = token;

    const wsUrl = resolveRealtimeWsUrl(token, branchId);
    wsManager.connect(wsUrl);
  };

  const disconnect = () => {
    wsManager.disconnect();
    clearFallbackStartTimer();
    stopFallbackPolling();
  };

  const subscribe = (events: string[]) => {
    wsManager.subscribe(events);
  };

  const unsubscribe = (events: string[]) => {
    wsManager.unsubscribe(events);
  };

  const setTrackedItems = (itemIds: string[]) => {
    trackedItemIds.clear();
    itemIds
      .map((itemId) => itemId.trim())
      .filter((itemId) => itemId.length > 0)
      .forEach((itemId) => trackedItemIds.add(itemId));
  };

  const setTrackedContracts = (contractIds: number[]) => {
    trackedContractIds.clear();
    contractIds
      .filter((contractId) => Number.isInteger(contractId) && contractId > 0)
      .forEach((contractId) => trackedContractIds.add(contractId));
  };

  const clearTrackedTargets = () => {
    trackedItemIds.clear();
    trackedContractIds.clear();
  };

  const scheduleFallbackStart = () => {
    if (fallbackStartTimer !== null) {
      return;
    }

    fallbackStartTimer = window.setTimeout(() => {
      fallbackStartTimer = null;
      if (connectionStatus.value === "connected") {
        return;
      }
      startFallbackPolling();
    }, 5000);
  };

  const clearFallbackStartTimer = () => {
    if (fallbackStartTimer === null) {
      return;
    }

    window.clearTimeout(fallbackStartTimer);
    fallbackStartTimer = null;
  };

  const startFallbackPolling = () => {
    if (fallbackPollTimer !== null) {
      return;
    }

    fallbackStartedAt = Date.now();
    void runFallbackCycle();
  };

  const stopFallbackPolling = () => {
    if (fallbackPollTimer !== null) {
      window.clearTimeout(fallbackPollTimer);
      fallbackPollTimer = null;
    }
  };

  const getPollingIntervalMs = () => {
    const elapsedMs = Date.now() - fallbackStartedAt;
    if (elapsedMs < 30000) {
      return 5000;
    }
    if (elapsedMs < 120000) {
      return 10000;
    }
    return 30000;
  };

  const scheduleNextFallbackCycle = () => {
    stopFallbackPolling();
    fallbackPollTimer = window.setTimeout(() => {
      fallbackPollTimer = null;
      void runFallbackCycle();
    }, getPollingIntervalMs());
  };

  const runFallbackCycle = async () => {
    if (connectionStatus.value === "connected") {
      stopFallbackPolling();
      return;
    }

    const pollingTasks: Promise<void>[] = [];

    trackedItemIds.forEach((itemId) => {
      pollingTasks.push(
        (async () => {
          try {
            const status = await fetchInventoryItemStatus(itemId, currentToken);
            applyPolledItemStatus(status);
          } catch {
            // Polling failures are tolerated and retried in the next cycle.
          }
        })(),
      );
    });

    trackedContractIds.forEach((contractId) => {
      pollingTasks.push(
        (async () => {
          try {
            const snapshot = await fetchRentalSettlementStatus(contractId, currentToken);
            settlementSnapshots.value = {
              ...settlementSnapshots.value,
              [snapshot.contract_id]: snapshot,
            };

            if (snapshot.settlement_id) {
              const syntheticEvent: RentalSettlementFinishedEvent = {
                type: "rental_settlement_finished",
                event_id: `poll-${snapshot.settlement_id}-${snapshot.settled_at ?? "unknown"}`,
                settlement_id: snapshot.settlement_id,
                contract_id: snapshot.contract_id,
                total_fee: snapshot.total_fee,
                refund_to_customer: snapshot.refund_to_customer,
                remaining_debt: snapshot.remaining_debt,
                settled_at: snapshot.settled_at ?? new Date().toISOString(),
              };
              upsertSettlementEvent(syntheticEvent);
            }
          } catch {
            // Polling failures are tolerated and retried in the next cycle.
          }
        })(),
      );
    });

    if (pollingTasks.length > 0) {
      await Promise.allSettled(pollingTasks);
    }

    if (!isConnected.value) {
      scheduleNextFallbackCycle();
    }
  };

  const applyPolledItemStatus = (payload: {
    item_id: string;
    status: string;
    changed_at: string;
  }) => {
    const previous = itemStatusUpdates.value[payload.item_id];
    const syntheticEvent: ItemStatusChangedEvent = {
      type: "item_status_changed",
      event_id: `poll-${payload.item_id}-${payload.changed_at}`,
      item_id: payload.item_id,
      old_status: previous?.new_status ?? payload.status,
      new_status: payload.status,
      changed_at: payload.changed_at,
      source_api: "fallback_polling_v1",
      changed_by: "system",
    };
    upsertItemEvent(syntheticEvent);
  };

  const getLatestItemStatus = (itemId: string) => itemStatusUpdates.value[itemId] ?? null;

  const getLatestSettlementSnapshot = (contractId: string) =>
    settlementSnapshots.value[contractId] ?? null;

  const disposeRealtimeListeners = () => {
    statusUnsubscribe?.();
    messageUnsubscribe?.();
    statusUnsubscribe = null;
    messageUnsubscribe = null;
    initialized = false;
  };

  return {
    connectionStatus,
    lastError,
    lastConnectedAt,
    latestItemStatusEvent,
    latestSettlementEvent,
    itemStatusUpdates,
    settlementSnapshots,
    isConnected,
    connect,
    disconnect,
    subscribe,
    unsubscribe,
    setTrackedItems,
    setTrackedContracts,
    clearTrackedTargets,
    getLatestItemStatus,
    getLatestSettlementSnapshot,
    disposeRealtimeListeners,
  };
});
