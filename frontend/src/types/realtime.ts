export type RealtimeConnectionStatus =
  | "disconnected"
  | "connecting"
  | "connected"
  | "reconnecting"
  | "error";

export type ItemStatusChangedEvent = {
  type: "item_status_changed";
  event_id: string;
  item_id: string;
  old_status: string;
  new_status: string;
  changed_at: string;
  source_api: string;
  changed_by?: string;
};

export type RentalSettlementFinishedEvent = {
  type: "rental_settlement_finished";
  event_id: string;
  settlement_id: string;
  contract_id: string;
  total_fee: number;
  refund_to_customer: number;
  remaining_debt: number;
  settled_at: string;
};

export type ConnectionEstablishedEvent = {
  type: "connection_established";
  connection_id: string;
  server_time: string;
  subscribed_events: string[];
  message_size_limit_kb: number;
};

export type WsPingMessage = {
  type: "ping";
  timestamp: string;
};

export type WsPongMessage = {
  type: "pong";
  timestamp: string;
};

export type WsSubscriptionStateMessage = {
  type: "subscribed" | "unsubscribed";
  events: string[];
};

export type WsErrorMessage = {
  type: "error";
  code: string;
  message: string;
};

export type ServerShutdownMessage = {
  type: "server_shutdown";
  message: string;
  timestamp: string;
};

export type RentalOverdueEvent = {
  type: "rental_overdue";
  event_id: string;
  contract_count: number;
  notified_at: string;
};

export type InventoryDataChangedEvent = {
  type: "inventory_data_changed";
  event_id: string;
  reason: string;
  changed_at: string;
};

// 1. THÊM MỚI: Định nghĩa kiểu dữ liệu cho sự kiện cập nhật tồn kho
export type VolumeStockUpdatedEvent = {
  type: "volume_stock_updated";
  event_id: string;
  // Bạn có thể bổ sung thêm các trường dữ liệu mà backend FastAPI gửi về ở đây
  // Ví dụ:
  // volume_id: string;
  // new_stock_quantity: number;
  // updated_at: string;
};

// 2. CẬP NHẬT: Thêm VolumeStockUpdatedEvent vào Union Type chung
export type RealtimeMessage =
  | ConnectionEstablishedEvent
  | ItemStatusChangedEvent
  | RentalSettlementFinishedEvent
  | RentalOverdueEvent
  | InventoryDataChangedEvent
  | VolumeStockUpdatedEvent // <-- Đã thêm vào đây
  | WsPingMessage
  | WsPongMessage
  | WsSubscriptionStateMessage
  | WsErrorMessage
  | ServerShutdownMessage;