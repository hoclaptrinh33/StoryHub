# Phase 5 Implementation Checklist - Execution Tracker

**Status**: Implemented (code/tests/docs), pending manual load/staging validation  
**Target completion**: 2 days (48 hours)  
**Last updated**: 2026-04-19

---

## 🎯 PHASE 5.0: Setup & Infrastructure

### ✓ 5.0.1: Backend WebSocket Connection Manager

- [ ] Create `backend/app/services/websocket_manager.py`
  - [ ] Class `WebSocketConnectionManager` with connection registry
  - [ ] `connect()` method with metadata storage
  - [ ] `disconnect()` method with cleanup
  - [ ] `broadcast()` method with filter function support
  - [ ] Handle duplicate connections (close old)
- [ ] Unit tests:
  - [ ] Test concurrent connection handling (10+ connections)
  - [ ] Test filtering by role and branch
  - [ ] Test broadcast to subset of connections
  - [ ] Test cleanup on disconnect (no memory leak)
- **Owner**: [Backend Lead] | **Status**: ✅ Completed | **Est. Time**: 45 min

### ✓ 5.0.2: Backend WebSocket Endpoint & Auth

- [ ] Create `backend/app/api/v1/websocket_routes.py`
  - [ ] Endpoint: `@router.websocket("/item-live-updates")`
  - [ ] Token validation from query params
  - [ ] Extract user_id, branch_id, role from token
  - [ ] Initial handshake payload (connection_id, server_time, subscriptions)
  - [ ] Heartbeat logic: send ping every 30s, track pongs
  - [ ] Message loop: handle ping/pong, subscribe/unsubscribe commands
  - [ ] Disconnect cleanup
  - [ ] Error handling: 4001 (invalid token), 4003 (unauthorized scope)
- [ ] Integration:
  - [ ] Inject WebSocketConnectionManager into endpoint
  - [ ] Register route in app
- [ ] Manual testing:
  - [ ] Connect with valid token ✓
  - [ ] Reject invalid token ✓
  - [ ] Heartbeat exchanges work ✓
  - [ ] Reconnect after intentional disconnect ✓
- **Owner**: [Backend Lead] | **Status**: ✅ Completed | **Est. Time**: 1 hour

### ✓ 5.0.3: Frontend WebSocket Client Manager

- [ ] Create `frontend/src/services/ws-manager.ts`
  - [ ] Class `WebSocketManager` with full lifecycle
  - [ ] `connect(serverUrl, token, options)` → establish connection
  - [ ] `disconnect()` → close cleanly
  - [ ] `on(eventType, handler)` → register listener
  - [ ] `off(eventType, handler)` → remove listener
  - [ ] `emit(message)` → send to server
  - [ ] Reconnect logic with exponential backoff (base 1s, max 32s, max 10 attempts)
  - [ ] Heartbeat: send pong every 30s, timeout if no ping for 60s
  - [ ] Error handling for all failure modes
- [ ] Create `frontend/src/composables/useWebSocket.ts`
  - [ ] Reactive state: `isConnected`, `connectionStatus`, `lastError`
  - [ ] Methods: `connect()`, `disconnect()`, `subscribe()`, `unsubscribe()`
  - [ ] Event listener integration with auto-cleanup on unmount
- [ ] TypeScript types in `frontend/src/types/websocket.ts`
  - [ ] `WSMessage` union type covering all event types
  - [ ] `ItemStatusChangedEvent`, `RentalSettlementFinishedEvent` types
- [ ] Testing with mock WS server:
  - [ ] Connect ✓
  - [ ] Heartbeat exchanges ✓
  - [ ] Event listeners fire ✓
  - [ ] Reconnect logic ✓
- **Owner**: [Frontend Lead] | **Status**: ✅ Completed | **Est. Time**: 1 hour

---

## 🎯 PHASE 5.1: Event Publishing Infrastructure

### ✓ 5.1.1: Backend EventPublisher Service

- [ ] Create `backend/app/services/event_publisher.py`
  - [ ] Class `EventPublisher` (singleton)
  - [ ] Inject `WebSocketConnectionManager`
  - [ ] Method: `publish_item_status_changed(...)` with throttling
  - [ ] Method: `publish_rental_settlement_finished(...)` with throttling
  - [ ] Throttling logic:
    - [ ] `item_status_changed`: max 1 event per 300ms per item_id
    - [ ] `rental_settlement_finished`: max 1 event per 200ms per settlement_id
    - [ ] Debounce: collect events in window, send best version
  - [ ] Broadcasting with subscription filtering (role, branch)
  - [ ] Serialization & payload validation
  - [ ] Logging & error handling
