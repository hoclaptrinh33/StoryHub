# WebSocket Realtime Implementation

## 1) Muc tieu

Kenh realtime cap nhat 2 su kien:

- `item_status_changed`
- `rental_settlement_finished`

Muc tieu chinh la dong bo trang thai item va settlement gan realtime cho man hinh POS va Rental Return, giam thao tac refresh thu cong.

## 2) Kien truc

Thanh phan backend:

- `backend/app/api/websocket.py`: endpoint WS `/ws/item-live-updates`, auth, handshake, ping/pong, subscribe/unsubscribe.
- `backend/app/services/websocket_manager.py`: registry ket noi, loc subscription theo role/branch, gioi han ket noi, shutdown notice.
- `backend/app/services/event_publisher.py`: phat event + throttle theo item/settlement.
- `backend/app/services/realtime_metrics.py`: snapshot metrics runtime cho observability.

Thanh phan frontend:

- `frontend/src/services/wsManager.ts`: quan ly ket noi, reconnect backoff, heartbeat watchdog.
- `frontend/src/stores/realtimeEvents.ts`: cache event, dedupe theo `event_id`, fallback polling.
- `frontend/src/composables/useWebSocket.ts`: API composable cho view.

## 3) Vong doi ket noi

1. Client mo WS den `/ws/item-live-updates?token=...&branch_id=...`.
2. Server xac thuc token va tao `connection_id`.
3. Server gui `connection_established` voi danh sach event da subscribe mac dinh.
4. Server gui `ping` theo interval cau hinh.
5. Client phan hoi `pong`.
6. Neu client bi timeout heartbeat qua nguong, server dong ket noi.
7. Frontend tu reconnect theo exponential backoff.
8. Neu reconnect that bai qua nguong, frontend chuyen sang fallback polling.

## 4) Luong event

### 4.1 Item status

- Phat event tu cac API: inventory reserve, POS order, rental create, unified checkout, rental return.
- Event duoc loc theo:
  - role
  - branch
  - subscribed events

### 4.2 Rental settlement

- Phat event khi `POST /api/v1/rentals/contracts/{contract_id}/return` hoan tat settlement.
- Payload gom `settlement_id`, `contract_id`, `total_fee`, `refund_to_customer`, `remaining_debt`, `settled_at`.

## 5) Throttle va bao ve

- `item_status_changed`: toi da 1 event / 300ms / item.
- `rental_settlement_finished`: toi da 1 event / 200ms / settlement.
- Event cuoi trong cua so throttle duoc giu lai va gui ra.
- Gioi han kich thuoc message duoc enforce o manager (`ws_message_size_limit_kb`).

## 6) Error handling

Ma loi ket noi chinh:

- `4001`: invalid token
- `4429`: vuot gioi han ket noi
- `4000`: heartbeat timeout hoac connection bi replace

Ung xu frontend:

- Ket noi loi: chuyen `connectionStatus` sang `error`.
- Reconnect theo backoff, co gioi han so lan thu.
- Qua gioi han: fallback polling va thong bao loi cho nguoi dung.

## 7) Observability metrics

Snapshot endpoint:

- `GET /api/v1/system/realtime/metrics` (role: manager, owner)

Fields:

- `ws_connections_active`
- `ws_connection_rejections_total`
- `ws_events_published_total` (by event type)
- `ws_event_latency_ms` (`count`, `p50`, `p95`, `p99`, `max`)
- `ws_broadcast_failures_total`
- `generated_at`

## 8) Ghi chu hieu nang

Da co:

- Unit + integration tests backend cho manager/publisher/endpoint/event emission.
- Frontend unit tests cho ws manager va realtime store (dedupe + fallback polling).

Con lai (thuc hien o staging):

- Load test 50-300 ket noi dong thoi.
- Do p99 latency va memory baseline theo runbook.
