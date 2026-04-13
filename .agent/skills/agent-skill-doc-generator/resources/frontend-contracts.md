# Frontend Contracts — UI Contract, User Flow, SDK/Client

> File này chứa templates và hướng dẫn cho 3 loại doc mới:
> **UI Contract**, **User Flow**, **SDK/Client Generation**.
> Tham chiếu từ `SKILL.md` chính.

---

## 1. UI Contract — Giao diện Machine-readable

### 1.1. Khi nào tạo

- Frontend cần biết rõ: hiển thị gì, khi nào loading, khi nào error
- Agent cần generate UI code chính xác (không đoán)
- Cần đồng bộ behavior giữa backend và frontend
- Có nhiều trạng thái UI phức tạp (không chỉ show data)

> 💡 `ui_*.yaml` là **spec cho UI** — giống như `api_*.yaml` là spec cho API.
> Backend team viết `api_*.yaml`, Frontend team viết/consume `ui_*.yaml`.

### 1.2. Template `ui_{feature}.yaml`

```yaml
# File: ui_{feature}.yaml
# UI Contract — Đặc tả giao diện cho feature

# IDENTITY
component: ""                     # Tên component (PascalCase)
description: ""                   # Mô tả ngắn gọn chức năng UI
page: ""                          # Trang chứa component (ví dụ: "/users/:id")
platform: "web"                   # web | mobile | kiosk | universal

# UI STATES — Các trạng thái giao diện
# Agent PHẢI handle TẤT CẢ states khi generate UI code
states:
  - name: ""                      # idle | loading | success | error | empty | offline
    description: ""               # Mô tả khi nào state này xảy ra
    ui_behavior: ""               # Mô tả UI hiển thị gì ở state này
    # Ví dụ:
    # - name: loading
    #   description: "Đang fetch data từ API"
    #   ui_behavior: "Hiển thị skeleton loader, disable tất cả actions"

# DATA BINDING — Nguồn dữ liệu
data_binding:
  source: ""                      # Tên API (tham chiếu api_*.yaml)
  method: ""                      # GET | POST...
  mapping: {}                     # Map từ API response → UI fields
    # Ví dụ:
    # display_name: response.user.name
    # avatar_url: response.user.avatar
  refresh_strategy: ""            # manual | interval:30s | realtime | on-focus
  cache_strategy: ""              # none | stale-while-revalidate | cache-first

# INTERACTIONS — Hành động người dùng
interactions:
  - action: ""                    # Tên hành động (ví dụ: "submit_form")
    trigger: ""                   # UI element kích hoạt (ví dụ: "submit_button click")
    api_call: ""                  # API được gọi (tham chiếu api_*.yaml)
    optimistic_update: false      # true = update UI trước khi API response
    loading_indicator: ""         # button_spinner | overlay | inline | none
    success_feedback: ""          # toast | redirect | inline_message | none
    confirm_required: false       # true = hiện dialog xác nhận trước
    confirm_message: ""           # Nội dung dialog xác nhận

# ERROR HANDLING — Xử lý lỗi ở tầng UI
error_handling: {}                # Map error_code → UI behavior
  # Ví dụ:
  # USER_NOT_FOUND:
  #   ui: "empty_state"
  #   message: "Không tìm thấy người dùng"
  #   action: "show_search_suggestion"
  # NETWORK_ERROR:
  #   ui: "retry_banner"
  #   strategy: "exponential_backoff"
  #   max_retries: 3

# AUTH UI — Hiển thị theo quyền
auth_ui:
  hide_if_no_permission: []       # Danh sách UI elements bị ẩn
  disable_if_no_permission: []    # Danh sách UI elements bị disable
  route_guard:
    required_roles: []            # Roles cần có để truy cập trang
    redirect_to: ""               # Redirect đến đâu nếu không đủ quyền
    show_message: ""              # Thông báo hiển thị

# PERFORMANCE — Yêu cầu hiệu năng UI
performance:
  skeleton_loading: false         # true = dùng skeleton thay spinner
  lazy_load: false                # true = lazy load component
  virtualize_list: false          # true = dùng virtual scrolling cho list dài
  prefetch: []                    # API calls cần prefetch
  debounce_ms: 0                  # Debounce cho input (ví dụ: search)

# RESPONSIVE — Responsive behavior
responsive:
  breakpoints:
    mobile: ""                    # Behavior trên mobile (ví dụ: "stack layout")
    tablet: ""                    # Behavior trên tablet
    desktop: ""                   # Behavior trên desktop

# ACCESSIBILITY
accessibility:
  aria_label: ""                  # Label cho screen reader
  keyboard_nav: true              # Hỗ trợ keyboard navigation
  focus_trap: false               # true = giữ focus trong component (modal)

# RELATED
related_api: ""                   # API chính (tham chiếu api_*.yaml)
related_lifecycle: ""             # Lifecycle liên quan (tham chiếu lifecycle_*.yaml)
related_domain: ""                # Domain liên quan (tham chiếu domain_*.yaml)
```