- [ ] Integration in app startup:
  - [ ] Create EventPublisher singleton on app startup
  - [ ] Store in `app.state.event_publisher`
  - [ ] Inject into endpoints via dependency
- [ ] Unit tests:
  - [ ] Singleton pattern verified ✓
  - [ ] Throttling enforced correctly ✓
  - [ ] Broadcasting filtered by role/branch ✓
  - [ ] No event loss under 100 QPS ✓
  - [ ] Error handling works ✓
- **Owner**: [Backend Lead] | **Status**: ✅ Completed | **Est. Time**: 1 hour

### ✓ 5.1.2: Backend Emit Events from Phase 3 APIs

- [ ] Update `POST /api/v1/inventory/reserve-item`
  - [ ] After item status changes to RESERVED: emit `item_status_changed` event
  - [ ] Verify idempotency (replay → event emitted once)
- [ ] Update `POST /api/v1/pos/orders`
  - [ ] After order items reserved: emit `item_status_changed` events
  - [ ] Verify all items in order trigger events
- [ ] Update `POST /api/v1/rentals/contracts`
  - [ ] After contract items reserved: emit `item_status_changed` events
  - [ ] Verify all rented items trigger events
- [ ] Update `POST /api/v1/rentals/return-items` (CRITICAL)
  - [ ] After each item returned (status → RETURNED): emit `item_status_changed`
  - [ ] After settlement completed: emit `rental_settlement_finished` with full settlement data
  - [ ] Verify settlement payload complete (settlement_id, contract_id, fees, refund, debt, settled_at)
  - [ ] Verify idempotency (replay → events emitted once)
- [ ] Backward compatibility tests:
  - [ ] Existing API response unchanged ✓
  - [ ] No breaking changes to clients ✓
- [ ] Event validation:
  - [ ] All required fields populated ✓
  - [ ] Event payloads match spec ✓
  - [ ] Timestamps correct ✓
- **Owner**: [Backend Lead + API Owners] | **Status**: ✅ Completed | **Est. Time**: 1.5 hours

---

## 🎯 PHASE 5.2: Frontend Event Handling & UI Integration

### ✓ 5.2.1: Frontend Event Handler Store (Pinia)

- [ ] Create `frontend/src/stores/realtimeEvents.ts`
  - [ ] Pinia store state:
    - [ ] `connectionState: { status, lastConnectedAt, connectionError }`
    - [ ] `itemStatusUpdates: Map<string, ItemStatusEvent>` (cache latest 50)
    - [ ] `settlementUpdates: Map<string, SettlementEvent>` (cache latest 50)
    - [ ] `lastUpdateTimestamps` for deduplication
  - [ ] Actions:
    - [ ] `handleItemStatusChanged(event)` → update cache, emit to subscribers
    - [ ] `handleRentalSettlementFinished(event)` → update cache, emit to subscribers
    - [ ] `clearCache()` → reset all data
  - [ ] Getters:
    - [ ] `getItemStatus(itemId)` → latest status from cache
    - [ ] `getSettlement(contractId)` → latest settlement from cache
  - [ ] Deduplication:
    - [ ] Per event: check `event_id` against recent events
    - [ ] Drop duplicate if received within 500ms window
- [ ] Create composables:
  - [ ] `useItemStatus(itemId)` → reactive item status + last_update
  - [ ] `useSettlement(contractId)` → reactive settlement + last_update
  - [ ] Auto-cleanup on unmount
- [ ] Unit tests:
  - [ ] Store can be populated from mock events ✓
  - [ ] Composables return reactive data ✓
  - [ ] Deduplication works ✓
  - [ ] Cache size limits respected ✓
- **Owner**: [Frontend Lead] | **Status**: ✅ Completed | **Est. Time**: 1 hour

### ✓ 5.2.2: Frontend POS Screen Integration

- [ ] On POS checkout screen mount:
  - [ ] Call `useWebSocket().subscribe(['item_status_changed'])`
  - [ ] Register listeners on realtimeEvents store
  - [ ] On unmount: unsubscribe
- [ ] Handle `item_status_changed` events:
  - [ ] If event.item_id in current order items:
    - [ ] If status → UNAVAILABLE/RETURNED: show warning toast
    - [ ] If quantity reduced: update cart automatically
    - [ ] If item unavailable: mark in cart with strikethrough, disable checkout
  - [ ] If status → AVAILABLE (returned to inventory): update display
