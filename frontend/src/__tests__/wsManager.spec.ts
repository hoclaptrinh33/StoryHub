import { beforeEach, describe, expect, it, vi } from "vitest";

import { WebSocketManager } from "../services/wsManager";

type FakeCloseEvent = {
  code?: number;
  reason?: string;
};

class FakeWebSocket {
  static readonly CONNECTING = 0;

  static readonly OPEN = 1;

  static readonly CLOSING = 2;

  static readonly CLOSED = 3;

  static instances: FakeWebSocket[] = [];

  static reset(): void {
    FakeWebSocket.instances = [];
  }

  static latest(): FakeWebSocket {
    const latestSocket = FakeWebSocket.instances.at(-1);
    if (!latestSocket) {
      throw new Error("No fake websocket instance available.");
    }
    return latestSocket;
  }

  readonly url: string;

  readyState = FakeWebSocket.CONNECTING;

  sentMessages: string[] = [];

  onopen: (() => void) | null = null;

  onmessage: ((event: { data: string }) => void) | null = null;

  onerror: (() => void) | null = null;

  onclose: ((event: FakeCloseEvent) => void) | null = null;

  constructor(url: string) {
    this.url = url;
    FakeWebSocket.instances.push(this);
  }

  open(): void {
    this.readyState = FakeWebSocket.OPEN;
    this.onopen?.();
  }

  send(data: string): void {
    this.sentMessages.push(data);
  }

  receive(payload: unknown): void {
    this.onmessage?.({ data: JSON.stringify(payload) });
  }

  close(code = 1000, reason = ""): void {
    if (this.readyState === FakeWebSocket.CLOSED) {
      return;
    }

    this.readyState = FakeWebSocket.CLOSED;
    this.onclose?.({ code, reason });
  }
}

describe("WebSocketManager", () => {
  beforeEach(() => {
    FakeWebSocket.reset();
    vi.stubGlobal("WebSocket", FakeWebSocket as unknown as typeof WebSocket);
  });

  it("connects, handles ping, and disconnects cleanly", () => {
    const manager = new WebSocketManager({
      baseReconnectDelayMs: 10,
      maxReconnectDelayMs: 40,
      maxReconnectAttempts: 3,
    });

    const statusHistory: string[] = [];
    manager.onStatusChange((status) => {
      statusHistory.push(status);
    });

    manager.connect("ws://localhost:8000/ws/item-live-updates");
    const socket = FakeWebSocket.latest();

    expect(statusHistory.at(-1)).toBe("connecting");

    socket.open();
    expect(manager.getStatus()).toBe("connected");

    socket.receive({
      type: "ping",
      timestamp: "2026-04-19T10:00:00Z",
    });

    expect(socket.sentMessages).toHaveLength(1);
    expect(JSON.parse(socket.sentMessages[0]).type).toBe("pong");

    manager.disconnect();
    expect(manager.getStatus()).toBe("disconnected");
  });

  it("reconnects with backoff after unexpected disconnect", async () => {
    vi.useFakeTimers();

    const manager = new WebSocketManager({
      baseReconnectDelayMs: 10,
      maxReconnectDelayMs: 40,
      maxReconnectAttempts: 3,
    });

    manager.connect("ws://localhost:8000/ws/item-live-updates");

    const firstSocket = FakeWebSocket.latest();
    firstSocket.open();
    firstSocket.close(1011, "upstream error");

    expect(manager.getStatus()).toBe("reconnecting");

    await vi.advanceTimersByTimeAsync(10);
    expect(FakeWebSocket.instances).toHaveLength(2);

    const secondSocket = FakeWebSocket.latest();
    secondSocket.open();

    expect(manager.getStatus()).toBe("connected");

    manager.disconnect();
  });

  it("enters error state when reconnect limit is exceeded", async () => {
    vi.useFakeTimers();

    const manager = new WebSocketManager({
      baseReconnectDelayMs: 5,
      maxReconnectDelayMs: 20,
      maxReconnectAttempts: 1,
    });

    manager.connect("ws://localhost:8000/ws/item-live-updates");
    const firstSocket = FakeWebSocket.latest();
    firstSocket.open();

    firstSocket.close(1011, "boom");
    await vi.advanceTimersByTimeAsync(5);

    const secondSocket = FakeWebSocket.latest();
    secondSocket.close(1011, "boom-again");

    expect(manager.getStatus()).toBe("error");
  });
});
