# Templates — Mẫu file output

> File này chứa các template trống để Agent copy và điền nội dung khi sinh docs.
> **Không sửa template trực tiếp** — chỉ copy rồi điền.

---

## 1. Template file `.yaml` — Mode: Detailed

```yaml
# File: {prefix}_{tên-ngắn-gọn}[_v{N}].yaml

# IDENTITY
name: ""
description: ""
version: 1.0.0
deprecated: false
tags: []
category: ""
priority: medium
doc_ref: "{prefix}_{tên-ngắn-gọn}[_v{N}].md"

# HTTP ENDPOINT (chỉ cho API endpoints, bỏ qua nếu utility function)
http:
  method: ""            # GET | POST | PUT | PATCH | DELETE
  path: ""              # Route pattern, ví dụ: /api/v1/users/:id
  path_params: {}
  query_params: {}
  request_body: null
  content_type: "application/json"

# PARAMETERS
parameters:
  type: object
  required: []
  properties: {}

# RETURNS
returns:
  type: object
  properties: {}

# BEHAVIOR CONTRACT
behavior:
  deterministic: true
  idempotent: true
  retryable: true
  side_effects: "none"
  latency: low
  cacheable: false
  # V2.0: Preconditions — điều kiện phải đúng trước khi gọi API
  preconditions: []          # [{condition: "", check_via: "", error_if_false: ""}]
  # V2.0: Postconditions — trạng thái hệ thống sau khi API thành công
  postconditions: []         # [{effect: "", verifiable: true, verify_via: ""}]
  # V2.0: Side-effect scope chi tiết
  side_effect_scope:
    reads: []
    writes: []
    external: []
  # V2.0: Failure strategy cho từng loại lỗi
  failure_strategy: {}       # {ERROR_CODE: {action: retry|skip|fallback, max_retries: 3, fallback: ""}}
  # V2.0: Frontend behavior hints
  frontend:
    loading_strategy: ""     # skeleton | spinner | shimmer | none
    error_surface: ""        # toast | modal | inline | fullpage
    empty_state: ""          # illustration | text_only | redirect
    cache_strategy: ""       # none | cache-first | stale-while-revalidate
    retry_ui: false
    optimistic_updates: false

# ERROR SCHEMA
errors: []

# AUTH CONTEXT (v2.0: ABAC)
auth:
  required: false
  type: ""
  scopes: []
  # V2.0: ABAC Permissions thay thế roles đơn giản
  permissions: []            # [{role: "", access: "full|conditional", condition: "", fields_denied: []}]
  # V2.0: Frontend auth
  frontend_auth:
    hide_actions: []
    disable_actions: []
    route_guard:
      min_role: ""
      redirect_to: ""

# TOOL DEPENDENCIES (v2.0: ordered, conditional, fallback)
dependencies:
  requires: []               # [{tool: "", order: 1, mandatory: true, provides_data: ""}]
  conditional: []            # [{tool: "", condition: ""}]
  fallback: []               # [{tool: "", replaces: "", when: ""}]
  provides: []
  conflicts_with: []

# RATE LIMITING
rate_limit:
  max_calls_per_minute: 60
  max_concurrent: 10

# PERFORMANCE
performance:
  expected_latency_ms: 200
  timeout_ms: 5000
  cache_ttl_seconds: 0

# ENVIRONMENT
environment:
  supported: ["production", "staging", "development"]
  requires_services: []
  runtime: ""

# STRUCTURED EXAMPLES
examples: []

# VERSIONING
versioning:
  backward_compatible: true
  changelog: []

# OBSERVABILITY (v2.0: business metrics, tracing, feedback)
observability:
  logging_level: info
  technical_metrics: []      # [{name: "", type: "counter|gauge|histogram", alert_threshold: ""}]
  business_metrics: []       # [{name: "", type: "", unit: "", alert_threshold: ""}]
  tracing:
    span_name: ""
    parent_span: ""
  feedback_triggers: []      # [{metric: "", condition: "", action: ""}]

# CLIENT / SDK (v2.0)
client:
  sdk_targets: []            # [{language: "", output: ""}]
  hooks: {}                  # {react_query: {hook_name: ""}, swr: {hook_name: ""}}
  mock:
    enabled: false
    output_path: ""

# TESTING (v2.0)
testing:
  contract_tests: []         # [{name: "", type: "happy_path|error_case|auth_check", auto_generate: true}]
  mock:
    enabled: false
    happy_path: {}
    error_cases: []
  frontend_scenarios: []     # [{scenario: "", mock_config: {}, ui_state: "", assertions: []}]

# SOURCE TRACKING (cho incremental update & staleness detection)
source_tracking:
  files: []              # [{path: "", hash: "sha256:..."}]
  generated_at: ""       # ISO 8601 timestamp
  generator_version: ""  # Version của skill đã sinh file này
```

---

## 2. Template file `.md` — Mode: Detailed

```markdown
# [Function Name]

> **Schema file:** [`{prefix}_{tên}[_v{N}].yaml`](./{prefix}_{tên}[_v{N}].yaml)
> **Version:** x.y.z | **Category:** [category] | **Priority:** [priority]
> **Endpoint:** `METHOD /api/v{N}/path` (nếu là API)

## Mô tả chức năng

> **WHY**: [Tại sao function này tồn tại, giải quyết vấn đề gì]

[Mô tả ngắn gọn chức năng]

## Tham số

| Tên | Kiểu | Bắt buộc | Mô tả |
|-----|------|----------|-------|
| | | | |

## Ví dụ sử dụng

### Cơ bản
```
[Code example]
```

## Response Schema

```json
{
}
```

## Edge Cases

| Case | Input | Kết quả |
|------|-------|---------|
| | | |

## Lưu ý hiệu năng

- [Performance notes]

## Lưu ý bảo mật

- [Security notes]

## Liên kết liên quan

| API | Mô tả | Quan hệ |
|-----|-------|--------|
| [`{tên-api-liên-quan}`](./{file}.md) | [Mô tả ngắn] | [requires / related / conflicts] |

## Changelog

| Version | Ngày | Thay đổi |
|---------|------|----------|
| | | |
```