### 1.3. Template `ui_{feature}.md`

```markdown
# UI: [Component Name]

> **Schema file:** [`ui_{feature}.yaml`](./ui_{feature}.yaml)
> **Page:** [route] | **Platform:** [web/mobile/kiosk]

## Mô tả

[Component này hiển thị gì, ở đâu, cho ai]

## UI States

| State | Khi nào | UI hiển thị |
|-------|---------|-------------|
| idle | | |
| loading | | |
| success | | |
| error | | |
| empty | | |

> ⚠️ **Agent PHẢI implement TẤT CẢ states.** Không được bỏ qua error/empty state.

## Data Binding

- **Source:** [`api_name`](./api_name.yaml)
- **Refresh:** [strategy]
- **Cache:** [strategy]

### Field Mapping

| UI Field | API Response Path | Format |
|----------|------------------|--------|
| | | |

## User Interactions

| Hành động | Trigger | API Call | Optimistic? | Feedback |
|-----------|---------|---------|-------------|----------|
| | | | | |

## Error Handling (UI)

| Error Code | UI Behavior | Message | Action |
|-----------|-------------|---------|--------|
| | | | |

## Auth & Permissions (UI)

| Element | Rule | Khi không có quyền |
|---------|------|-------------------|
| | | |

## Responsive Behavior

| Breakpoint | Layout | Thay đổi |
|-----------|--------|----------|
| Mobile | | |
| Tablet | | |
| Desktop | | |

## Performance Notes

- [Skeleton loading, lazy load, prefetch...]

## Wireframe / Mockup

> [Mô tả bố cục hoặc link đến wireframe]
```

### 1.4. Ví dụ đầy đủ: `ui_user-profile.yaml`

