# Runbook: WebSocket Troubleshooting

## 1) Muc tieu

Tai lieu nay dung de debug nhanh cac van de realtime trong moi truong dev/staging.

## 2) Trieu chung pho bien

- Khong ket noi duoc websocket.
- Mat ket noi lien tuc, reconnect loop.
- UI khong nhan event sau khi thao tac API thanh cong.
- Do tre event cao bat thuong.
- Broadcast failures tang dot bien.

## 3) Kiem tra nhanh

1. Kiem tra backend con song:

```powershell
curl http://127.0.0.1:8000/api/v1/health
```

2. Kiem tra metrics snapshot:

```powershell
curl -H "Authorization: Bearer manager-demo" http://127.0.0.1:8000/api/v1/system/realtime/metrics
```

3. Theo doi log backend realtime:

- Tim `Realtime event delivered`
- Tim `Failed to broadcast event`
- Tim `WS_HEARTBEAT_TIMEOUT`

## 4) Test ket noi thu cong

### 4.1 Dung wscat

```powershell
npm i -g wscat
wscat -c "ws://127.0.0.1:8000/ws/item-live-updates?token=cashier-demo&branch_id=main"
```

Gui lenh subscribe:

```json
{
  "type": "subscribe",
  "events": ["item_status_changed", "rental_settlement_finished"]
}
```

### 4.2 Trigger event tu REST API

Trong terminal khac:

```powershell
curl -X POST "http://127.0.0.1:8000/api/v1/inventory/reservations" ^
  -H "Content-Type: application/json" ^
  -H "Authorization: Bearer cashier-demo" ^
  -H "X-Device-Id: WEB-KIOSK-01" ^
  -d "{\"item_id\":\"ITM-DORA01-001\",\"customer_id\":1,\"reservation_minutes\":15,\"request_id\":\"runbook-reserve-001\"}"
```

Neu websocket hoat dong dung, `wscat` se nhan duoc `item_status_changed`.

## 5) Neu mat ket noi lien tuc

1. Kiem tra timeout heartbeat:

- `STORYHUB_WS_HEARTBEAT_INTERVAL_MS`
- `STORYHUB_WS_MAX_MISSED_HEARTBEATS`

2. Kiem tra browser/network:

- Proxy, VPN, antivirus co chan WS hay khong.

3. Kiem tra gioi han ket noi:

- Metrics `ws_connections_active`
- Metrics `ws_connection_rejections_total`

4. Kiem tra fallback polling tren frontend:

- Sau 5s disconnected, frontend bat dau polling.
- Khi reconnect thanh cong, polling phai dung.

## 6) Neu event khong den UI

1. Xac nhan role va branch dung voi event.
2. Xac nhan client dang subscribe event can nghe.
3. Xac nhan API da trigger publisher.
4. Kiem tra `ws_broadcast_failures_total` co tang khong.
5. Kiem tra payload co vuot `ws_message_size_limit_kb` khong.

## 7) Baseline canh bao de nghi

- `ws_connections_active > 250` trong 5 phut.
- `ws_broadcast_failures_total` tang nhanh hon 1% event.
- `ws_event_latency_ms.p99 > 1000` ms.

Load test tham khao:

```powershell
k6 run backend/scripts/load/realtime_ws_k6.js
```

## 8) Quy trinh khac phuc

1. Co lap van de (1 user / 1 branch / 1 event type).
2. Xac nhan bang wscat.
3. Kiem tra metrics snapshot.
4. Neu can, restart backend co kiem soat de gui `server_shutdown`.
5. Chay lai smoke test POS + Rental Return.