---

## 3. Template file `.yaml` — Mode: Schema-only

Chỉ giữ các phần bắt buộc, **KHÔNG tạo file `.md`**:

```yaml
# File: {prefix}_{tên-ngắn-gọn}[_v{N}].yaml (schema-only)
name: ""
description: ""
version: 1.0.0
parameters:
  type: object
  required: []
  properties: {}
returns:
  type: object
  properties: {}
behavior:
  deterministic: true
  idempotent: true
  retryable: true
  side_effects: "none"
errors: []
auth:
  required: false
source_tracking:
  files: []
  generated_at: ""
```

---

## 4. Template file `.yaml` — Mode: Blueprint (Design-First)

Dùng khi sinh docs từ ý tưởng, **chưa có source code**.

```yaml
# File: {prefix}_{tên-ngắn-gọn}[_v{N}].yaml
# ⚠️ STATUS: BLUEPRINT — Sinh từ mô tả ý tưởng, chưa có code thực tế

# IDENTITY
name: ""
description: ""
version: 0.1.0-blueprint    # Version 0.x = chưa có implementation
deprecated: false
status: blueprint            # blueprint | implemented | verified
tags: []
category: ""
priority: medium
doc_ref: "{prefix}_{tên-ngắn-gọn}[_v{N}].md"

# HTTP ENDPOINT (dự kiến)
http:
  method: ""
  path: ""
  path_params: {}
  query_params: {}
  request_body: null
  content_type: "application/json"

# PARAMETERS (dự kiến)
parameters:
  type: object
  required: []
  properties: {}

# RETURNS (dự kiến)
returns:
  type: object
  properties: {}

# BEHAVIOR CONTRACT (dự kiến — agent suy luận từ mô tả)
behavior:
  deterministic: true
  idempotent: true
  retryable: true
  side_effects: "none"
  latency: low
  cacheable: false

# ERROR SCHEMA (dự kiến)
errors: []

# AUTH CONTEXT (dự kiến)
auth:
  required: false
  type: ""
  roles: []
  scopes: []

# TOOL DEPENDENCIES (dự kiến)
dependencies:
  requires: []
  provides: []
  conflicts_with: []

# BLUEPRINT TRACKING (thay thế source_tracking khi chưa có code)
blueprint_tracking:
  prompt_hash: ""            # SHA-256 hash của prompt/ý tưởng gốc
  prompt_summary: ""         # Tóm tắt ý tưởng đầu vào (≤200 ký tự)
  assumptions: []            # Danh sách giả định agent đã đưa ra
  confidence: medium         # low | medium | high — độ tự tin của agent
  generated_at: ""           # ISO 8601 timestamp
  generator_version: ""

# IMPLEMENTATION NOTES (hướng dẫn cho dev khi bắt tay code)
implementation_notes:
  suggested_tech_stack: []   # Gợi ý tech stack phù hợp
  open_questions: []         # Câu hỏi cần làm rõ trước khi code
  acceptance_criteria: []    # Tiêu chí nghiệm thu
```

---

## 5. Template file `.md` — Mode: Blueprint (Design-First)

```markdown
# [Function Name] *(Blueprint)*

> ⚠️ **BLUEPRINT** — Tài liệu này được sinh từ mô tả ý tưởng, chưa có code thực tế.
> Khi code được implement, hãy chạy lại skill ở mode `detailed` để cập nhật.

> **Schema file:** [`{prefix}_{tên}[_v{N}].yaml`](./{prefix}_{tên}[_v{N}].yaml)
> **Version:** 0.1.0-blueprint | **Status:** Blueprint | **Confidence:** [low/medium/high]

## Ý tưởng gốc

> [Mô tả ý tưởng / yêu cầu nghiệp vụ mà user đưa vào]

## Mô tả chức năng (dự kiến)

> **WHY**: [Tại sao function này cần tồn tại]

[Mô tả chức năng dự kiến]

## Tham số (dự kiến)

| Tên | Kiểu | Bắt buộc | Mô tả |
|-----|------|----------|-------|
| | | | |

## Response Schema (dự kiến)

```json
{
}
```

## Edge Cases (dự kiến)

| Case | Input | Kết quả dự kiến |
|------|-------|-----------------|
| | | |

## Giả định (Assumptions)

Agent đã đưa ra các giả định sau khi sinh docs này:
- [ ] [Giả định 1]
- [ ] [Giả định 2]

> ⚠️ Developer cần **xác nhận từng giả định** trước khi implement.

## Câu hỏi mở (Open Questions)

- [ ] [Câu hỏi cần giải đáp]

## Tiêu chí nghiệm thu (Acceptance Criteria)

- [ ] [Criterion 1]
- [ ] [Criterion 2]

## Gợi ý khi implement

- **Tech stack gợi ý:** [...]
- **Lưu ý bảo mật dự kiến:** [...]
- **Lưu ý hiệu năng dự kiến:** [...]
```