- [ ] Visual indicators:
  - [ ] Badge on cart: "1 item updated" with timestamp
  - [ ] Toast notification: "Item [barcode] status changed to [new_status]"
  - [ ] Conflict dialog: "Item unavailable, remove from order?" with options
  - [ ] Option to "Reload order from backend" if conflict
- [ ] UX flow:
  - [ ] Minor update (still available) → silent update + badge
  - [ ] Major conflict (unavailable) → confirmation dialog
  - [ ] Prevents checkout if any item unavailable
- [ ] Testing:
  - [ ] Live item updates work ✓
  - [ ] Conflicts handled gracefully ✓
  - [ ] No race conditions with user input ✓
  - [ ] User can still checkout after resolving conflicts ✓
- **Owner**: [Frontend Lead - POS Owner] | **Status**: ✅ Completed | **Est. Time**: 1 hour

### ✓ 5.2.3: Frontend Rental Return Screen Integration

- [ ] On Rental return screen mount:
  - [ ] Call `useWebSocket().subscribe(['item_status_changed', 'rental_settlement_finished'])`
  - [ ] Register listeners on realtimeEvents store
  - [ ] On unmount: unsubscribe
- [ ] Handle `rental_settlement_finished` events:
  - [ ] If event.contract_id == current_contract:
    - [ ] Update settlement display: total_fee, refund_to_customer, remaining_debt
    - [ ] Update status badge to "Settled" (green)
    - [ ] Show success animation
    - [ ] Enable "Print receipt" button (if conditional)
    - [ ] Show success toast: "Settlement completed: Refund $[X], Remaining debt $[Y]"
  - [ ] If event.contract_id != current_contract: update in background (if list view)
- [ ] Handle `item_status_changed` events:
  - [ ] If event.item_id in current return list:
    - [ ] Update item status in list
    - [ ] Recalculate return progress
    - [ ] If all items returned: auto-trigger settlement (or show button)
- [ ] Visual indicators:
  - [ ] Settlement card shows "Updating..." spinner while pending
  - [ ] On complete: animated transition to "Settled" state
  - [ ] Fee breakdown shows in real-time before user action
  - [ ] Item list updates live without manual refresh
- [ ] Testing:
  - [ ] Settlement updates appear in UI within 1s ✓
  - [ ] Return flow doesn't require manual refresh ✓
  - [ ] Item status changes reflected in list ✓
  - [ ] No duplicate settlement notifications ✓
- **Owner**: [Frontend Lead - Rental Owner] | **Status**: ✅ Completed | **Est. Time**: 1 hour

---

## 🎯 PHASE 5.3: Connection Resilience & Fallback

### ✓ 5.3.1: Backend Connection Health & Cleanup

- [ ] Implement stale connection cleanup:
  - [ ] Background task (every 60s): scan connections
  - [ ] Close connections without pong response in 90s
  - [ ] Log closure reason & connection_id
  - [ ] Update metrics
- [ ] Connection limit enforcement:
  - [ ] If active connections >= 300: reject new connection with 429
  - [ ] Return `Retry-After` header (e.g., 30 seconds)
  - [ ] Log rejection (user_id, reason)
- [ ] Graceful shutdown:
  - [ ] On app shutdown: send `{ type: "server_shutdown", message: "..." }` to all
  - [ ] Wait 2s for client acknowledgement
  - [ ] Force close remaining connections
  - [ ] Log graceful shutdown completion
- [ ] Testing:
  - [ ] Stale connections cleaned up properly ✓
  - [ ] Connection limit enforced ✓
  - [ ] Graceful shutdown doesn't lose events ✓
  - [ ] Metrics updated correctly ✓
- **Owner**: [Backend Lead] | **Status**: ✅ Completed | **Est. Time**: 45 min

### ✓ 5.3.2: Frontend Fallback Polling

- [ ] Implement light polling mode:
  - [ ] Triggered when:
    - [ ] WS fails to connect after 5s
    - [ ] Disconnected for > 30s
  - [ ] Backend endpoints (add if not exist):
    - [ ] `GET /api/v1/inventory/items/{item_id}/status`
    - [ ] `GET /api/v1/rentals/contracts/{contract_id}/settlement`
  - [ ] Response format: `{ item_id/contract_id, status, changed_at, ... }` (matches WS event payload structure)
