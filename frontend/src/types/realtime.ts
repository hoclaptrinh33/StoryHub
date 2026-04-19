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

export type RealtimeMessage =
  | ConnectionEstablishedEvent
  | ItemStatusChangedEvent
  | RentalSettlementFinishedEvent
  | WsPingMessage
  | WsPongMessage
  | WsSubscriptionStateMessage
  | WsErrorMessage
  | ServerShutdownMessage;