```yaml
component: UserProfile
description: "Trang thông tin chi tiết user — hiển thị profile, cho phép edit"
page: "/users/:user_id"
platform: web

states:
  - name: idle
    description: "Component vừa mount, chưa fetch data"
    ui_behavior: "Hiển thị skeleton loader"
  - name: loading
    description: "Đang fetch user data từ API"
    ui_behavior: "Skeleton loader cho avatar + text fields, disable all actions"
  - name: success
    description: "Data fetch thành công"
    ui_behavior: "Hiển thị đầy đủ thông tin user, enable edit/delete buttons"
  - name: error
    description: "API trả lỗi"
    ui_behavior: "Hiển thị error banner với nút retry"
  - name: empty
    description: "User không tồn tại (404)"
    ui_behavior: "Hiển thị empty state: 'User không tồn tại', nút quay lại"
  - name: editing
    description: "User đang sửa thông tin"
    ui_behavior: "Chuyển fields sang editable, hiện Save/Cancel buttons"

data_binding:
  source: api_get-user_v1
  method: GET
  mapping:
    display_name: response.name
    email: response.email
    avatar_url: response.avatar
    role_badge: response.role
    member_since: response.created_at
  refresh_strategy: on-focus
  cache_strategy: stale-while-revalidate

interactions:
  - action: edit_profile
    trigger: "edit_button click"
    api_call: api_update-user_v1
    optimistic_update: false
    loading_indicator: button_spinner
    success_feedback: toast
    confirm_required: false
  - action: delete_account
    trigger: "delete_button click"
    api_call: api_delete-user_v1
    optimistic_update: false
    loading_indicator: overlay
    success_feedback: redirect
    confirm_required: true
    confirm_message: "Bạn có chắc chắn muốn xóa tài khoản? Hành động này không thể hoàn tác."
  - action: refresh_data
    trigger: "refresh_button click OR page focus"
    api_call: api_get-user_v1
    optimistic_update: false
    loading_indicator: inline

error_handling:
  USER_NOT_FOUND:
    ui: "empty_state"
    message: "Không tìm thấy người dùng này"
    action: "show_back_button"
  DB_CONNECTION_FAILED:
    ui: "retry_banner"
    strategy: "exponential_backoff"
    max_retries: 3
    message: "Lỗi kết nối, đang thử lại..."
  INVALID_UUID:
    ui: "error_page"
    message: "Đường dẫn không hợp lệ"
    action: "redirect_to_home"
  FORBIDDEN:
    ui: "access_denied"
    message: "Bạn không có quyền xem thông tin này"

auth_ui:
  hide_if_no_permission: ["delete_button", "admin_badge"]
  disable_if_no_permission: ["edit_button"]
  route_guard:
    required_roles: ["admin", "editor", "self"]
    redirect_to: "/403"
    show_message: "Bạn cần đăng nhập để xem trang này"

performance:
  skeleton_loading: true
  lazy_load: false
  virtualize_list: false
  prefetch: ["api_get-user-permissions_v1"]
  debounce_ms: 0

responsive:
  breakpoints:
    mobile: "Stack layout, avatar trên cùng, fields bên dưới"
    tablet: "2 cột: avatar bên trái, fields bên phải"
    desktop: "2 cột rộng với sidebar navigation"

accessibility:
  aria_label: "Trang thông tin người dùng"
  keyboard_nav: true
  focus_trap: false

related_api: api_get-user_v1
related_lifecycle: null
related_domain: domain_user
```

---

## 2. User Flow — Luồng thao tác người dùng

### 2.1. Khi nào tạo

- Feature có nhiều bước (>2 steps)
- Cần document cả happy path lẫn edge cases
- Frontend team cần biết "user làm gì ↔ system respond gì"
- Agent cần tạo UI wizard, multi-step form, checkout flow

### 2.2. Template `flow_{feature}.md`

```markdown
# Flow: [Feature Name]

> **Actors:** [Ai tham gia flow này]
> **Preconditions:** [Điều kiện trước khi bắt đầu]
> **Postconditions:** [Kết quả sau khi hoàn tất]

## Tổng quan

[Mô tả ngắn về flow này — user đang cố gắng làm gì]

## Happy Path

| Bước | Actor | Hành động | System Response | API/Event | UI State |
|------|-------|----------|-----------------|-----------|----------|
| 1 | | | | | |
| 2 | | | | | |
| 3 | | | | | |

## Sơ đồ luồng

```
[User Action 1]
    │
    ▼
[System Check] ──(fail)──→ [Error UI]
    │ (pass)
    ▼
[User Action 2]
    │
    ▼
[System Response] → [Success UI]
```

## Alternative Paths

### Alt 1: [Tên tình huống]
| Bước | Thay đổi | Xử lý |
|------|---------|-------|
| | | |

## Edge Cases

| Case | Trigger | System Response | UI Response |
|------|---------|-----------------|-------------|
| | | | |

## Error Recovery

| Lỗi | Bước xảy ra | Recovery |
|-----|------------|----------|
| | | |

## Related Docs

| Doc | Vai trò trong flow |
|-----|-------------------|
| [`api_name`](./api_name.yaml) | Bước X |
| [`ui_name`](./ui_name.yaml) | UI cho bước Y |
| [`lifecycle_name`](./lifecycle_name.yaml) | State chuyển ở bước Z |
```