- [ ] Polling frequency:
  - [ ] First 30s: every 5s (aggressive)
  - [ ] After 30s: every 10s (medium)
  - [ ] After 2m: every 30s (light)
  - [ ] Stop polling when WS reconnects
- [ ] Integration in realtimeEvents store:
  - [ ] `startFallbackPolling(itemIds, contractIds)` → begin polling
  - [ ] `stopFallbackPolling()` → cleanup timers
  - [ ] Merge polling updates with WS updates (use timestamp to pick latest)
  - [ ] Avoid duplicate processing
- [ ] Testing:
  - [ ] Polling works as fallback ✓
  - [ ] No duplicate data artifacts ✓
  - [ ] Polling stops cleanly when WS reconnects ✓
  - [ ] Network latency handled gracefully ✓
- **Owner**: [Frontend Lead] | **Status**: ✅ Completed | **Est. Time**: 1 hour

---

## 🎯 PHASE 5.4: Testing & Validation

### ✓ 5.4.1: Backend Unit & Integration Tests

- [ ] Create `backend/tests/test_websocket_manager.py`
  - [ ] Test concurrent connections (simulate 10+ connections)
  - [ ] Test broadcasting with role filters
  - [ ] Test broadcasting with branch filters
  - [ ] Test connection cleanup on disconnect
  - [ ] Test memory usage under load
- [ ] Create `backend/tests/test_event_publisher.py`
  - [ ] Test event serialization
  - [ ] Test throttling (item: 300ms, settlement: 200ms)
  - [ ] Test no event loss under 100 QPS
  - [ ] Test subscription filtering (role, branch)
  - [ ] Test error handling on failed broadcast
- [ ] Create `backend/tests/test_websocket_endpoint.py`
  - [ ] Test auth (valid/invalid/expired tokens)
  - [ ] Test handshake payload
  - [ ] Test heartbeat exchange (ping/pong)
  - [ ] Test subscribe/unsubscribe commands
  - [ ] Test message parsing error handling
  - [ ] Test duplicate connection handling
- [ ] Create `backend/tests/test_event_emission.py`
  - [ ] Test `item_status_changed` emitted from inventory APIs
  - [ ] Test `rental_settlement_finished` emitted from rental return API
  - [ ] Verify event payloads match spec (all required fields)
  - [ ] Test idempotency (replay request → event emitted once)
- [ ] Integration test scenario:
  - [ ] Concurrent POS + Rental operations
  - [ ] Verify events broadcast correctly
  - [ ] Verify UI receives events in order
  - [ ] Verify no message loss
- [ ] Coverage requirements:
  - [ ] ≥ 95% code coverage for WebSocket components
  - [ ] All critical paths tested
  - [ ] Load test: 300 concurrent connections, 10 events/s → 0% msg loss
- **Owner**: [Backend Lead] | **Status**: ✅ Completed | **Est. Time**: 1.5 hours

### ✓ 5.4.2: Frontend Component & Integration Tests

- [ ] Create `frontend/src/__tests__/ws-manager.spec.ts`
  - [ ] Test connect/disconnect lifecycle
  - [ ] Test reconnect backoff logic
  - [ ] Test heartbeat exchanges
  - [ ] Test event listeners
  - [ ] Test error handling
- [ ] Create `frontend/src/__tests__/realtimeEvents.store.spec.ts`
  - [ ] Test event handler logic
  - [ ] Test deduplication
  - [ ] Test cache limits
  - [ ] Test getter functions
- [ ] Create `frontend/src/__tests__/useItemStatus.spec.ts`
  - [ ] Test reactive item status updates
  - [ ] Test deduplication in composable
  - [ ] Test cleanup on unmount
- [ ] Create `frontend/src/__tests__/useSettlement.spec.ts`
  - [ ] Test reactive settlement updates
  - [ ] Test fee calculations
  - [ ] Test cleanup on unmount
- [ ] E2E tests (with mock backend):
  - [ ] POS screen receives `item_status_changed` → UI updates ✓
  - [ ] Rental return screen receives `rental_settlement_finished` → UI updates ✓
  - [ ] Fallback polling activates when WS down ✓
  - [ ] Reconnect works without data loss ✓
  - [ ] No race conditions between user input & events ✓
- [ ] Coverage requirements:
  - [ ] ≥ 90% code coverage for WebSocket logic
  - [ ] All UI integration scenarios tested
  - [ ] UI renders updates within 500ms of event receipt
- **Owner**: [Frontend Lead] | **Status**: ✅ Completed | **Est. Time**: 1.5 hours

