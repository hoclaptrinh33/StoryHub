# Testing Contracts — Contract Testing, Mock Generation, Realtime, Migration

> File này chứa templates và hướng dẫn cho:
> **Contract Testing**, **Mock Generation**, **Frontend Test Scenarios**,
> **Realtime/WebSocket**, **Migration/Evolution**.
> Tham chiếu từ `SKILL.md` chính.

---

## 1. Contract Testing & Mock Generation

### 1.1. Khi nào tạo

- Cần đảm bảo frontend và backend "nói cùng ngôn ngữ" (contract test)
- Cần mock API cho frontend development song song
- Cần frontend testing scenarios (loading, error, empty states)
- Cần auto-generate test cases từ spec

### 1.2. Section `testing` (thêm vào api template)

```yaml
# Thêm vào cuối file api_*.yaml
# TESTING — Contract tests, mock, frontend scenarios

testing:
  # === CONTRACT TESTS ===
  # Auto-generate test cases đảm bảo API tuân thủ spec
  contract_tests:
    - name: ""                    # Tên test case
      type: ""                    # happy_path | error_case | edge_case | auth_check
      auto_generate: true         # true = agent tự generate test code
      description: ""             # Mô tả test case
      input: {}                   # Test input
      expected_output: {}         # Expected output (hoặc expected_error)
      expected_status: 200        # HTTP status code expected
      # Ví dụ:
      # - name: "should return user data for valid ID"
      #   type: happy_path
      #   auto_generate: true
      #   input: { user_id: "550e8400-e29b-41d4-a716-446655440000" }
      #   expected_status: 200
      # - name: "should return 404 for non-existent user"
      #   type: error_case
      #   auto_generate: true
      #   input: { user_id: "00000000-0000-4000-8000-000000000000" }
      #   expected_status: 404
      #   expected_error: { code: "USER_NOT_FOUND" }
      # - name: "should return 401 without auth token"
      #   type: auth_check
      #   auto_generate: true
      #   expected_status: 401

  # === MOCK GENERATOR ===
  # Sinh mock API responses cho frontend development
  mock:
    enabled: true                 # true = agent sinh mock data
    output_path: ""               # Path để save mock file (ví dụ: "mocks/api_get-user_v1.mock.json")
    
    # Happy path mock
    happy_path:
      delay_ms: 200               # Simulated delay
      response: {}                # Mock response (lấy từ examples[0].output)
    
    # Error case mocks
    error_cases:
      - error_code: ""            # Error code từ errors[]
        delay_ms: 100             # Delay cho error response
        # Ví dụ:
        # - error_code: USER_NOT_FOUND
        #   delay_ms: 100
        # - error_code: DB_CONNECTION_FAILED
        #   delay_ms: 5000        # Simulate slow failure

  # === FRONTEND TEST SCENARIOS ===
  # Mỗi scenario mô tả 1 trạng thái UI cần test
  frontend_scenarios:
    - scenario: ""                # Tên scenario
      description: ""             # Mô tả
      mock_config: {}             # Cấu hình mock cho scenario này
      ui_state: ""                # UI state expected (tham chiếu ui_*.yaml)
      assertions: []              # Kiểm tra gì trên UI
      # Ví dụ:
      # - scenario: "Loading state"
      #   description: "Test skeleton loader hiển thị đúng"
      #   mock_config: { delay_ms: 5000 }
      #   ui_state: "loading"
      #   assertions: ["skeleton visible", "actions disabled"]
      # - scenario: "Error state - Network failure"
      #   description: "Test retry banner hiển thị"
      #   mock_config: { status: 500, error_code: "DB_CONNECTION_FAILED" }
      #   ui_state: "error"
      #   assertions: ["retry button visible", "error message shown"]
      # - scenario: "Empty state"
      #   description: "Test empty illustration"
      #   mock_config: { status: 404, error_code: "USER_NOT_FOUND" }
      #   ui_state: "empty"
      #   assertions: ["empty illustration visible", "back button visible"]
      # - scenario: "Auth - insufficient permissions"
      #   description: "Test hidden/disabled elements"
      #   mock_config: { auth_role: "viewer" }
      #   ui_state: "success"
      #   assertions: ["edit_button hidden", "delete_button disabled"]
```

### 1.3. Ví dụ đầy đủ: Testing section cho `api_get-user_v1.yaml`