### 2.3. Ví dụ đầy đủ: `flow_borrow-book.md`

```markdown
# Flow: Mượn sách

> **Actors:** User (thành viên thư viện), System, Librarian (optional)
> **Preconditions:** User đã đăng nhập, có thẻ thành viên active
> **Postconditions:** Sách chuyển sang trạng thái "borrowed", user có transaction record

## Tổng quan

User muốn mượn sách từ thư viện. Flow bao gồm: tìm sách → kiểm tra
khả dụng → xác nhận mượn → nhận xác nhận.

## Happy Path

| Bước | Actor | Hành động | System Response | API/Event | UI State |
|------|-------|----------|-----------------|-----------|----------|
| 1 | User | Quét thẻ NFC tại kiosk | Hiển thị thông tin user | `api_scan-card_v1` | `ui_user-info.loading → success` |
| 2 | User | Tìm kiếm sách | Hiển thị danh sách kết quả | `api_search-book_v1` | `ui_book-search.loading → success` |
| 3 | User | Chọn sách cần mượn | Hiển thị chi tiết sách + nút "Mượn" | `api_get-book_v1` | `ui_book-detail.success` |
| 4 | User | Nhấn "Xác nhận mượn" | Kiểm tra quota → tạo giao dịch | `api_borrow-book_v1` | `ui_borrow-confirm.loading` |
| 5 | System | — | Gửi email xác nhận + in phiếu | `event_book_borrowed` | `ui_borrow-success.success` |
| 6 | User | Lấy sách | — | — | `ui_borrow-success.idle` |

## Sơ đồ luồng

```
[Quét thẻ NFC]
    │
    ▼
[Verify user] ──(thẻ không hợp lệ)──→ [Hiển thị lỗi, yêu cầu quét lại]
    │ (OK)
    ▼
[Tìm sách] ──(không tìm thấy)──→ [Hiển thị empty state]
    │ (tìm thấy)
    ▼
[Chọn sách] ──(sách không available)──→ [Hiển thị "Sách đang được mượn"]
    │ (available)
    ▼
[Check quota] ──(vượt quota)──→ [Hiển thị cảnh báo quota]
    │ (OK)
    ▼
[Tạo giao dịch] → [Email + Print] → [Thành công]
```

## Edge Cases

| Case | Trigger | System Response | UI Response |
|------|---------|-----------------|-------------|
| Thẻ hết hạn | Scan thẻ NFC | `CARD_EXPIRED` (401) | Hiển thị "Thẻ hết hạn, liên hệ quầy" |
| Vượt quota mượn | Nhấn "Mượn" | `BORROW_LIMIT_EXCEEDED` (403) | Hiển thị "Bạn đã mượn tối đa X sách" |
| Sách đang reserved bởi user khác | Xem chi tiết sách | Sách status = "reserved" | Disable nút "Mượn", hiển thị "Sách đã được đặt trước" |
| User bị suspend | Scan thẻ | `USER_SUSPENDED` (403) | Hiển thị "Tài khoản tạm khóa" + lý do |
| Network timeout | Bất kỳ bước nào | timeout | Hiển thị retry banner |

## Error Recovery

| Lỗi | Bước xảy ra | Recovery |
|-----|------------|----------|
| Mất kết nối giữa bước 4 | Xác nhận mượn | Retry tự động 3 lần, nếu fail hiện nút retry manual |
| Kiosk crash sau bước 4 | Sau khi tạo giao dịch | Transaction đã lưu DB, user vẫn nhận email xác nhận |
| Printer offline | Bước 5 (in phiếu) | Skip print, gửi phiếu qua email thay thế |

## Related Docs

| Doc | Vai trò trong flow |
|-----|-------------------|
| [`api_scan-card_v1`](./api_scan-card_v1.yaml) | Bước 1: Verify thẻ |
| [`api_search-book_v1`](./api_search-book_v1.yaml) | Bước 2: Tìm sách |
| [`api_borrow-book_v1`](./api_borrow-book_v1.yaml) | Bước 4: Tạo giao dịch |
| [`ui_borrow-confirm`](./ui_borrow-confirm.yaml) | UI cho bước 4-5 |
| [`lifecycle_book`](./lifecycle_book.yaml) | State: available → borrowed |
| [`event_book-borrowed`](./event_book-borrowed.yaml) | Bước 5: Side effects |
| [`domain_user`](./domain_user.yaml) | Invariant: quota check |
```

