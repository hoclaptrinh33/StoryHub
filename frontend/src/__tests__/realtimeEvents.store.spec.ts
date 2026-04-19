import { createPinia, setActivePinia } from "pinia";
import { beforeEach, describe, expect, it, vi } from "vitest";

import * as storyhubApi from "../services/storyhubApi";
import type { RealtimeConnectionStatus, RealtimeMessage } from "../types/realtime";
import { useRealtimeEventsStore } from "../stores/realtimeEvents";

const wsMockState = vi.hoisted(() => ({
  statusListeners: [] as Array<(status: RealtimeConnectionStatus, error: string | null) => void>,
  messageListeners: [] as Array<(message: RealtimeMessage) => void>,
  connectCalls: [] as string[],
  subscribeCalls: [] as string[][],
  unsubscribeCalls: [] as string[][],
}));

vi.mock("../services/wsManager", () => {
  class WebSocketManager {
    getStatus(): RealtimeConnectionStatus {
      return "disconnected";
    }

    onMessage(listener: (message: RealtimeMessage) => void): () => void {
      wsMockState.messageListeners.push(listener);
      return () => {
        wsMockState.messageListeners = wsMockState.messageListeners.filter(
          (entry) => entry !== listener,
        );
      };
    }

    onStatusChange(
      listener: (status: RealtimeConnectionStatus, error: string | null) => void,
    ): () => void {
      wsMockState.statusListeners.push(listener);
      listener("disconnected", null);
      return () => {
        wsMockState.statusListeners = wsMockState.statusListeners.filter(
          (entry) => entry !== listener,
        );
      };
    }

    connect(url: string): void {
      wsMockState.connectCalls.push(url);
    }

    disconnect(): void {
      // no-op for unit test
    }

    subscribe(events: string[]): void {
      wsMockState.subscribeCalls.push([...events]);
    }

    unsubscribe(events: string[]): void {
      wsMockState.unsubscribeCalls.push([...events]);
    }
  }

  return { WebSocketManager };
});

vi.mock("../services/storyhubApi", async () => {
  const actual = await vi.importActual<typeof import("../services/storyhubApi")>("../services/storyhubApi");
  return {
    ...actual,
    fetchInventoryItemStatus: vi.fn(),
    fetchRentalSettlementStatus: vi.fn(),
    resolveRealtimeWsUrl: vi.fn(() => "ws://localhost:8000/ws/item-live-updates?token=cashier-demo"),
  };
});

const emitStatus = (status: RealtimeConnectionStatus, error: string | null = null) => {
  wsMockState.statusListeners.forEach((listener) => listener(status, error));
};

const emitMessage = (message: RealtimeMessage) => {
  wsMockState.messageListeners.forEach((listener) => listener(message));
};

describe("useRealtimeEventsStore", () => {
  beforeEach(() => {
    wsMockState.statusListeners = [];
    wsMockState.messageListeners = [];
    wsMockState.connectCalls = [];
    wsMockState.subscribeCalls = [];
    wsMockState.unsubscribeCalls = [];

    setActivePinia(createPinia());

    const resetStore = useRealtimeEventsStore();
    resetStore.disconnect();
    resetStore.clearTrackedTargets();
    resetStore.disposeRealtimeListeners();

    vi.mocked(storyhubApi.fetchInventoryItemStatus).mockReset();
    vi.mocked(storyhubApi.fetchRentalSettlementStatus).mockReset();
    vi.mocked(storyhubApi.resolveRealtimeWsUrl).mockClear();
  });

  it("deduplicates repeated item events by event_id", () => {
    const store = useRealtimeEventsStore();

    store.connect("cashier-demo", "main");
    emitStatus("connected", null);

    const event: RealtimeMessage = {
      type: "item_status_changed",
      event_id: "evt-dup-001",
      item_id: "ITM-001",
      old_status: "available",
      new_status: "reserved",
      changed_at: "2026-04-19T10:00:00Z",
      source_api: "inventory_reserve_item_v1",
      changed_by: "cashier-01",
    };

    emitMessage(event);
    emitMessage(event);

    expect(Object.keys(store.itemStatusUpdates)).toHaveLength(1);
    expect(store.itemStatusUpdates["ITM-001"]?.event_id).toBe("evt-dup-001");
    expect(store.latestItemStatusEvent?.item_id).toBe("ITM-001");
  });

  it("starts fallback polling when disconnected and stops after reconnect", async () => {
    vi.useFakeTimers();

    const store = useRealtimeEventsStore();

    vi.mocked(storyhubApi.fetchInventoryItemStatus).mockResolvedValue({
      item_id: "ITM-001",
      status: "reserved",
      changed_at: "2026-04-19T10:00:00Z",
      item_type: "rental",
    });
    vi.mocked(storyhubApi.fetchRentalSettlementStatus).mockResolvedValue({
      settlement_id: "5001",
      contract_id: "2001",
      rental_fee: 10000,
      late_fee: 0,
      damage_fee: 0,
      lost_fee: 0,
      total_fee: 10000,
      deducted_from_deposit: 10000,
      refund_to_customer: 0,
      remaining_debt: 0,
      settled_at: "2026-04-19T10:00:00Z",
      contract_status: "closed",
    });

    store.setTrackedItems(["ITM-001"]);
    store.setTrackedContracts([2001]);
    store.connect("cashier-demo", "main");

    emitStatus("error", "socket down");

    await vi.advanceTimersByTimeAsync(5000);
    await Promise.resolve();
    await Promise.resolve();

    expect(storyhubApi.fetchInventoryItemStatus).toHaveBeenCalledTimes(1);
    expect(storyhubApi.fetchRentalSettlementStatus).toHaveBeenCalledTimes(1);
    expect(store.latestSettlementEvent?.contract_id).toBe("2001");

    await vi.advanceTimersByTimeAsync(5000);
    await Promise.resolve();
    await Promise.resolve();

    expect(storyhubApi.fetchInventoryItemStatus).toHaveBeenCalledTimes(2);
    expect(storyhubApi.fetchRentalSettlementStatus).toHaveBeenCalledTimes(2);

    emitStatus("connected", null);
    await vi.advanceTimersByTimeAsync(30000);

    expect(storyhubApi.fetchInventoryItemStatus).toHaveBeenCalledTimes(2);
    expect(storyhubApi.fetchRentalSettlementStatus).toHaveBeenCalledTimes(2);
  });
});