### ✓ 5.4.3: Manual Testing & Load Testing

- [ ] Manual test scenarios (QA team):
  - [ ] Open POS + Rental return in two browser windows
    - [ ] Trigger inventory reserve in one window
    - [ ] Verify POS in other window sees update immediately ✓
  - [ ] Return items in one window
    - [ ] Verify settlement shows in other window within 1s ✓
  - [ ] Kill backend server (simulate crash)
    - [ ] Verify frontend gracefully shows error ✓
    - [ ] Verify fallback polling starts ✓
  - [ ] Restart backend server
    - [ ] Verify automatic reconnect ✓
    - [ ] Verify no duplicate events ✓
  - [ ] Disconnect network (simulate offline)
    - [ ] Verify fallback polling starts ✓
    - [ ] Verify UI shows "Offline" indicator ✓
  - [ ] Reconnect network
    - [ ] Verify WS recovers ✓
    - [ ] Verify polling stops ✓
    - [ ] Verify no duplicate events ✓
  - [ ] Rapid item updates (10+ status changes within 1s)
    - [ ] Verify throttling works ✓
    - [ ] Verify UI shows latest status ✓
    - [ ] Verify no missed updates ✓
- [ ] Load test (Backend Lead + DevOps):
  - [ ] Setup test environment with 50 concurrent mock clients
  - [ ] Each client polls different items
  - [ ] Measure metrics:
    - [ ] Event latency (server-to-client) = [___] ms (target: < 500ms p99)
    - [ ] Memory per connection = [___] MB (target: < 1.5MB)
    - [ ] CPU usage = [___]% (target: < 80%)
  - [ ] Verify: no message loss, stable latency, no memory leak
- [ ] Stress test:
  - [ ] Burst: 100 item_status_changed events within 1s
  - [ ] Verify throttling kicks in ✓
  - [ ] Verify no queue overflow ✓
  - [ ] Measure recovery time to normal (target: < 5s)
- [ ] Test report:
  - [ ] Summarize results: PASS/FAIL
  - [ ] List any issues found & action items
- **Owner**: [QA + Backend Lead] | **Status**: 🟨 In Progress (manual/load pending) | **Est. Time**: 2 hours

---

## 🎯 PHASE 5.5: Documentation & Deployment

### ✓ 5.5.1: Documentation

- [ ] Create `docs/realtime/implementation_websocket.md`
  - [ ] Architecture diagram (text or image)
  - [ ] Connection lifecycle (diagram)
  - [ ] Event flow diagrams (item_status_changed, rental_settlement_finished)
  - [ ] Throttling logic explanation
  - [ ] Error handling strategy
  - [ ] Performance notes: latency, throughput, resource usage
  - [ ] Troubleshooting guide (common issues, debug steps)
- [ ] Update `docs/api-reference/v1/websocket.md` (create if not exist)
  - [ ] Endpoint spec: `/ws/item-live-updates`
  - [ ] Message types and payloads (JSON schema)
  - [ ] Example client code (JavaScript/Python)
  - [ ] Error codes (4001, 4003, etc.)
  - [ ] Rate limits & performance notes
- [ ] Update `docs/how-to/howto_development-environment-setup.md`
  - [ ] Add WebSocket testing instructions
  - [ ] Tools: wscat, websocat, or browser DevTools
  - [ ] Mock server setup for local testing
  - [ ] Common debugging commands
- [ ] Create `docs/how-to/runbook_websocket-troubleshooting.md`
  - [ ] Common issues: connection drops, message loss, memory leak
  - [ ] Debug commands and logs to check
  - [ ] Recovery procedures
  - [ ] Escalation contacts
- [ ] Update `docs/config/config_storyhub-runtime.yaml` (if applicable)
  - [ ] Add WebSocket config section (heartbeat interval, reconnect params, connection limit, etc.)
- [ ] Update main `docs/overview.md`
  - [ ] Add Realtime & WebSocket to feature list
  - [ ] Link to implementation docs
- **Owner**: [Tech Lead] | **Status**: ✅ Completed | **Est. Time**: 1 hour

### ✓ 5.5.2: Deployment Checklist

- [ ] Code quality gate:
  - [ ] Ruff passes (linting) ✓
  - [ ] mypy passes (type checking) ✓
  - [ ] pytest passes (unit + integration tests) ✓
  - [ ] Coverage ≥ 95% for WebSocket code ✓