```yaml
testing:
  contract_tests:
    - name: "should return user data for valid UUID"
      type: happy_path
      auto_generate: true
      input: { user_id: "550e8400-e29b-41d4-a716-446655440000" }
      expected_status: 200
    - name: "should return 404 for non-existent user"
      type: error_case
      auto_generate: true
      input: { user_id: "00000000-0000-4000-8000-000000000000" }
      expected_status: 404
      expected_error: { code: "USER_NOT_FOUND" }
    - name: "should return 400 for invalid UUID format"
      type: error_case
      auto_generate: true
      input: { user_id: "not-a-uuid" }
      expected_status: 400
      expected_error: { code: "INVALID_UUID" }
    - name: "should return 401 without auth token"
      type: auth_check
      auto_generate: true
      expected_status: 401
    - name: "should return 403 for viewer accessing admin data"
      type: auth_check
      auto_generate: true
      input: { user_id: "admin-user-id" }
      expected_status: 403

  mock:
    enabled: true
    output_path: "mocks/api_get-user_v1.mock.json"
    happy_path:
      delay_ms: 150
      response:
        id: "550e8400-e29b-41d4-a716-446655440000"
        name: "Nguyễn Văn A"
        email: "nguyenvana@example.com"
        age: 28
        role: "editor"
        created_at: "2024-01-15T08:30:00Z"
    error_cases:
      - error_code: USER_NOT_FOUND
        delay_ms: 100
      - error_code: DB_CONNECTION_FAILED
        delay_ms: 5000
      - error_code: INVALID_UUID
        delay_ms: 50

  frontend_scenarios:
    - scenario: "Loading state"
      description: "Skeleton loader hiển thị khi đang fetch"
      mock_config: { delay_ms: 5000 }
      ui_state: "loading"
      assertions:
        - "Skeleton loader visible cho avatar, name, email"
        - "Edit/Delete buttons disabled"
    - scenario: "Success state"
      description: "Data hiển thị đầy đủ"
      mock_config: { delay_ms: 150 }
      ui_state: "success"
      assertions:
        - "User name hiển thị"
        - "Email hiển thị"
        - "Role badge hiển thị"
    - scenario: "Error - User not found"
      description: "Empty state illustration"
      mock_config: { status: 404, error_code: "USER_NOT_FOUND" }
      ui_state: "empty"
      assertions:
        - "Empty state illustration visible"
        - "Text: 'Không tìm thấy người dùng'"
        - "Back button visible"
    - scenario: "Error - Server error"
      description: "Retry banner với exponential backoff"
      mock_config: { status: 503, error_code: "DB_CONNECTION_FAILED" }
      ui_state: "error"
      assertions:
        - "Error banner visible"
        - "Retry button visible"
        - "Auto retry sau 1s, 2s, 4s"
    - scenario: "Auth - Viewer role"
      description: "Kiểm tra hidden/disabled elements"
      mock_config: { auth_role: "viewer" }
      ui_state: "success"
      assertions:
        - "Delete button hidden"
        - "Edit button disabled"
```

---

## 2. Realtime / Event-Driven Layer

### 2.1. Khi nào tạo

- Ứng dụng có WebSocket / SSE (Server-Sent Events)
- Có realtime updates (live notifications, live data)
- Kiosk / dashboard cần auto-refresh
- Agent cần biết "data có thể thay đổi mà không cần gọi API lại"

### 2.2. Template `realtime_{channel}.yaml`

```yaml
# File: realtime_{channel}.yaml
# Định nghĩa kênh realtime

# IDENTITY
channel: ""                       # Tên channel (snake_case)
description: ""                   # Mô tả
protocol: ""                      # websocket | sse | polling | mqtt

# CONNECTION
connection:
  path: ""                        # WebSocket path (ví dụ: "/ws/books")
  auth_required: true             # Cần auth để connect?
  heartbeat_interval_ms: 30000    # Ping/pong interval
  reconnect_strategy: ""          # exponential_backoff | fixed_interval | none
  max_reconnect_attempts: 10

# EVENTS — Sự kiện truyền qua channel
events:
  - name: ""                      # Tên event realtime
    direction: ""                 # server_to_client | client_to_server | bidirectional
    payload:
      type: object
      properties: {}
    related_api_event: ""         # Map đến event_*.yaml (nếu có)
    triggers_ui: ""               # UI component nào cần update (tham chiếu ui_*.yaml)
    throttle_ms: 0                # Throttle event (tránh flood)
    # Ví dụ:
    # - name: book_status_changed
    #   direction: server_to_client
    #   payload:
    #     type: object
    #     properties:
    #       book_id: { type: string }
    #       old_status: { type: string }
    #       new_status: { type: string }
    #   related_api_event: event_book-borrowed
    #   triggers_ui: ui_book-list
    #   throttle_ms: 1000

# SUBSCRIPTIONS — Ai nhận gì
subscriptions:
  - role: ""                      # Role được subscribe
    events: []                    # Danh sách events nhận
    filter: ""                    # Filter condition (ví dụ: chỉ nhận events liên quan đến mình)
    # Ví dụ:
    # - role: librarian
    #   events: [book_status_changed, new_reservation, overdue_alert]
    # - role: user
    #   events: [book_status_changed]
    #   filter: "event.reserved_by == current_user.id"

# PERFORMANCE
performance:
  max_connections: 1000           # Số connections tối đa
  message_size_limit_kb: 64      # Kích thước message tối đa
  buffer_size: 100                # Số messages buffer khi client offline
```

### 2.3. Ví dụ: `realtime_library-updates.yaml`

