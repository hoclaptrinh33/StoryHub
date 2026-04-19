# Kế hoạch chi tiết Giai đoạn 5: Realtime và đồng bộ trạng thái

**Thời gian dự kiến**: 1-2 ngày (8-16 giờ)  
**Objective**: Triển khai WebSocket realtime để cập nhật trạng thái item và rental settlement mà không cần F5 thủ công.

## 📋 Tóm tắt requirement

### Từ spec realtime_item-live-updates.yaml

- **Channel**: `/ws/item-live-updates`
- **Auth**: Bắt buộc, validate token từ query params hoặc header
- **Heartbeat**: 30s (server gửi ping)
- **Reconnect**: exponential backoff, max 10 attempts
- **Events**: 2 loại: `item_status_changed` (throttle 300ms) + `rental_settlement_finished` (throttle 200ms)
- **Subscriptions**: Filtered by role + branch (role-based scope)
- **Performance**: 300 concurrent connections, 64KB msg size, buffer 100

### Events & Triggers

| Event                        | Triggers                                                                    | Source APIs                                                                                               |
| ---------------------------- | --------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| `item_status_changed`        | item.reserve, pos.create_order, rental.create_contract, rental.return_items | `inventory_reserve_item_v1`, `pos_create_order_v1`, `rental_create_contract_v1`, `rental_return_items_v1` |
| `rental_settlement_finished` | settlement완료 시                                                           | `rental_return_items_v1` (return flow의 일부)                                                             |

### Consumers