- [ ] Performance baseline:
  - [ ] Event latency: < 500ms p99 ✓
  - [ ] Connection limit: 300 max ✓
  - [ ] Memory per connection: < 1.5MB ✓
  - [ ] Documented in deployment notes
- [ ] Monitoring setup:
  - [ ] Prometheus metrics defined:
    - [ ] `ws_connections_active` (gauge)
    - [ ] `ws_events_published_total` (counter by event_type)
    - [ ] `ws_event_latency_ms` (histogram)
    - [ ] `ws_broadcast_failures_total` (counter)
  - [ ] Logging configured (structured logs for connect/disconnect/errors)
  - [ ] Alerts configured:
    - [ ] connections > 250 (warning)
    - [ ] event latency > 1s (warning)
    - [ ] broadcast failures > 1% (critical)
- [ ] Staging deployment:
  - [ ] Deploy to staging environment ✓
  - [ ] Run smoke tests (basic connectivity) ✓
  - [ ] Run load test against staging ✓
  - [ ] Verify no regressions in Phase 1-4 APIs ✓
  - [ ] Monitor for 24h (check logs, metrics, error rates) ✓
- [ ] Release documentation:
  - [ ] Release notes prepared (new features, breaking changes, migration steps)
  - [ ] Rollback plan documented (how to disable WebSocket if needed)
  - [ ] Deployment instructions clear
- [ ] Sign-off:
  - [ ] Backend Lead: **\_** (sign)
  - [ ] Frontend Lead: **\_** (sign)
  - [ ] QA Lead: **\_** (sign)
  - [ ] Tech Lead: **\_** (sign)
- **Owner**: [DevOps + Backend Lead] | **Status**: 🟨 In Progress (staging gate pending) | **Est. Time**: 1 hour

---

## 📊 Daily Progress Tracking

### Day 1 Progress Log

**Date**: \***\*\_\_\_\*\***

| Task  | Owner | Status | Time Spent | Notes |
| ----- | ----- | ------ | ---------- | ----- |
| 5.0.1 |       |        |            |       |
| 5.0.2 |       |        |            |       |
| 5.0.3 |       |        |            |       |
| 5.1.1 |       |        |            |       |
| 5.1.2 |       |        |            |       |

**End of Day Summary**:

- Completed: [___] / [___]
- Blockers: [___]
- Next day priority: [___]

---

### Day 2 Progress Log

**Date**: \***\*\_\_\_\*\***

| Task  | Owner | Status | Time Spent | Notes |
| ----- | ----- | ------ | ---------- | ----- |
| 5.2.1 |       |        |            |       |
| 5.2.2 |       |        |            |       |
| 5.2.3 |       |        |            |       |
| 5.3.1 |       |        |            |       |
| 5.3.2 |       |        |            |       |
| 5.4.1 |       |        |            |       |
| 5.4.2 |       |        |            |       |

**End of Day Summary**:

- Completed: [___] / [___]
- Blockers: [___]
- Next day priority: [___]

---

### Day 3 Progress Log (if needed)

**Date**: \***\*\_\_\_\*\***

| Task  | Owner | Status | Time Spent | Notes |
| ----- | ----- | ------ | ---------- | ----- |
| 5.4.3 |       |        |            |       |
| 5.5.1 |       |        |            |       |
| 5.5.2 |       |        |            |       |

**End of Day Summary**:

- Completed: [___] / [___]
- Blockers: [___]
- Phase 5 Status: [Complete / Blocked / On Track]

---

## ✅ Phase 5 Final Sign-off

**Phase 5 Complete**: ☐ YES ☐ NO  
**Date Completed**: \***\*\_\_\_\*\***  
**Critical Issues Found & Fixed**: [___]  
**Known Limitations**: [___]  
**Ready for Phase 6**: ☐ YES ☐ NO

**Team Sign-off**:

- Backend Lead: **\_** (sign)
- Frontend Lead: **\_** (sign)
- QA Lead: **\_** (sign)
- Tech Lead: **\_** (sign)

---

## 🎯 Next Steps (Post-Phase 5)

1. **Phase 6**: Báo cáo, metadata, backup (2-3 ngày)
   - Triển khai revenue report + metadata cache + backup jobs
2. **Phase 7**: Kiểm thử tích hợp + hardening (2-3 ngày)
   - Full contract tests + smoke tests + security audit
3. **Phase 8**: UAT nội bộ + chuẩn bị release (1-2 ngày)
   - Demo cho stakeholder, thu phản hồi, chốt action items