```yaml
channel: library_updates
description: "Cập nhật realtime cho hệ thống thư viện — trạng thái sách, thông báo"
protocol: websocket

connection:
  path: "/ws/library"
  auth_required: true
  heartbeat_interval_ms: 30000
  reconnect_strategy: exponential_backoff
  max_reconnect_attempts: 10

events:
  - name: book_status_changed
    direction: server_to_client
    payload:
      type: object
      properties:
        book_id: { type: string, format: uuid }
        old_status: { type: string, enum: [available, reserved, borrowed, returned] }
        new_status: { type: string, enum: [available, reserved, borrowed, returned] }
        changed_by: { type: string, format: uuid }
        timestamp: { type: string, format: date-time }
    related_api_event: event_book-borrowed
    triggers_ui: ui_book-list
    throttle_ms: 500
  - name: new_reservation
    direction: server_to_client
    payload:
      type: object
      properties:
        book_id: { type: string, format: uuid }
        user_id: { type: string, format: uuid }
        expires_at: { type: string, format: date-time }
    triggers_ui: ui_book-detail
    throttle_ms: 0
  - name: overdue_alert
    direction: server_to_client
    payload:
      type: object
      properties:
        transaction_id: { type: string, format: uuid }
        book_title: { type: string }
        days_overdue: { type: integer }
    triggers_ui: ui_notifications
    throttle_ms: 0

subscriptions:
  - role: librarian
    events: [book_status_changed, new_reservation, overdue_alert]
  - role: admin
    events: [book_status_changed, new_reservation, overdue_alert]
  - role: user
    events: [book_status_changed, overdue_alert]
    filter: "event.user_id == current_user.id OR event.reserved_by == current_user.id"

performance:
  max_connections: 500
  message_size_limit_kb: 32
  buffer_size: 50
```

---

## 3. Migration / Evolution

### 3.1. Khi nào tạo

- Breaking change trong API (v1 → v2)
- Schema database thay đổi
- Business rule thay đổi (config không đủ, cần code change)
- Cần audit trail cho thay đổi hệ thống

### 3.2. Template `migration_{name}.md`

```markdown
# Migration: [Tên migration]

> **Type:** [api_version | schema | business_rule | data]
> **Status:** [planned | in_progress | completed | rolled_back]
> **Date:** [YYYY-MM-DD]
> **Breaking:** [yes | no]

## Tổng quan

[Mô tả thay đổi và lý do]

## Impact Analysis

### Affected Docs
| Doc | Thay đổi |
|-----|---------|
| [`api_name`](./api_name.yaml) | [Mô tả impact] |
| [`domain_name`](./domain_name.yaml) | [Mô tả impact] |

### Affected Consumers
| Consumer | Impact | Action Required |
|----------|--------|----------------|
| Frontend Web | | |
| Mobile App | | |
| Partner API | | |

## Migration Steps

### Pre-migration
1. [ ] [Bước chuẩn bị]

### Execution
1. [ ] [Bước thực hiện]

### Post-migration
1. [ ] [Bước kiểm tra]

## Rollback Plan

Nếu migration fail:
1. [Bước rollback]

## Data Migration (nếu có)

```sql
-- Forward migration
ALTER TABLE ...

-- Rollback migration
ALTER TABLE ...
```

## Timeline

| Mốc | Ngày | Trạng thái |
|-----|------|-----------|
| Announced | | |
| Deprecation warning | | |
| Migration window | | |
| Old version removed | | |

## Related
- [Deprecation flow](./deprecation-flow.md) — nếu là API version change
```

---

## 4. Quy tắc sử dụng chung

### 4.1. Testing docs auto-generation

Khi agent sinh `api_*.yaml` ở mode `detailed`:
1. **Tự động** thêm section `testing` với ≥ 3 contract tests:
   - 1 happy path
   - 1 error case
   - 1 auth check
2. **Tự động** generate mock data từ `examples[]`
3. **Tự động** generate ≥ 3 frontend scenarios:
   - loading state
   - success state
   - error state

### 4.2. Realtime docs khi nào tạo

Agent tạo `realtime_*.yaml` khi phát hiện:
- WebSocket / Socket.IO imports
- SSE (Server-Sent Events) endpoint
- Polling pattern (setInterval + API call)
- MQTT / Redis Pub/Sub imports

### 4.3. Migration docs khi nào tạo

Agent tạo `migration_*.md` khi:
- Chạy deprecation flow (v1 → v2)
- Schema change detected (so sánh hash)
- Business rule change (domain_*.yaml thay đổi invariant)

### 4.4. Validation rules

**Testing section:**
- [ ] Có ≥ 1 happy_path test
- [ ] Có ≥ 1 error_case test
- [ ] Mỗi error_code trong `errors[]` có ≥ 1 test case
- [ ] Mock response khớp với `returns` schema

**Realtime:**
- [ ] Mỗi event có payload schema
- [ ] Subscriptions cover tất cả roles trong auth
- [ ] `triggers_ui` trỏ đúng ui_*.yaml

**Migration:**
- [ ] Có rollback plan
- [ ] Affected docs được liệt kê đầy đủ
- [ ] Timeline rõ ràng
