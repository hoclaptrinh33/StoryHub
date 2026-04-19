# API Reference v1: WebSocket Item Live Updates

## 1) Endpoint

- URL: `/ws/item-live-updates`
- Method: WebSocket upgrade
- Auth: `token` query param (hoac `authorization` query param)

Vi du:

```text
ws://127.0.0.1:8000/ws/item-live-updates?token=cashier-demo&branch_id=main
```

## 2) Handshake message

Server gui ngay sau khi ket noi thanh cong:

```json
{
  "type": "connection_established",
  "connection_id": "f4f6...",
  "server_time": "2026-04-19T10:00:00Z",
  "subscribed_events": ["item_status_changed", "rental_settlement_finished"],
  "message_size_limit_kb": 64
}
```

## 3) Client -> Server messages

### 3.1 Subscribe

```json
{
  "type": "subscribe",
  "events": ["item_status_changed"]
}
```

### 3.2 Unsubscribe

```json
{
  "type": "unsubscribe",
  "events": ["item_status_changed"]
}
```

### 3.3 Pong

```json
{
  "type": "pong",
  "timestamp": "2026-04-19T10:00:10Z"
}
```

## 4) Server -> Client messages

### 4.1 Ping

```json
{
  "type": "ping",
  "timestamp": "2026-04-19T10:00:10Z"
}
```

### 4.2 Item status changed

```json
{
  "type": "item_status_changed",
  "event_id": "evt-...",
  "item_id": "ITM-DORA01-001",
  "old_status": "available",
  "new_status": "reserved",
  "changed_at": "2026-04-19T10:00:12Z",
  "source_api": "inventory_reserve_item_v1",
  "changed_by": "cashier-01"
}
```

### 4.3 Rental settlement finished

```json
{
  "type": "rental_settlement_finished",
  "event_id": "evt-...",
  "settlement_id": "5001",
  "contract_id": "2001",
  "total_fee": 25000,
  "refund_to_customer": 5000,
  "remaining_debt": 0,
  "settled_at": "2026-04-19T10:01:20Z"
}
```

### 4.4 Subscribe ack

```json
{
  "type": "subscribed",
  "events": ["item_status_changed"]
}
```

### 4.5 Unsubscribe ack

```json
{
  "type": "unsubscribed",
  "events": []
}
```

### 4.6 Error

```json
{
  "type": "error",
  "code": "WS_INVALID_MESSAGE",
  "message": "Message must be valid JSON object."
}
```

### 4.7 Server shutdown

```json
{
  "type": "server_shutdown",
  "message": "Realtime service is restarting.",
  "timestamp": "2026-04-19T10:05:00Z"
}
```

## 5) Close codes

- `4001`: auth invalid token
- `4429`: connection limit reached
- `4000`: heartbeat timeout or replaced by new connection
- `1001`: server shutdown

## 6) Minimal client example (browser)

```ts
const ws = new WebSocket(
  "ws://127.0.0.1:8000/ws/item-live-updates?token=cashier-demo&branch_id=main",
);

ws.onopen = () => {
  ws.send(
    JSON.stringify({ type: "subscribe", events: ["item_status_changed"] }),
  );
};

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  if (message.type === "ping") {
    ws.send(
      JSON.stringify({ type: "pong", timestamp: new Date().toISOString() }),
    );
    return;
  }

  if (message.type === "item_status_changed") {
    console.log("Item changed", message.item_id, message.new_status);
  }
};
```