- `item_status_changed` → audit_log (sync, required) + refresh UI (async)
- `rental_settlement_finished` → update_customer_finance (sync, required) + report_aggregates (async) + notify_ui (async)

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────┐
│        Frontend (Vue 3 + Tauri)             │
│  ┌──────────────────────────────────────┐   │
│  │ WebSocketManager                     │   │
│  │ - connect/disconnect/reconnect       │   │
│  │ - subscribe/unsubscribe              │   │
│  │ - parse events                       │   │
│  └──────────────────────────────────────┘   │
│              ↑↓ (ws://)                      │
└─────────────────────────────────────────────┘
                    ↑↓
┌─────────────────────────────────────────────────────────┐
│        Backend (FastAPI)                                │
│  ┌──────────────────────────────────────────────────┐   │
│  │ WebSocket Endpoint: /ws/item-live-updates       │   │
│  │ - auth + connect                                │   │
│  │ - manage active connections                     │   │
│  │ - heartbeat & reconnect handling                │   │
│  └──────────────────────────────────────────────────┘   │
│              ↓                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │ EventPublisher (Singleton)                       │   │
│  │ - serialize & broadcast events                   │   │
│  │ - throttle by event type                         │   │
│  │ - filter by subscription (role/branch)           │   │
│  └──────────────────────────────────────────────────┘   │
│              ↑ (injected into API endpoints)            │
│  ┌──────────────────────────────────────────────────┐   │
│  │ API Endpoints (Phase 3 & 4)                      │   │
│  │ - inventory_reserve_item                         │   │
│  │ - pos_create_order / pos_refund                  │   │
│  │ - rental_create_contract / rental_return_items   │   │
│  │ → emit events after mutation                     │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

---

## ✅ Detailed Task Breakdown

### PHASE 5.0: Setup & Infrastructure (2-3 hours)

#### 5.0.1 Backend: WebSocket Connection Manager

**Owner**: Backend Lead  
**Dependencies**: None

**Tasks**:

- [ ] Create `backend/app/services/websocket_manager.py`
  - Class `WebSocketConnectionManager`:
    - Store active connections: `Dict[str, WebSocket]` keyed by conn_id
    - `connect(websocket, conn_id, user_id, branch_id, role)` → register + return success
    - `disconnect(conn_id)` → cleanup
    - `broadcast(message, filter_func)` → send to filtered connections only
    - Handle duplicate connections gracefully (close old, keep new)
- [ ] Create connection metadata store:
  - Per-connection: `user_id, branch_id, role, subscribed_events, connected_at, last_heartbeat`
  - For filtering: role-based scope and branch-based scope
- [ ] Test: Helper to simulate concurrent connections

**Exit criteria**:

- [ ] Connections can be registered, filtered, and broadcasted to
- [ ] Concurrent tests pass (simulate 10+ connections)
- [ ] No memory leak in disconnect flow

---

#### 5.0.2 Backend: WebSocket Endpoint Setup & Auth

**Owner**: Backend Lead  
**Dependencies**: 5.0.1

**Tasks**:

- [ ] Create `backend/app/api/v1/websocket_routes.py` with endpoint:
  ```
  @router.websocket("/item-live-updates")
  async def websocket_item_live_updates(websocket: WebSocket, token: str = Query(...)):
      # 1. Validate token (reuse auth from core)
      # 2. Extract user_id, branch_id, role
      # 3. Manager.connect(...)
      # 4. Send initial handshake: { "status": "connected", "conn_id": "...", "server_time": "..." }
      # 5. Enter message loop:
      #    - On "ping" → send "pong" + server_time
      #    - On "subscribe" → update conn metadata
      #    - On "unsubscribe" → update conn metadata
      # 6. On disconnect → Manager.disconnect(...)
  ```
- [ ] Handshake payload:
  ```json
  {
    "type": "connection_established",
    "connection_id": "conn_abc123",
    "server_time": "2026-04-19T10:00:00Z",
    "subscribed_events": ["item_status_changed", "rental_settlement_finished"],
    "message_size_limit_kb": 64
  }
  ```
- [ ] Heartbeat logic:
  - Server sends `{"type": "ping", "timestamp": "..."}` every 30s
  - Client expected to respond with `{"type": "pong"}` (tracked for liveness)
  - After 3 missed pongs (90s), close connection
- [ ] Error handling:
  - Invalid token → close with code 4001
  - Unauthorized scope (branch mismatch) → close with code 4003
  - Connection already active for user → close old, accept new
  - Any unhandled exception → log + close gracefully

**Exit criteria**:

- [ ] Can connect with valid token
- [ ] Invalid token rejected
- [ ] Heartbeat exchanges work
- [ ] Reconnect after intentional disconnect works

---

#### 5.0.3 Frontend: WebSocket Client Manager

**Owner**: Frontend Lead  
**Dependencies**: None (can develop in parallel)

**Tasks**:

- [ ] Create `frontend/src/services/ws-manager.ts`:
  - Class `WebSocketManager`:
    - `connect(serverUrl, token, options)` → establish connection
    - `disconnect()` → close cleanly
    - `on(eventType, handler)` → register event listener
    - `off(eventType, handler)` → remove listener
    - `emit(message)` → send to server
    - Private: `_handleReconnect()` with exponential backoff (base 1s, max 32s, max 10 attempts)
    - Private: `_heartbeat()` loop (send pong every 30s, timeout if no ping for 60s)
  - Error scenarios:
    - Connection refused → pause, then exponential backoff
    - Token expired mid-session → close, require re-login
    - Network timeout → attempt reconnect
    - Message parse error → log, continue (don't crash)
- [ ] Create `frontend/src/composables/useWebSocket.ts`:
  - Provide reactive interface:
    - `isConnected: Ref<boolean>`
    - `connectionStatus: Ref<'disconnected' | 'connecting' | 'connected' | 'reconnecting' | 'error'>`
    - `lastError: Ref<string | null>`
    - `connect(token)`, `disconnect()`, `subscribe(events)`, `unsubscribe(events)`
    - `on(eventType, handler)` with auto-cleanup on unmount
  - Integrate with Pinia store for app-wide state
- [ ] TypeScript types:
  ```typescript
  type WSMessage =
    | { type: 'connection_established'; connection_id: string; ... }
    | { type: 'item_status_changed'; item_id: string; old_status: string; new_status: string; ... }
    | { type: 'rental_settlement_finished'; settlement_id: string; ... }
    | { type: 'ping'; timestamp: string }
    | { type: 'pong'; timestamp: string };
  ```

**Exit criteria**:

- [ ] Can connect to mock WS server
- [ ] Reconnect logic works in simulation
- [ ] Heartbeat exchanges verified
- [ ] Event listeners fire correctly

---

### PHASE 5.1: Event Publishing Infrastructure (2-3 hours)

#### 5.1.1 Backend: EventPublisher Service

**Owner**: Backend Lead  
**Dependencies**: 5.0.1

**Tasks**:

- [ ] Create `backend/app/services/event_publisher.py`:
  - Class `EventPublisher` (singleton via FastAPI app.state):
    - Inject `WebSocketConnectionManager`
    - `publish_item_status_changed(item_id, old_status, new_status, source_api, changed_by, changed_at, branch_id)`:
      - Serialize payload
      - Throttle (max 1 per 300ms per item_id)
      - Broadcast to connections where `role in ['cashier', 'manager', 'owner'] AND branch_id matches OR role == 'owner'`
      - Log event
    - `publish_rental_settlement_finished(settlement_data, branch_id)`:
      - Serialize payload
      - Throttle (max 1 per 200ms per settlement_id)
      - Broadcast similarly
      - Log event
    - Throttling logic:
      - Maintain `Dict[str, (last_event_time, pending_event)]` per event_type+id
      - Use asyncio task to debounce: collect events in window, send best version
  - Error handling:
    - Failed broadcast to individual connection → log, don't crash
    - Throttling overflow → drop oldest, keep newest
- [ ] Integration point in app startup:
  - Create EventPublisher instance on app startup
  - Store in `app.state.event_publisher`
  - Inject into API endpoints via dependency

**Exit criteria**:

- [ ] Singleton pattern verified (same instance across requests)
- [ ] Throttling verified (can't exceed rate limit per item)
- [ ] Broadcasting filters correctly by role/branch
- [ ] No event loss under normal load (< 100 QPS)

---

#### 5.1.2 Backend: Emit Events from Phase 3 APIs

**Owner**: Backend Lead + API Owners  
**Dependencies**: 5.1.1

**Tasks**:

- [ ] Update `POST /api/v1/inventory/reserve-item`:
  - After successful reserve (status changed to RESERVED):
    ```python
    await event_publisher.publish_item_status_changed(
        item_id=item.id,
        old_status=Item.Status.AVAILABLE,
        new_status=Item.Status.RESERVED,
        source_api="inventory_reserve_item_v1",
        changed_by=current_user.id,
        changed_at=datetime.utcnow().isoformat(),
        branch_id=current_user.branch_id
    )
    ```
- [ ] Update `POST /api/v1/pos/orders`:
  - After order items reserved, emit item_status_changed events
- [ ] Update `POST /api/v1/rentals/contracts`:
  - After contract items reserved, emit item_status_changed events
- [ ] Update `POST /api/v1/rentals/return-items` (CRITICAL):
  - After each item returned (status changed to RETURNED):
    - Emit item_status_changed
  - After settlement completed:
    - Emit rental_settlement_finished with settlement data

**Validation**:

- [ ] Each API endpoint that mutates item status → triggers event
- [ ] Event payload matches spec (all required fields)
- [ ] Backwards compatibility: no breaking changes to API response
- [ ] Idempotency: replaying same request → emit event only once (rely on DB idempotency key)

**Exit criteria**:

- [ ] All critical paths (POS, Rental, Return) emit events
- [ ] No event duplication under idempotency replay
- [ ] Event metadata (branch_id, changed_by) correctly populated

---

### PHASE 5.2: Frontend Event Handling & UI Integration (2-3 hours)

#### 5.2.1 Frontend: Event Handler Store (Pinia)

**Owner**: Frontend Lead  
**Dependencies**: 5.0.3, 5.1.1

**Tasks**:

- [ ] Create `frontend/src/stores/realtimeEvents.ts`:
  - Pinia store to centralize event handling:
    - `connectionState: { status, lastConnectedAt, connectionError }`
    - `itemStatusUpdates: Map<string, ItemStatusEvent>` (cache latest 50)
    - `settlementUpdates: Map<string, SettlementEvent>` (cache latest 50)
    - `lastUpdateTimestamps` for deduplication
  - Actions:
    - `handleItemStatusChanged(event)`: update cache, emit to subscribers
    - `handleRentalSettlementFinished(event)`: update cache, emit to subscribers
    - `clearCache()`
  - Getters:
    - `getItemStatus(itemId)` → latest status from cache
    - `getSettlement(contractId)` → latest settlement from cache
- [ ] Create reactive composables for UI:
  - `useItemStatus(itemId)`: return reactive item status + last_update
  - `useSettlement(contractId)`: return reactive settlement + last_update
- [ ] Deduplication logic:
  - Per event: check `event_id` (from backend) against recent events
  - Drop duplicate if received within 500ms window

**Exit criteria**:

- [ ] Store can be populated from mock events
- [ ] Composables return reactive data
- [ ] Deduplication works

---

#### 5.2.2 Frontend: POS Screen Integration

**Owner**: Frontend Lead (POS Owner)  
**Dependencies**: 5.2.1

**Tasks**:

- [ ] On POS checkout screen mount:
  - `useWebSocket().subscribe(['item_status_changed'])`
  - On item_status_changed for current order items:
    - If item status changes to UNAVAILABLE/RETURNED → show warning toast
    - If item quantity reduced → update cart automatically
    - If item becomes unavailable → mark in cart with strikethrough + disable checkout
- [ ] Visual indicators:
  - Icon badge on cart showing "1 item updated" with timestamp
  - Option to "Reload order from backend" if conflict detected
  - Toast notification: "Item [barcode] status changed to [new_status]"
- [ ] UX flow:
  - Minor update (status changed but item still available) → silent update + badge
  - Major conflict (item unavailable) → show confirmation dialog, allow user to remove item or abort checkout

**Exit criteria**:

- [ ] Live item updates work in POS screen
- [ ] Conflicts handled gracefully without losing user input
- [ ] No race conditions between user input and incoming events

---

#### 5.2.3 Frontend: Rental Return Screen Integration

**Owner**: Frontend Lead (Rental Owner)  
**Dependencies**: 5.2.1

**Tasks**:

- [ ] On Rental return screen mount:
  - `useWebSocket().subscribe(['item_status_changed', 'rental_settlement_finished'])`
  - On rental_settlement_finished for current contract:
    - Update settlement display: total_fee, refund_to_customer, remaining_debt
    - Update status badge to "Settled" (green)
    - Show success animation
    - Enable "Print receipt" button (if not already enabled)
- [ ] On item_status_changed for items in return list:
  - Update item status in list
  - Recalculate return progress
- [ ] Visual indicators:
  - Settlement card shows "Updating..." spinner while pending
  - On settlement complete: show calculated fees in real-time before user action
  - Toast: "Settlement completed: Refund $[X], Remaining debt $[Y]"

**Exit criteria**:

- [ ] Settlement updates appear in UI within 1s of backend event
- [ ] Return flow doesn't require manual refresh
- [ ] Item status changes reflected in list

---

### PHASE 5.3: Connection Resilience & Fallback (1-2 hours)

#### 5.3.1 Backend: Connection Health & Cleanup

**Owner**: Backend Lead  
**Dependencies**: 5.0.2

**Tasks**:

- [ ] Implement stale connection cleanup:
  - Background task (every 60s): scan connections without pong response in 90s
  - Force close stale connections
  - Log closure reason
- [ ] Connection limit enforcement:
  - If active connections >= 300, reject new connections with error 429
  - Return retry-after header
- [ ] Graceful shutdown:
  - On app shutdown: send `{ type: "server_shutdown", message: "..." }` to all connections
  - Wait 2s for clients to acknowledge
  - Force close remaining

**Exit criteria**:

- [ ] Stale connections cleaned up properly
- [ ] Connection limit enforced
- [ ] Shutdown doesn't lose in-flight events

---

#### 5.3.2 Frontend: Fallback Polling

**Owner**: Frontend Lead  
**Dependencies**: 5.2.1

**Tasks**:

- [ ] Implement light polling when WebSocket unavailable:
  - Polling triggered when:
    - WebSocket fails to connect after 5s
    - Disconnected for > 30s
  - Polling endpoints (add to backend if not exist):
    - `GET /api/v1/inventory/items/{item_id}/status` → return current status + changed_at
    - `GET /api/v1/rentals/contracts/{contract_id}/settlement` → return settlement data
  - Polling frequency:
    - First 30s: every 5s
    - After 30s: every 10s
    - After 2m: every 30s
  - Stop polling when WebSocket reconnects
- [ ] Polling integration:
  - In realtimeEvents store:
    - `startFallbackPolling(itemIds, contractIds)`
    - `stopFallbackPolling()`
  - POS & Rental screens call start/stop on mount/unmount
  - Merge polling updates with WS updates (use timestamp to pick latest)

**Exit criteria**:

- [ ] Polling works as fallback
- [ ] No duplicate data merging artifacts
- [ ] Polling stops when WS reconnects

---

### PHASE 5.4: Testing & Validation (1-2 hours)

#### 5.4.1 Backend: Unit & Integration Tests

**Owner**: Backend Lead  
**Dependencies**: All Phase 5.0-5.3 backend tasks

**Tasks**:

- [ ] Create `backend/tests/test_websocket_manager.py`:
  - Test concurrent connections
  - Test broadcasting with filters (role, branch)
  - Test connection cleanup
  - Test 300+ connection limit
- [ ] Create `backend/tests/test_event_publisher.py`:
  - Test event serialization
  - Test throttling (max 1 event per 300ms)
  - Test no event loss under 100 QPS
  - Test subscription filtering
- [ ] Create `backend/tests/test_websocket_endpoint.py`:
  - Test auth (valid/invalid/expired tokens)
  - Test handshake payload
  - Test heartbeat exchange
  - Test subscribe/unsubscribe commands
  - Test message parsing error handling
- [ ] Create `backend/tests/test_event_emission.py`:
  - Test item_status_changed emitted from inventory APIs
  - Test rental_settlement_finished emitted from rental return API
  - Verify event payloads match spec
- [ ] Integration test:
  - Simulate concurrent POS + Rental operations
  - Verify events broadcast correctly to subscribed clients

**Exit criteria**:

- [ ] 95%+ code coverage for WebSocket components
- [ ] All critical paths tested
- [ ] Load test: 300 concurrent connections, 10 events/s → no message loss

---

#### 5.4.2 Frontend: Component & Integration Tests

**Owner**: Frontend Lead  
**Dependencies**: All Phase 5.2 frontend tasks

**Tasks**:

- [ ] Create `frontend/src/__tests__/ws-manager.spec.ts`:
  - Test connect/disconnect
  - Test reconnect backoff
  - Test heartbeat exchanges
  - Test event listeners
- [ ] Create `frontend/src/__tests__/realtimeEvents.store.spec.ts`:
  - Test event handler logic
  - Test deduplication
  - Test cache limits
- [ ] Create `frontend/src/__tests__/useItemStatus.spec.ts`:
  - Test reactive updates
  - Test deduplication in UI
- [ ] Create e2e tests (with mock backend):
  - POS screen receives item_status_changed → UI updates ✓
  - Rental return screen receives rental_settlement_finished → UI updates ✓
  - Fallback polling activates when WS down ✓
  - Reconnect works without data loss ✓

**Exit criteria**:

- [ ] 90%+ code coverage for frontend WebSocket logic
- [ ] E2E scenarios all pass
- [ ] UI renders updates within 500ms of event receipt

---

#### 5.4.3 Manual Testing & Load Testing

**Owner**: QA + Backend Lead  
**Dependencies**: All Phase 5 tasks

**Tasks**:

- [ ] Manual test scenarios:
  - [ ] Open POS + Rental return in two windows
  - [ ] Trigger inventory reserve in one → verify POS sees update immediately
  - [ ] Return items in one window → verify settlement shows in other
  - [ ] Kill backend server → verify frontend gracefully degrades, shows error
  - [ ] Restart backend → verify automatic reconnect
  - [ ] Disconnect network → verify fallback polling starts
  - [ ] Reconnect network → verify WS recovers, polling stops
- [ ] Load test:
  - [ ] Simulate 50 concurrent users, each polling different items
  - [ ] Measure: event latency (server-to-client), memory usage, CPU
  - [ ] Verify: no msg loss, < 1s latency, < 500MB memory for 300 connections
- [ ] Stress test:
  - [ ] Burst: 100 item_status_changed events within 1s
  - [ ] Verify: throttling kicks in, no queue overflow
  - [ ] Measure: recovery time back to normal

**Exit criteria**:

- [ ] All manual test scenarios pass
- [ ] Event latency < 500ms p99
- [ ] No message loss under load
- [ ] Memory stable (no leak)

---

### PHASE 5.5: Documentation & Deployment (1 hour)

#### 5.5.1 Documentation

**Owner**: Tech Lead  
**Dependencies**: All Phase 5 tasks completed

**Tasks**:

- [ ] Create `docs/realtime/implementation_websocket.md`:
  - Architecture diagram
  - Connection lifecycle
  - Event flow diagrams
  - Throttling logic
  - Error handling strategy
  - Performance notes (latency, throughput)
- [ ] Update `docs/api-reference/v1/websocket.md`:
  - Endpoint spec: `/ws/item-live-updates`
  - Message types and payloads
  - Example client code
- [ ] Add to `docs/how-to/howto_development-environment-setup.md`:
  - WebSocket testing with wscat or similar tool
  - Mock server for local testing
- [ ] Create runbook:
  - `docs/how-to/runbook_websocket-troubleshooting.md`
  - Common issues: connection drops, message loss, memory leak
  - Debug commands and logs to check

**Exit criteria**:

- [ ] Developer can understand and debug WS system from docs
- [ ] Operational guide for monitoring in production

---

#### 5.5.2 Deployment Checklist

**Owner**: DevOps + Backend Lead  
**Dependencies**: All Phase 5 tasks

**Tasks**:

- [ ] Code quality gate:
  - [ ] Ruff passes (linting)
  - [ ] mypy passes (type checking)
  - [ ] pytest passes (unit + integration tests)
  - [ ] 95%+ coverage for WebSocket code
- [ ] Performance baseline established:
  - [ ] Event latency: < 500ms p99
  - [ ] Connection limit: 300 max
  - [ ] Memory per connection: < 1.5MB
- [ ] Monitoring setup:
  - [ ] Prometheus metrics:
    - `ws_connections_active` (gauge)
    - `ws_events_published_total` (counter by event_type)
    - `ws_event_latency_ms` (histogram)
    - `ws_broadcast_failures_total` (counter)
  - [ ] Logging: structured logs for connect/disconnect/errors
  - [ ] Alerts: connections > 250, event latency > 1s, broadcast failures > 1%
- [ ] Staging deployment:
  - [ ] Deploy to staging environment
  - [ ] Run load test against staging
  - [ ] Verify no regressions in existing APIs (Phase 1-4)
  - [ ] Monitor for 24h

**Exit criteria**:

- [ ] All code quality gates pass
- [ ] Performance baseline documented
- [ ] Monitoring & alerting in place
- [ ] Staging validation complete

---

## 📊 Dependency Graph & Sequencing

```
5.0.1 (Backend Connection Manager)
    ↓
5.0.2 (Backend WebSocket Endpoint) ←─→ 5.0.3 (Frontend WS Client) [parallel]
    ↓                                      ↓
5.1.1 (Backend EventPublisher)       5.2.1 (Frontend Event Store)
    ↓                                      ↓
5.1.2 (Backend Emit Events) ←──────────→ 5.2.2 (POS Integration)
    ↓                                      ↓
5.3.1 (Backend Resilience) ←──────────→ 5.2.3 (Rental Integration)
    ↓                                      ↓
5.3.2 (Frontend Fallback Polling)   5.3.2 (Frontend Fallback Polling)
    ↓                                      ↓
5.4.1 (Backend Tests) ←──────────────→ 5.4.2 (Frontend Tests)
    ↓
5.4.3 (Manual + Load Testing)
    ↓
5.5.1 (Documentation)
    ↓
5.5.2 (Deployment Checklist)
```

**Critical Path**: 5.0.1 → 5.0.2 → 5.1.1 → 5.1.2 → 5.4.1 → 5.4.3 → 5.5.2 (8-9 hours)  
**Parallel Work**: Frontend (5.0.3 → 5.2.x) can happen alongside backend (4-5 hours)

---

## ⏰ Recommended Timeline

**Day 1 (4 hours)**:

- Morning: 5.0.1 + 5.0.2 (Backend WS foundation)
- Parallel: 5.0.3 (Frontend WS client)
- Afternoon: 5.1.1 + 5.1.2 (Event publishing)

**Day 2 (4 hours)**:

- Morning: 5.2.1 + 5.2.2 + 5.2.3 (Frontend integration)
- Parallel: 5.3.1 + 5.3.2 (Resilience)
- Afternoon: 5.4.1 + 5.4.2 (Testing)

**Day 2.5 (optional, if needed)**:

- Manual testing, load testing, troubleshooting
- Documentation + deployment checklist

---

## 🚨 Risk Mitigation

| Risk                                                                | Mitigation                                                                        |
| ------------------------------------------------------------------- | --------------------------------------------------------------------------------- |
| **Event storm** (100+ events/s overwhelming clients)                | Implement throttling (300ms/200ms per event_type+id); queue + debounce in service |
| **Memory leak** (connections not cleaned up)                        | Implement heartbeat-based cleanup; monitor memory under load                      |
| **Broadcast failures** (some clients miss events)                   | Implement retry logic for failed broadcasts; log failures for debugging           |
| **Frontend reconnect loop** (connect → fail → reconnect infinitely) | Exponential backoff + max 10 attempts; fallback to polling                        |
| **Token expiry during session**                                     | Catch 401 in WS layer; trigger re-login UI; close connection gracefully           |
| **Stale item/settlement data** (old event arrives after new)        | Use timestamp comparison; always prefer newer event (by changed_at)               |

---

## ✅ Definition of Done

**For Phase 5 to be considered complete**:

1. ✅ All 5 code components (Backend WS, EventPublisher, Frontend WS, Event Store, Integration) tested and merged
2. ✅ All manual test scenarios pass (see 5.4.3)
3. ✅ Load test: 300 concurrent, 10 events/s, < 500ms latency, no msg loss
4. ✅ Code coverage ≥ 95% for WebSocket; ≥ 90% for integration
5. ✅ Documentation complete (architecture, runbook, deployment)
6. ✅ Monitoring & alerts configured in staging
7. ✅ No breaking changes to Phase 1-4 APIs
8. ✅ Phase 3 hardening tests still pass (backward compatibility)

---

## 📚 References

- Spec: `docs/realtime/realtime_item-live-updates.yaml`
- Event specs: `docs/events/event_item-status-changed.yaml`, `docs/events/event_rental-settled.yaml`
- Frontend contracts: `docs/ui-contracts/ui_pos-main-kiosk.yaml`, `docs/ui-contracts/ui_rental-return-inspection.yaml`
- Phase 3 notes: `/memories/repo/phase3-implementation-notes.md`
