import type { RealtimeConnectionStatus, RealtimeMessage } from "../types/realtime";

type MessageListener = (message: RealtimeMessage) => void;
type StatusListener = (status: RealtimeConnectionStatus, error: string | null) => void;

type WebSocketManagerOptions = {
  maxReconnectAttempts?: number;
  baseReconnectDelayMs?: number;
  maxReconnectDelayMs?: number;
  heartbeatTimeoutMs?: number;
};

const DEFAULT_OPTIONS: Required<WebSocketManagerOptions> = {
  maxReconnectAttempts: 10,
  baseReconnectDelayMs: 1000,
  maxReconnectDelayMs: 32000,
  heartbeatTimeoutMs: 65000,
};

export class WebSocketManager {
  private socket: WebSocket | null = null;

  private readonly options: Required<WebSocketManagerOptions>;

  private readonly messageListeners = new Set<MessageListener>();

  private readonly statusListeners = new Set<StatusListener>();

  private reconnectAttempts = 0;

  private reconnectTimer: number | null = null;

  private heartbeatWatchdogTimer: number | null = null;

  private lastPingAt = 0;

  private manualDisconnect = false;

  private currentUrl = "";

  private status: RealtimeConnectionStatus = "disconnected";

  private lastError: string | null = null;

  constructor(options?: WebSocketManagerOptions) {
    this.options = {
      ...DEFAULT_OPTIONS,
      ...options,
    };
  }

  getStatus(): RealtimeConnectionStatus {
    return this.status;
  }

  onMessage(listener: MessageListener): () => void {
    this.messageListeners.add(listener);
    return () => {
      this.messageListeners.delete(listener);
    };
  }

  onStatusChange(listener: StatusListener): () => void {
    this.statusListeners.add(listener);
    listener(this.status, this.lastError);

    return () => {
      this.statusListeners.delete(listener);
    };
  }

  connect(url: string): void {
    if (!url) {
      this.setStatus("error", "WebSocket URL is empty.");
      return;
    }

    const socketState = this.socket?.readyState;
    if (
      socketState === WebSocket.OPEN ||
      socketState === WebSocket.CONNECTING
    ) {
      return;
    }

    this.currentUrl = url;
    this.manualDisconnect = false;

    const isReconnecting = this.reconnectAttempts > 0;
    this.setStatus(isReconnecting ? "reconnecting" : "connecting");

    const socket = new WebSocket(url);
    this.socket = socket;

    socket.onopen = () => {
      this.reconnectAttempts = 0;
      this.lastError = null;
      this.lastPingAt = Date.now();
      this.startHeartbeatWatchdog();
      this.setStatus("connected");
    };

    socket.onmessage = (event) => {
      const parsed = this.parseMessage(event.data);
      if (!parsed) {
        return;
      }

      if (parsed.type === "ping") {
        this.lastPingAt = Date.now();
        this.send({
          type: "pong",
          timestamp: new Date().toISOString(),
        });
      }

      this.messageListeners.forEach((listener) => {
        listener(parsed);
      });
    };

    socket.onerror = () => {
      this.lastError = "Realtime channel encountered an unexpected error.";
      this.setStatus("error", this.lastError);
    };

    socket.onclose = () => {
      this.stopHeartbeatWatchdog();
      this.socket = null;

      if (this.manualDisconnect) {
        this.setStatus("disconnected", null);
        return;
      }

      this.scheduleReconnect();
    };
  }

  disconnect(): void {
    this.manualDisconnect = true;
    this.stopHeartbeatWatchdog();
    this.clearReconnectTimer();

    if (!this.socket) {
      this.setStatus("disconnected", null);
      return;
    }

    if (this.socket.readyState === WebSocket.OPEN || this.socket.readyState === WebSocket.CONNECTING) {
      this.socket.close(1000, "CLIENT_DISCONNECT");
    }

    this.socket = null;
    this.setStatus("disconnected", null);
  }

  subscribe(events: string[]): void {
    this.send({ type: "subscribe", events });
  }

  unsubscribe(events: string[]): void {
    this.send({ type: "unsubscribe", events });
  }

  send(message: Record<string, unknown>): void {
    if (!this.socket || this.socket.readyState !== WebSocket.OPEN) {
      return;
    }

    this.socket.send(JSON.stringify(message));
  }

  private scheduleReconnect(): void {
    if (!this.currentUrl) {
      this.setStatus("disconnected", this.lastError);
      return;
    }

    if (this.reconnectAttempts >= this.options.maxReconnectAttempts) {
      this.setStatus(
        "error",
        "Realtime channel reached reconnect limit. Switching to fallback polling.",
      );
      return;
    }

    const backoffDelay = Math.min(
      this.options.baseReconnectDelayMs * 2 ** this.reconnectAttempts,
      this.options.maxReconnectDelayMs,
    );

    this.reconnectAttempts += 1;
    this.setStatus("reconnecting", this.lastError);

    this.clearReconnectTimer();
    this.reconnectTimer = window.setTimeout(() => {
      this.reconnectTimer = null;
      this.connect(this.currentUrl);
    }, backoffDelay);
  }

  private parseMessage(rawData: string): RealtimeMessage | null {
    try {
      const parsed = JSON.parse(rawData) as RealtimeMessage;
      if (!parsed || typeof parsed !== "object" || typeof parsed.type !== "string") {
        this.lastError = "Invalid realtime message format.";
        return null;
      }
      return parsed;
    } catch {
      this.lastError = "Failed to parse realtime message.";
      return null;
    }
  }

  private startHeartbeatWatchdog(): void {
    this.stopHeartbeatWatchdog();

    this.heartbeatWatchdogTimer = window.setInterval(() => {
      if (this.status !== "connected") {
        return;
      }

      const elapsed = Date.now() - this.lastPingAt;
      if (elapsed <= this.options.heartbeatTimeoutMs) {
        return;
      }

      this.lastError = "Realtime heartbeat timed out.";
      this.forceReconnect();
    }, 10000);
  }

  private stopHeartbeatWatchdog(): void {
    if (this.heartbeatWatchdogTimer === null) {
      return;
    }

    window.clearInterval(this.heartbeatWatchdogTimer);
    this.heartbeatWatchdogTimer = null;
  }

  private forceReconnect(): void {
    if (!this.socket) {
      this.scheduleReconnect();
      return;
    }

    this.manualDisconnect = false;
    if (this.socket.readyState === WebSocket.OPEN || this.socket.readyState === WebSocket.CONNECTING) {
      this.socket.close(4000, "HEARTBEAT_TIMEOUT");
      return;
    }

    this.scheduleReconnect();
  }

  private clearReconnectTimer(): void {
    if (this.reconnectTimer === null) {
      return;
    }

    window.clearTimeout(this.reconnectTimer);
    this.reconnectTimer = null;
  }

  private setStatus(status: RealtimeConnectionStatus, error: string | null = this.lastError): void {
    this.status = status;
    this.lastError = error;
    this.statusListeners.forEach((listener) => {
      listener(status, error);
    });
  }
}