---

## 3. SDK / Client Generation — Hooks & Typed Clients

### 3.1. Mục đích

Thêm section `client` vào API `.yaml` template để agent có thể:
- Generate typed SDK client (TypeScript, Kotlin, Swift)
- Generate React hooks (React Query, SWR)
- Generate mock adapters cho testing

### 3.2. Section `client` (thêm vào api template)

```yaml
# Thêm vào cuối file api_*.yaml
# PHẦN MỚI: CLIENT / SDK GENERATION
client:
  # SDK targets — ngôn ngữ cần generate
  sdk_targets:
    - language: typescript
      output: "sdk/userApi.ts"
    - language: kotlin  
      output: "sdk/UserApi.kt"

  # React hooks
  hooks:
    react_query:
      query_key: ["user", "userId"]
      hook_name: "useGetUser"
      enabled_condition: "!!userId"
      stale_time_ms: 300000
      example: |
        const { data, error, isLoading } = useGetUser(userId);
    swr:
      hook_name: "useUser"
      key: "/api/v1/users/${userId}"
      example: |
        const { data, error } = useUser(userId);

  # Mock adapter (cho testing)
  mock:
    happy_path:
      delay_ms: 200
      response: # Lấy từ examples[0].output
    error_cases:
      - error_code: USER_NOT_FOUND
        delay_ms: 100
      - error_code: DB_CONNECTION_FAILED
        delay_ms: 5000
```

### 3.3. Section `frontend` (thêm vào api template behavior)

```yaml
# Thêm vào section behavior: trong api_*.yaml
behavior:
  # ... sections cũ giữ nguyên ...
  
  # MỚI: Frontend behavior hints
  frontend:
    loading_strategy: "skeleton"     # skeleton | spinner | shimmer | none
    error_surface: "toast"           # toast | modal | inline | page
    empty_state: "illustration"      # illustration | text | redirect
    cache_strategy: "stale-while-revalidate"  # none | cache-first | stale-while-revalidate
    retry_ui: true                   # true = hiển thị nút retry khi error
    optimistic_updates: false        # true = agent dùng optimistic update
```

---

## 4. Quy tắc sử dụng chung

### 4.1. Quan hệ giữa frontend docs và backend docs

```
api_{action}_v1.yaml          ← Backend spec (inputs/outputs/errors)
    │
    ├── ui_{feature}.yaml     ← Frontend spec (states/interactions/auth_ui)
    │       │
    │       └── flow_{feature}.md  ← User flow (step-by-step UX)
    │
    └── client: section       ← SDK/hooks generation
```

### 4.2. Agent phải đọc theo thứ tự (khi generate UI)

1. **`api_*.yaml`** → biết data shape + errors
2. **`ui_*.yaml`** → biết UI states + interactions
3. **`flow_*.md`** → hiểu full flow multi-step
4. **`lifecycle_*.yaml`** → biết state transitions ảnh hưởng UI

### 4.3. Validation rules cho frontend docs

**File `ui_*.yaml`:**
- [ ] Phải có ÍT NHẤT 4 states: loading, success, error, empty
- [ ] `data_binding.source` phải trỏ đúng tên api docs
- [ ] Mỗi error_code trong `error_handling` phải tồn tại trong api docs tương ứng
- [ ] `auth_ui.route_guard.required_roles` phải subset của `api.auth.roles`

**File `flow_*.md`:**
- [ ] Happy path phải có ≥ 2 bước
- [ ] Mỗi API reference phải tồn tại
- [ ] Phải có ≥ 1 edge case
- [ ] Phải có error recovery section
