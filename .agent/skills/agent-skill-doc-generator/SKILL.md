---
name: agent-skill-doc-generator
description: "Full-stack Agent-native Specification System v2.0 — Sinh tài liệu dual-output tách file (.yaml + .md) cho cả developer lẫn AI agent. Bao phủ TOÀN BỘ stack: Domain Model (invariants, aggregates, business rules), Lifecycle/State Machine, Event System, API Contract, UI Contract (states, interactions, auth_ui), User Flow, SDK/Client generation, Configuration Layer, Realtime/WebSocket, Contract Testing & Mock. Enhanced Behavior Contract (preconditions, postconditions, failure strategy), Enhanced Permission (ABAC), Enhanced Dependency Graph (ordered, conditional, fallback). Tự động phân tích project scale (Tier 1/2/3) với complexity scoring. Hỗ trợ Blueprint Mode, Runtime Feedback Loop, Migration tracking. Dùng cho mọi dự án từ nhỏ đến lớn."
argument-hint: "Đường dẫn source code HOẶC mô tả ý tưởng; ngôn ngữ/framework; mức chi tiết (summary | detailed | schema-only); mode (code-first | blueprint); tier (auto | starter | standard | enterprise); doc types (api | domain | lifecycle | event | ui | flow | config | realtime | all); thư mục output (tùy chọn)"
user-invocable: true
---

# Skill: Agent Skill Doc Generator

## Mục tiêu

Skill này sinh tài liệu **dual-output tách riêng file** cho mỗi function/tool/module trong dự án:
- **Machine-readable (`.yaml`)** — AI agent parse trực tiếp, dùng cho orchestration
- **Human-readable (`.md`)** — Developer đọc hiểu, dùng cho onboarding và reference

Tài liệu sinh ra phải đủ để:
1. Agent load file `.yaml` trực tiếp vào tool registry (không cần parse markdown)
2. Developer mở file `.md` và hiểu chức năng, edge cases, security trong 5 phút
3. Hệ thống validate tự động (syntax, type, semantic) cho từng loại file riêng biệt

## Khi nào dùng

- Cần tạo tài liệu cho API endpoints, service functions, utility modules
- Cần tài liệu mà AI agent có thể sử dụng trực tiếp để gọi tools
- Cần chuẩn hóa doc format cho toàn bộ dự án
- Cần upgrade docs hiện có thành dạng machine-readable
- Cần tạo tool registry cho agent orchestration system
- Cần onboard developer mới vào dự án nhanh chóng
- **Cần thiết kế API/module trước khi viết code (Blueprint Mode)**

## Tài liệu tham chiếu

> ⚠️ **QUAN TRỌNG**: Các file phụ chứa templates, conventions, ví dụ nằm trong thư mục `resources/`.
> Agent PHẢI đọc file phụ tương ứng khi cần thông tin chi tiết.

| File | Nội dung | Khi nào đọc |
|---|---|---|
| [`resources/templates.md`](./resources/templates.md) | Templates trống cho YAML/MD (detailed, schema-only, blueprint) | Khi bắt đầu sinh output |
| [`resources/conventions.md`](./resources/conventions.md) | Naming convention, anti-patterns, quality checklist, CI/CD script | Khi cần kiểm tra quy tắc đặt tên hoặc validate |
| [`resources/examples.md`](./resources/examples.md) | Full examples (getUserData) + prompt mẫu gọi skill | Khi cần tham khảo output mẫu hoàn chỉnh |
| [`resources/deprecation-flow.md`](./resources/deprecation-flow.md) | Quy trình deprecated API version (v1→v2) | Khi có breaking change cần deprecate |
| [`resources/openapi-interop.md`](./resources/openapi-interop.md) | Import/export OpenAPI spec, bảng mapping | Khi dự án có hoặc cần OpenAPI spec |
| [`resources/domain-modeling.md`](./resources/domain-modeling.md) | Domain Model, Lifecycle/State Machine, Event System templates | Khi sinh domain/lifecycle/event docs |
| [`resources/frontend-contracts.md`](./resources/frontend-contracts.md) | UI Contract, User Flow, SDK/Client generation templates | Khi sinh frontend docs hoặc UI specs |
| [`resources/runtime-execution.md`](./resources/runtime-execution.md) | Enhanced Behavior, Failure Strategy, Config, ABAC, Observability | Khi cần behavior contract nâng cao |
| [`resources/testing-contracts.md`](./resources/testing-contracts.md) | Contract Testing, Mock Gen, Realtime, Migration templates | Khi sinh testing/realtime/migration docs |

---

## Kiến trúc tổng quan

```
┌──────────────────────────────────────────────────────────────────┐
│                    INPUT LAYER                                    │
│  Nhánh A: Source Code + Project Structure + Dependencies          │
│  Nhánh B: Ý tưởng / User Stories / Mô tả nghiệp vụ              │
│           (Blueprint Mode — khi chưa có code)                     │
└──────────────────────┬───────────────────────────────────────────┘
                       ▼
┌──────────────────────────────────────────────────────────────────┐
│              MODE DETECTION & ROUTING                              │
│  Có source code? → Code-First (Nhánh A)                           │
│  Chỉ có ý tưởng? → Blueprint (Nhánh B)                           │
│  User chỉ định?  → Theo user                                     │
└──────────────────────┬───────────────────────────────────────────┘
                       ▼
┌──────────────────────────────────────────────────────────────────┐
│              MULTI-LAYER PROCESSING ENGINE                        │
│                                                                    │
│  Layer 1: Domain Analysis                                         │
│    → Extract invariants, aggregates, business rules                │
│    → Detect state machines, events                                 │
│                                                                    │
│  Layer 2: API & Backend Contract                                  │
│    → Context → Intent Extraction → IR                              │
│    → Enhanced Behavior (preconditions, postconditions, failure)    │
│    → ABAC Permission Model                                        │
│    → Ordered Dependency Graph                                      │
│                                                                    │
│  Layer 3: Frontend Contract                                       │
│    → UI States, Data Binding, Interactions                         │
│    → User Flow (multi-step UX)                                     │
│    → SDK/Client Hooks Generation                                   │
│                                                                    │
│  Layer 4: Runtime & Testing                                       │
│    → Configuration Layer                                           │
│    → Contract Tests + Mock Generation                              │
│    → Realtime/WebSocket specs                                      │
│                                                                    │
│  Dual Output per doc type:                                         │
│    ├─ Dev Doc (.md)                                                │
│    └─ Agent Schema (.yaml)                                         │
└──────────────────────┬───────────────────────────────────────────┘
                       ▼
┌──────────────────────────────────────────────────────────────────┐
│          CROSS-FILE VALIDATION LOOP (3 tầng)                       │
│  Syntax Validation → Type Matching → Semantic Validation           │
│  + Cross-reference Validation (domain↔lifecycle↔event↔api↔ui)     │
└──────────────────────┬───────────────────────────────────────────┘
                       ▼
┌──────────────────────────────────────────────────────────────────┐
│                   OUTPUT LAYER                                     │
│  Multi-type outputs: api_, domain_, lifecycle_, event_,            │
│    ui_, flow_, config_, realtime_, migration_                      │
│  + Version metadata + Quality report + Runtime Feedback            │
│  → Ghi vào cấu trúc thư mục chuẩn + cập nhật registry             │
└──────────────────────────────────────────────────────────────────┘
```

---

## 1. Cấu trúc Thư mục Linh hoạt (Adaptive Directory Structure)

### 1.1. Nguyên tắc cốt lõi

> **KHÔNG tạo thư mục trống.** Chỉ tạo thư mục khi có nội dung thực sự cần ghi vào.
> Cấu trúc docs được **grow-on-demand** — bắt đầu nhỏ, mở rộng khi dự án phát triển.

Skill tự phân tích dự án để chọn **tier** phù hợp. User cũng có thể chỉ định tier hoặc override.

### 1.2. Bảng Project Signals — Agent tự phát hiện tier

Agent quét project rồi tính điểm dựa trên các tín hiệu sau:

**Bảng A — Base Signals (tín hiệu cơ bản):**

| Tín hiệu | Cách phát hiện | Điểm |
|---|---|---|
| Số lượng API endpoints/routes | Đếm route definitions trong code | +1/endpoint |
| Số lượng database tables/models | Đếm model/schema files | +1/model |
| Có CI/CD config | `.github/workflows/`, `Jenkinsfile`... | +3 |
| Có Docker/Compose | `Dockerfile`, `docker-compose.yml` | +2 |
| Có tests | `__tests__/`, `*.test.*`, `*.spec.*` | +2 |
| Có nhiều hơn 1 service/package | Monorepo, microservices | +5 |
| Có auth/middleware phức tạp | JWT, OAuth, RBAC... | +3 |
| Có queue/worker/cron | Redis queue, BullMQ, cron jobs | +3 |
| Số lượng contributors | git log, CODEOWNERS | +1/person |
| Tổng lines of code | `cloc` hoặc ước lượng | +1 mỗi 2000 LOC |

**Bảng B — Complexity Signals (tín hiệu phức tạp — v2.0):**

| Tín hiệu phức tạp | Cách phát hiện | Điểm |
|---|---|---|
| AI/ML pipeline | Import tensorflow, torch, openai, langchain... | +8 |
| Complex state machine (>5 states) | Phát hiện enum states, FSM pattern, XState | +5 |
| Event-driven architecture | Event emitter, RabbitMQ, Kafka, Redis Pub/Sub | +4 |
| Multi-tenant | Tenant context, schema isolation, tenant middleware | +5 |
| Real-time / WebSocket | ws, socket.io, SSE imports | +3 |
| CRUD-only pattern (giảm điểm) | Chỉ có basic CRUD, không có business logic | -2 /endpoint |
| External API integrations (>3) | Nhiều HTTP client calls đến service khác | +3 |
| Complex auth (ABAC, policies) | Policy engine, attribute-based checks | +3 |
| File/media processing | Multer, sharp, ffmpeg, S3 upload | +2 |

> 💡 **Complexity signals giải quyết vấn đề**: 3 endpoint AI pipeline phải được tier cao hơn 20 endpoint CRUD đơn giản.

**Quy tắc chọn tier:**

```
Tổng = Base Signals + Complexity Signals

Tổng điểm 1-7   → Tier 1: Starter
Tổng điểm 8-20  → Tier 2: Standard
Tổng điểm 21+   → Tier 3: Enterprise

⚠️ OVERRIDE RULES:
- Bất kỳ signal nào ≥ +5 → tối thiểu Tier 2
- Có ≥ 2 signals ≥ +5    → tối thiểu Tier 3
```

> 💡 **User override**: Nếu user chỉ định tier cụ thể hoặc tên thư mục cụ thể → bỏ qua auto-detection, làm theo user.

> 💡 **Blueprint Mode**: Khi chưa có code, agent ước lượng tier dựa trên mô tả ý tưởng thay vì quét file:
> - Mô tả 1-3 endpoints đơn giản → Tier 1
> - Mô tả 4-15 endpoints, đề cập DB → Tier 2
> - Mô tả microservices, team lớn → Tier 3

### 1.3. Ba Tier cấu trúc

#### 🟢 Tier 1: Starter (dự án nhỏ, ≤ 7 điểm)

**Khi nào:** Script, CLI tool, library nhỏ, API dưới 5 endpoints, side project

```
docs/
├── api_auth-login_v1.md           # Docs đặt thẳng trong docs/
├── api_auth-login_v1.yaml         # Không cần thư mục con
├── api_get-user_v1.md
├── api_get-user_v1.yaml
└── README.md                      # (tùy chọn) Tổng quan ngắn
```

**Đặc điểm:**
- ❌ Không tạo thư mục con (quá ít file, không cần phân loại)
- ✅ Vẫn giữ naming convention (prefix + kebab-case)
- ✅ Vẫn tách `.md` + `.yaml`
- Tổng dự kiến: **2-10 files**

---

#### 🟡 Tier 2: Standard (dự án trung bình, 8-20 điểm)

**Khi nào:** Backend có 5-20 endpoints, có database, 1-3 developers

```
docs/
├── overview.md                        # 1 file overview (không cần thư mục riêng)
│
├── api-reference/                     # Gộp API docs
│   ├── v1/
│   │   ├── api_auth-login_v1.md
│   │   ├── api_auth-login_v1.yaml
│   │   ├── api_get-user_v1.md
│   │   └── api_get-user_v1.yaml
│   └── webhooks/
│       ├── wh_payment-success.md
│       └── wh_payment-success.yaml
│
├── database/                          # Schema docs (nếu có DB)
│   ├── schema_users.md
│   └── schema_transactions.md
│
└── business-logic/                    # (tùy chọn, chỉ tạo khi logic phức tạp)
    └── logic_role-permissions.md
```

**Đặc điểm:**
- ✅ Có thư mục con, nhưng **không đánh số** (dưới 5 thư mục, không cần sort)
- ✅ `overview.md` là 1 file đơn, không cần thư mục `00-overview/`
- ✅ Chỉ tạo thư mục khi có ≥ 2 files thuộc loại đó
- Tổng dự kiến: **10-40 files**

---

#### 🔴 Tier 3: Enterprise (dự án lớn, 21+ điểm)

**Khi nào:** Monolith lớn, microservices, team > 3 người, 20+ endpoints

```
docs/
├── 00-overview/                       # Giới thiệu & Onboarding
│   ├── project-setup.md
│   └── environment-vars.md
│
├── 01-architecture/                   # Kiến trúc & ADR
│   ├── system-context.md
│   └── adr_001_use-postgresql.md
│
├── 02-database/                       # Schema & ERD
│   ├── schema_users.md
│   └── schema_nfc-transactions.md
│
├── 03-api-reference/                  # API Docs — Dual-Output
│   ├── v1/
│   │   ├── api_auth-login_v1.md
│   │   ├── api_auth-login_v1.yaml
│   │   ├── api_scan-card-kiosk_v1.md
│   │   └── api_scan-card-kiosk_v1.yaml
│   └── webhooks/
│       ├── wh_payment-success.md
│       └── wh_payment-success.yaml
│
├── 04-business-logic/                 # Quy trình nghiệp vụ
│   ├── logic_role-permissions.md
│   └── logic_data-caching-strategy.md
│
├── 05-agent-prompts/                  # Prompt & Workflow cho Agent
│   ├── system_router.md
│   └── skill_data-extraction.md
│
└── {NN}-{tên-mới}/                   # Mở rộng khi cần
    └── ...
```

**Đặc điểm:**
- ✅ Thư mục **đánh số** `{NN}-` (nhiều thư mục, cần thứ tự đọc rõ ràng)
- ✅ Đầy đủ các loại docs
- ✅ Mở rộng thoải mái: `06-deployment/`, `07-testing/`, `08-integrations/`...
- Tổng dự kiến: **40+ files**

### 1.4. Module Catalog — Điều kiện tạo từng thư mục

Không phải tier nào cũng tạo mọi thư mục. Bảng dưới đây cho agent biết **khi nào nên tạo**:

| Module (thư mục) | Tier 1 | Tier 2 | Tier 3 | Điều kiện kích hoạt |
|---|---|---|---|---|
| `overview` / `00-overview/` | ❌ Bỏ qua | 📄 1 file `overview.md` | 📁 Thư mục | Luôn tạo (trừ Tier 1) |
| `architecture` / `01-architecture/` | ❌ Bỏ qua | ❌ Bỏ qua | 📁 Thư mục | Có > 2 services HOẶC user yêu cầu ADR |
| `database` / `02-database/` | ❌ Bỏ qua | 📁 Nếu có DB | 📁 Thư mục | Phát hiện ORM/database config |
| `api-reference` / `03-api-reference/` | 📄 File thẳng trong `docs/` | 📁 Thư mục | 📁 Thư mục + số | Có ≥ 1 API endpoint |
| `business-logic` / `04-business-logic/` | ❌ Bỏ qua | 📁 Nếu logic phức tạp | 📁 Thư mục | Có ≥ 2 quy trình nghiệp vụ phức tạp |
| `agent-prompts` / `05-agent-prompts/` | ❌ Bỏ qua | ❌ Bỏ qua | 📁 Nếu dùng AI | Dự án có AI/agent integration |
| `deployment` / `06-deployment/` | ❌ | ❌ | 📁 Nếu có CI/CD | Phát hiện Docker, k8s, CI config |
| `testing` / `07-testing/` | ❌ | ❌ | 📁 Nếu test phức tạp | Có > 50 test files HOẶC E2E tests |
| **`domain`** / `08-domain/` | ❌ Bỏ qua | 📁 Nếu có invariants | 📁 Thư mục | Có entity với business rules phức tạp |
| **`lifecycle`** / `09-lifecycle/` | ❌ Bỏ qua | 📁 Nếu có state machine | 📁 Thư mục | Entity có ≥ 3 trạng thái rõ ràng |
| **`events`** / `10-events/` | ❌ Bỏ qua | 📁 Nếu có event system | 📁 Thư mục | Phát hiện event emitter, queue, pub/sub |
| **`ui-contracts`** / `11-ui-contracts/` | ❌ Bỏ qua | 📁 Nếu có frontend | 📁 Thư mục | Dự án có frontend cần document |
| **`user-flows`** / `12-user-flows/` | ❌ Bỏ qua | 📁 Nếu flow phức tạp | 📁 Thư mục | Feature có ≥ 3 bước user interaction |
| **`config`** / `13-config/` | ❌ Bỏ qua | 📁 Nếu có config phức tạp | 📁 Thư mục | Có ≥ 3 config values ảnh hưởng logic |
| **`realtime`** / `14-realtime/` | ❌ Bỏ qua | ❌ Bỏ qua | 📁 Nếu có WS/SSE | Phát hiện WebSocket, SSE, MQTT |
| **`migrations`** / `15-migrations/` | ❌ Bỏ qua | ❌ Bỏ qua | 📁 Khi có breaking change | Có API deprecation hoặc schema change |

> 💡 **Grow-on-demand**: Khi user chạy skill lần sau và dự án đã phát triển, agent **tự nâng tier** nếu signals thay đổi.

### 1.5. Quy tắc nâng/hạ Tier

```
Khi chạy skill trên dự án có docs/ sẵn:
1. Quét project signals → tính tier hiện tại
2. So sánh với cấu trúc docs/ hiện có:
   - Nếu tier MỚI > tier CŨ → đề xuất restructure (KHÔNG tự ý làm)
   - Nếu tier MỚI = tier CŨ → giữ nguyên cấu trúc, chỉ thêm file mới
   - Nếu tier MỚI < tier CŨ → giữ nguyên (KHÔNG bao giờ hạ tier)
3. Nếu restructure: tạo migration plan, hỏi user xác nhận trước khi di chuyển files
```

### 1.6. Nguyên tắc tổ chức chung (áp dụng mọi tier)

- **Naming convention**: prefix + kebab-case — xem chi tiết tại [`resources/conventions.md`](./resources/conventions.md)
- **Dual-output**: API docs luôn có cặp `.md` + `.yaml` — dù file nằm ở đâu
- **Versioning bằng thư mục con `v1/`**: chỉ áp dụng khi đã có thư mục `api-reference/` (Tier 2+)
- **Webhooks tách riêng**: thư mục `webhooks/` nằm trong `api-reference/`
- **Không tạo thư mục trống**: thư mục chỉ xuất hiện khi có ≥ 1 file bên trong
- **Đánh số `{NN}-`**: chỉ dùng cho Tier 3 (nhiều thư mục, cần ordering)
- **Mở rộng tự do**: Tier 3 có thể thêm `06-`, `07-`... tùy nhu cầu

---

## 2. Input Layer — Thu thập context

### 2.1. Code-First Mode (có source code)

| Loại context | Mô tả | Bắt buộc? |
|---|---|---|
| **Source Code** | Code của function/module cần document | ✅ Bắt buộc |
| **Project Structure** | Cây thư mục dự án | ✅ Bắt buộc |
| **Dependencies / Imports** | Các module/package được import | ✅ Bắt buộc |
| **Runtime Context** | Runtime version (Node 20, Python 3.12...) | ✅ Bắt buộc |
| **Config** | Database, API keys (placeholder), cache, queue | ⚠️ Nên có |
| **Sample Input/Output** | Ví dụ request/response thực tế | ⚠️ Nên có |
| **Existing Docs** | Tài liệu hiện có (nếu có) | ⚠️ Nên có |
| **Test Files** | Unit tests liên quan | 🟡 Optional |
| **Error Logs** | Lỗi thường gặp | 🟡 Optional |

> ⚠️ Nếu thiếu Runtime Context → agent có thể hiểu sai logic. Luôn ưu tiên thu thập đủ trước khi sinh docs.

**Dependency Detection Fallback — Annotations trong source code:**

Khi code quá phức tạp để Agent tự suy luận dependency từ import, developer có thể gắn annotation `@doc-*` vào comment. Agent sẽ **ưu tiên annotations hơn tự suy luận**. Nếu không có annotations → fallback về phân tích import/require.

```typescript
// @doc-requires: authenticate, validateUserRole
// @doc-provides: user_context, user_permissions
// @doc-conflicts: deleteUser
// @doc-category: core/user
// @doc-priority: high
// @doc-side-effects: read-only
export async function getUserData(userId: string) { ... }
```

### 2.2. Blueprint Mode (chưa có code — Design-First)

| Loại context | Mô tả | Bắt buộc? |
|---|---|---|
| **Ý tưởng / Mô tả nghiệp vụ** | Text mô tả chức năng cần thiết kế | ✅ Bắt buộc |
| **User Stories** | Các câu chuyện người dùng (nếu có) | ⚠️ Nên có |
| **Tech Stack dự kiến** | Ngôn ngữ, framework, database dự định | ⚠️ Nên có |
| **Wireframe / UI mô tả** | Giao diện dự kiến (text hoặc hình ảnh) | 🟡 Optional |
| **Competitor / Reference API** | API tham khảo từ hệ thống tương tự | 🟡 Optional |

> 💡 **Blueprint Mode giúp:**
> - Thiết kế API contract trước khi code → team đồng thuận sớm
> - Sinh acceptance criteria cho dev team
> - Phát hiện thiếu sót trong ý tưởng trước khi tốn công implement
> - Tạo mock API documentation cho frontend team làm việc song song

---

## 3. Processing Engine — Pipeline chuẩn

### 3.1. Quy trình xử lý

```
Mode Detection (Code-First hoặc Blueprint?)
  → Context Collection (khác nhau theo mode)
  → Multi-Layer Analysis:
      Layer 1: Domain Analysis
        → Extract invariants, aggregates, business rules
        → Detect state machines (lifecycle), events
      Layer 2: API & Backend Contract
        → Intent Extraction (xác định function purpose)
        → IR Generation (Intermediate Representation)
        → Enhanced Behavior (preconditions, postconditions, failure strategy)
        → ABAC Permission Model
        → Ordered Dependency Graph
      Layer 3: Frontend Contract (nếu dự án có frontend)
        → UI States, Data Binding, Interactions
        → User Flow (multi-step UX)
        → SDK/Client Hooks
      Layer 4: Runtime & Testing
        → Configuration extraction
        → Contract Test generation
        → Mock data generation
        → Realtime/WebSocket specs (nếu có)
  → Dual Output Generation (TÁCH RIÊNG FILE, mỗi doc type)
      ├─ Dev Doc Generator  → {name}.md
      └─ Agent Schema Gen   → {name}.yaml
  → Cross-File Validation Loop (3 tầng + cross-reference)
  → Registry Update → _registry.yaml
  → Runtime Feedback Check (nếu có monitoring data)
  → Packaging & Output (ghi vào cấu trúc thư mục chuẩn)
```

### 3.2. IR — Intermediate Representation (lớp trung gian)

IR là bước **bắt buộc** trước khi sinh output. IR chứa:

```yaml
# IR template — KHÔNG phải output cuối, chỉ dùng nội bộ
ir:
  function_name: "getUserData"
  purpose: "Lấy thông tin user theo ID từ database"
  module: "user-service"
  mode: "code-first"           # code-first | blueprint
  
  # Thông tin để sinh file name theo convention
  output_config:
    prefix: "api"                           # Prefix theo bảng chuẩn (bp_ nếu blueprint)
    short_name: "get-user-data"             # Tên ngắn gọn, kebab-case
    version: "v1"                           # Version API
    target_dir: "docs/03-api-reference/v1/" # Thư mục đích (hoặc auto theo tier)
  
  # Source Tracking (Code-First) HOẶC Blueprint Tracking (Blueprint Mode)
  source_fingerprint:                       # Chỉ dùng cho Code-First
    files:
      - path: "src/services/user.service.ts"
        hash: "sha256:a1b2c3d4..."
    generated_at: "2024-03-15T10:30:00Z"
  
  blueprint_fingerprint:                    # Chỉ dùng cho Blueprint Mode
    prompt_hash: "sha256:..."               # Hash của ý tưởng đầu vào
    prompt_summary: "API quản lý user: get, create, update, delete"
    assumptions:                            # Giả định agent đưa ra
      - "Dùng UUID v4 làm primary key"
      - "Soft delete thay vì hard delete"
    confidence: medium                      # low | medium | high
  
  inputs:
    - name: user_id
      type: string
      required: true
      constraints: "UUID v4 format"
      
  outputs:
    - name: user
      type: object
      properties:
        - name: name
          type: string
          
  side_effects:
    - type: "database_read"
      target: "users table"
      
  error_cases:
    - condition: "user_id không tồn tại"
      error_type: "NotFoundError"
      
  dependencies:
    - "database connection pool"
    - "authentication middleware"
    
  auth_requirements:
    - "Bearer Token"
    - "Role: admin hoặc self"
```

**Lợi ích của IR:**
- Tránh lệch giữa `.md` & `.yaml` (cùng một nguồn sự thật)
- Tự động suy ra file name và target directory từ `output_config`
- Không phải parse lại code nhiều lần
- Dễ validate consistency giữa 2 file output

---

## 4. Dual Output — Nguyên tắc tách file

### Nguyên tắc cốt lõi

```
IR (nguồn sự thật)
  ├─→ {name}.yaml    # Agent parse trực tiếp, không cần đọc markdown
  └─→ {name}.md      # Dev đọc trực tiếp, không bị nhiễu bởi YAML
```

**Tại sao tách riêng:**
- ✅ Agent load `.yaml` trực tiếp vào tool registry → nhanh, chính xác
- ✅ Dev mở `.md` → sạch sẽ, chỉ có nội dung cần đọc
- ✅ Validate riêng: YAML dùng schema validation, Markdown dùng linter
- ✅ CI/CD dễ xử lý: agent registry chỉ scan `*.yaml`
- ✅ IDE có syntax highlight riêng cho từng loại file

> 📖 **Full examples cho cả `.yaml` lẫn `.md`**: xem [`resources/examples.md`](./resources/examples.md)
> 📝 **Templates trống để copy**: xem [`resources/templates.md`](./resources/templates.md)

### Các phần trong file `.yaml`

| Phần | Mục đích | Bắt buộc? |
|---|---|---|
| **Identity** | Agent biết tool này là gì | ✅ Bắt buộc |
| **HTTP Endpoint** | Agent biết gọi API ở đâu | ✅ (cho API) |
| **Parameters** | Agent biết truyền gì vào | ✅ Bắt buộc |
| **Returns** | Agent biết nhận gì ra | ✅ Bắt buộc |
| **Behavior Contract** | Preconditions, postconditions, failure strategy, retry/cache | ✅ Bắt buộc |
| **Error Schema** | Agent xử lý lỗi thế nào | ✅ Bắt buộc |
| **Auth Context** | ABAC permissions, frontend auth | ✅ Bắt buộc |
| **Tool Dependencies** | Ordered, conditional, fallback dependencies | ⚠️ Nên có |
| **Rate Limiting** | Giới hạn tần suất | ⚠️ Nên có |
| **Performance** | Set timeout hợp lý | ⚠️ Nên có |
| **Structured Examples** | Self-validate output | ⚠️ Nên có |
| **Versioning** | Changelog | ⚠️ Nên có |
| **Source/Blueprint Tracking** | Phát hiện doc outdated | ⚠️ Nên có |
| **Client / SDK** | Typed hooks, mock adapter | ⚠️ Nên có (v2.0) |
| **Testing** | Contract tests, mock data, frontend scenarios | ⚠️ Nên có (v2.0) |
| **Frontend Hints** | Loading strategy, error surface, cache strategy | ⚠️ Nên có (v2.0) |
| **Environment** | Chạy ở đâu | 🟡 Optional |
| **Observability** | Technical + business metrics, tracing, feedback loop | 🟡 Optional |

---

## 5. Validation Loop — 3 tầng kiểm tra (Cross-File)

### Tầng 1: Syntax Validation (mỗi file riêng)

```
File .yaml:
✅ YAML parse thành công (không lỗi syntax)
✅ Tất cả required fields có giá trị
✅ Types hợp lệ (string, integer, boolean...)
✅ File name đúng naming convention: {prefix}_{name}[_v{N}].yaml

File .md:
✅ Markdown render đúng (headings, tables, code blocks)
✅ Có đủ sections tối thiểu: Mô tả, Tham số, Ví dụ
✅ File name khớp với file .yaml tương ứng
✅ Có link đến file .yaml ở đầu
```

### Tầng 2: Type Matching (cross-file consistency)

```
Kiểm tra giữa .yaml và .md:
✅ Parameters trong .yaml khớp với bảng Tham số trong .md
✅ Returns schema trong .yaml khớp với Response Schema trong .md
✅ Error codes trong .yaml khớp với Edge Cases trong .md
✅ Auth roles trong .yaml khớp với Lưu ý bảo mật trong .md
✅ Version trong .yaml khớp với Changelog trong .md
✅ doc_ref trong .yaml trỏ đúng file .md
✅ Link schema trong .md trỏ đúng file .yaml
```

### Tầng 3: Semantic Validation

```
Kiểm tra:
✅ Examples trong .yaml có thể chạy được (input hợp lệ → output khớp schema)
✅ Error examples trigger đúng error code
✅ Behavior contract hợp lý (VD: side_effects="read-only" + idempotent=true → OK)
✅ Dependencies chain không circular
✅ Rate limit hợp lý với latency
✅ Auth scope phù hợp với side_effects
✅ File name version khớp với version trong nội dung
```

### Validation Report

```
📋 Validation Report — getUserData v1.2.0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📂 Files:
   ├─ api_get-user-data_v1.yaml  ✅ Valid YAML
   └─ api_get-user-data_v1.md    ✅ Valid Markdown

✅ Tầng 1 — Syntax      : PASS (0 errors)
✅ Tầng 2 — Type Match   : PASS (0 mismatches)
✅ Tầng 3 — Semantic      : PASS (0 issues)
⚠️ Warnings              : 1
   └─ cache_ttl (300s) > suggested max for user data (180s)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Result: PASS ✅
```

> 📖 **Full checklist quality gates**: xem [`resources/conventions.md`](./resources/conventions.md) (Section 4)

---

## 6. Granularity Control — 4 chế độ output

| Mode | Output files | Khi nào dùng | Chi phí token |
|---|---|---|---|
| **`schema-only`** | Chỉ file `.yaml` (rút gọn) | Agent cần parse tool nhanh | Thấp |
| **`summary`** | `.yaml` đầy đủ + `.md` ngắn | Quick reference | Trung bình |
| **`detailed`** | `.yaml` đầy đủ + `.md` đầy đủ | Onboarding, full docs | Cao |
| **`blueprint`** | `.yaml` blueprint + `.md` blueprint | Design-First, chưa có code | Trung bình |

### Cách chọn mode

```
Nếu user chỉ định mode → dùng mode đó
Nếu user không chỉ định:
  - Không có code, chỉ có ý tưởng → blueprint
  - Function đơn giản (< 20 dòng, không side effects) → summary
  - Function phức tạp (> 50 dòng, có side effects, nhiều params) → detailed
  - Chỉ cần cho agent registry → schema-only
```

---

## 7. Quy trình thực thi

### Bước 1: Xác định Mode

```
1. User cung cấp input:
   - Có đường dẫn source code → Code-First Mode
   - Chỉ có mô tả ý tưởng/user stories → Blueprint Mode
   - User chỉ định rõ mode → theo user
2. Nếu Blueprint Mode: bỏ qua bước quét source code, chuyển thẳng sang Bước 3
```

### Bước 2: Thu thập context (Code-First)

```
1. Đọc source code của function/module cần document
2. Đọc file imports để xác định dependencies
   - Ưu tiên annotations @doc-* nếu có
   - Fallback: phân tích import/require
3. Đọc runtime config (package.json, .env.example, tsconfig...)
4. Đọc test files liên quan (nếu có)
5. Đọc existing docs (nếu có) + đọc source_tracking hash từ .yaml cũ
6. Tạo project profile (runtime, framework, DB engine...)
7. Tính hash SHA-256 cho mỗi source file liên quan (cho staleness detection)
```

### Bước 2b: Thu thập context (Blueprint Mode)

```
1. Nhận mô tả ý tưởng / user stories / wireframe từ user
2. Phân tích ý tưởng → liệt kê endpoints/functions cần thiết
3. Ước lượng tech stack nếu user không chỉ định
4. Tính hash SHA-256 của prompt ý tưởng (cho blueprint_tracking)
5. Nếu thiếu thông tin quan trọng → hỏi user (tối đa 5 câu)
```

### Bước 3: Phân tích Project Profile & Chọn Tier

```
1. Code-First: Quét project signals (Section 1.2)
   Blueprint: Ước lượng tier từ mô tả (Section 1.2 ghi chú Blueprint)
2. Kiểm tra thư mục docs/ đã tồn tại chưa:
   - Nếu chưa → tạo cấu trúc theo tier đã chọn
   - Nếu rồi → so sánh tier mới vs cũ (Section 1.5)
3. Staleness Detection (Code-First, nếu docs/ đã tồn tại):
   - Đọc source_tracking.files[].hash từ các file .yaml hiện có
   - Tính hash SHA-256 hiện tại của từng source file
   - So sánh: hash CŨ ≠ hash MỚI → đánh dấu doc đó là STALE
   - Báo cáo: "X docs cần update, Y docs vẫn fresh"
   - Chỉ regenerate docs bị STALE (tiết kiệm token)
4. Xác định modules cần tạo theo Module Catalog (Section 1.4)
5. Xác nhận granularity mode (Section 6)
6. Nếu thiếu context quan trọng → hỏi user (tối đa 5 câu)
```

> ⚠️ Nếu agent detect tier khác với mong đợi → PHẢI thông báo user.

### Bước 4: Sinh IR (Intermediate Representation)

```
Với MỖI function/module:
1. Extract: tên, purpose, inputs, outputs
2. Analyze: side effects, error cases, auth requirements
   - Blueprint Mode: suy luận từ mô tả, đánh dấu confidence level
3. Detect: dependencies, rate limits, environment constraints
4. Tính toán output_config: prefix (api_ hoặc bp_), short_name, version, target_dir
5. Validate IR: đủ thông tin để sinh CẢ 2 file output
```

### Bước 5: Sinh Dual Output (2 file riêng biệt)

```
Từ IR, sinh TUẦN TỰ:
1. Sinh file .yaml theo template tương ứng (xem resources/templates.md)
   - Code-First: dùng template detailed/schema-only + source_tracking
   - Blueprint: dùng template blueprint + blueprint_tracking
   - Bao gồm doc_ref trỏ đến file .md
2. Sinh file .md theo template tương ứng
   - Blueprint: thêm banner ⚠️ BLUEPRINT ở đầu trang
   - Bao gồm link đến file .yaml ở đầu
3. Kiểm tra naming convention đúng cho cả 2 file
4. Ghi cả 2 file vào thư mục đích
```

### Bước 6: Cross-File Validation Loop

```
1. Syntax Validation (mỗi file riêng) → fix nếu lỗi
2. Type Matching (cross-file) → fix nếu lệch giữa .yaml và .md
3. Semantic Validation → cảnh báo nếu có vấn đề
   - Blueprint Mode: giảm mức nghiêm ngặt (cho phép thiếu performance data)
4. Sinh Validation Report
```

### Bước 7: Output & Báo cáo

```
1. Xác nhận files đã ghi đúng vị trí trong cấu trúc thư mục
2. Cập nhật Registry Index _registry.yaml (Section 8)
3. Sinh báo cáo tổng hợp:
   - Số lượng cặp files đã tạo (.yaml + .md)
   - Số lượng docs updated (incremental) vs sinh mới
   - Số lượng blueprint docs (nếu có)
   - Số lượng docs bị stale còn lại (chưa update)
   - Cấu trúc thư mục output
   - Validation results (PASS/FAIL/WARNING)
   - Gợi ý cải thiện (nếu có)
```

---

## 8. Registry Index — Tool discovery tự động

### File `_registry.yaml`

Mỗi khi sinh hoặc update docs, skill **tự động tạo/cập nhật** file `_registry.yaml` ở root `docs/`:

```yaml
# File: docs/_registry.yaml
# AUTO-GENERATED — Không sửa tay, skill tự cập nhật mỗi lần chạy

project:
  name: "my-api-project"
  tier: "standard"
  total_tools: 12
  total_blueprints: 3              # Số lượng docs ở trạng thái blueprint
  total_stale: 2                   # Số docs cần update (source code đã đổi)
  last_full_scan: "2024-03-15T10:30:00Z"
  doc_types_generated:             # Loại docs đã sinh (v2.0)
    - api
    - domain
    - lifecycle
    - event
    - ui
    - flow
    - config

tools:
  - name: getUserData
    path: "api-reference/v1/api_get-user-data_v1.yaml"
    version: "1.2.0"
    deprecated: false
    status: "implemented"          # implemented | blueprint | verified
    tags: ["user-management", "read-only"]
    category: "core/user"
    method: GET
    endpoint: "/api/v1/users/:user_id"
    stale: false

  - name: createCart
    path: "api-reference/v1/bp_cart-create_v1.yaml"
    version: "0.1.0-blueprint"
    deprecated: false
    status: "blueprint"            # ← Blueprint — chưa có code
    tags: ["cart", "e-commerce"]
    category: "core/cart"
    method: POST
    endpoint: "/api/v1/carts"
    stale: false

schemas:
  - name: "users"
    path: "database/schema_users.md"

logic:
  - name: "role-permissions"
    path: "business-logic/logic_role-permissions.md"

# === CÁC SECTION MỚI (v2.0) ===

domains:                           # Domain models
  - name: "user"
    path: "domain/domain_user.yaml"
    invariants_count: 3
  - name: "borrowing"
    path: "domain/domain_borrowing.yaml"
    invariants_count: 5

lifecycles:                        # State machines
  - name: "book"
    path: "lifecycle/lifecycle_book.yaml"
    states_count: 5
    transitions_count: 7

events:                            # System events
  - name: "book_borrowed"
    path: "events/event_book-borrowed.yaml"
    consumers_count: 4
  - name: "book_returned"
    path: "events/event_book-returned.yaml"
    consumers_count: 3

ui_contracts:                      # Frontend contracts
  - name: "UserProfile"
    path: "ui-contracts/ui_user-profile.yaml"
    states_count: 6
    related_api: "api_get-user_v1"

user_flows:                        # User flows
  - name: "borrow-book"
    path: "user-flows/flow_borrow-book.md"
    steps_count: 6

configs:                           # Configuration
  - name: "borrowing"
    path: "config/config_borrowing.yaml"
    values_count: 5

realtime:                          # Realtime channels
  - name: "library-updates"
    path: "realtime/realtime_library-updates.yaml"
    protocol: "websocket"
    events_count: 3
```

### Quy tắc quản lý registry

```
1. File tên PHẢI là `_registry.yaml` (prefix `_` để luôn ở đầu khi sort)
2. Đặt ở root thư mục docs/
3. AUTO-GENERATED: skill tự tạo/cập nhật sau mỗi lần chạy
4. Agent load file này TRƯỚC → biết ngay có bao nhiêu tool, ở đâu
5. Bao gồm thông tin stale và blueprint status
6. KHÔNG sửa tay — mọi thay đổi sẽ bị ghi đè lần chạy sau
7. Section mới (v2.0): domains[], lifecycles[], events[], ui_contracts[], user_flows[], configs[], realtime[]
```

### Registry trong từng Tier

| Tier | Registry | Nội dung |
|---|---|---|
| **Tier 1: Starter** | `docs/_registry.yaml` | Chỉ `tools[]` (đủ dùng) |
| **Tier 2: Standard** | `docs/_registry.yaml` | `tools[]` + `schemas[]` + `domains[]` + `lifecycles[]` + `ui_contracts[]` |
| **Tier 3: Enterprise** | `docs/_registry.yaml` | Đầy đủ TẤT CẢ sections |

---

## 9. Blueprint → Implementation — Chuyển đổi trạng thái

Khi developer đã viết code xong cho một blueprint doc:

```
1. User chạy skill trỏ vào source code thật
2. Agent phát hiện đã có blueprint docs (status: blueprint) cho cùng function
3. Agent so sánh: IR từ code thật vs IR từ blueprint
4. Sinh docs mới (mode detailed) từ code thật
5. Ghi đè file cũ:
   - .yaml: xóa blueprint_tracking, thêm source_tracking, đổi status → implemented
   - .md: xóa banner BLUEPRINT, cập nhật nội dung thực tế
6. Cập nhật _registry.yaml: đổi status từ "blueprint" → "implemented"
7. Báo cáo diff giữa blueprint vs thực tế:
   - Endpoints khớp / không khớp
   - Parameters thay đổi
   - Giả định đúng / sai
```

### Blueprint Enforcement (v2.0)

Để tránh "docs ảo" tồn tại mãi:

```
Khi chạy incremental scan:
1. Kiểm tra tuổi blueprint docs (blueprint_tracking.generated_at)
2. Nếu age > 30 ngày → WARNING trong report: "Blueprint cần review"
3. Nếu age > 90 ngày → AUTO-DEPRECATE:
   - Đổi status: "deprecated"
   - Thêm warning vào .md: "⚠️ Blueprint quá cũ, cần implement hoặc xóa"
   - Cập nhật _registry.yaml
4. Report liệt kê: X blueprints cần attention
```

---

## 10. Runtime Feedback Loop (v2.0)

Cơ chế phản hồi từ runtime → cập nhật docs:

```
Bước 8 (MỚI trong pipeline): Runtime Feedback Check

1. Nếu dự án có monitoring/observability data:
   - Đọc error rate thực tế → so sánh với error schema trong docs
   - Đọc latency thực tế → so sánh với performance.expected_latency_ms
   - Đọc top errors → kiểm tra có trong errors[] không

2. Nếu phát hiện drift:
   - Error code xuất hiện ở runtime nhưng không có trong docs
     → ⚠️ Gợi ý: "Thêm error case [CODE] vào error schema"
   - Latency thực tế >> expected
     → ⚠️ Gợi ý: "Update performance.expected_latency_ms"
   - API bị deprecated trên runtime nhưng docs chưa mark
     → ⚠️ Gợi ý: "Chạy deprecation flow"

3. Output: Runtime Feedback Report (kèm theo Validation Report)
```

> 💡 Runtime Feedback là **advisory** — agent gợi ý, developer quyết định có update không.

---

## 11. Doc Types tổng hợp (v2.0)

### Bảng tất cả doc types

| Prefix | Doc Type | Output | Khi nào dùng | Resource file |
|---|---|---|---|---|
| `api_` | API Endpoint | `.yaml` + `.md` | Có API endpoint | `templates.md` |
| `wh_` | Webhook | `.yaml` + `.md` | Có webhook | `templates.md` |
| `schema_` | Database Schema | `.md` only | Có database | `templates.md` |
| `logic_` | Business Logic | `.md` only | Logic phức tạp | `templates.md` |
| `adr_` | Architecture Decision | `.md` only | Enterprise tier | `conventions.md` |
| `system_` | Agent System Prompt | `.md` only | Có AI agent | `conventions.md` |
| `skill_` | Agent Skill | `.md` only | Có AI agent | `conventions.md` |
| `bp_` | Blueprint | `.yaml` + `.md` | Design-first mode | `templates.md` |
| `domain_` | Domain Model | `.yaml` + `.md` | Có business rules | `domain-modeling.md` |
| `lifecycle_` | State Machine | `.yaml` + `.md` | Entity có ≥3 states | `domain-modeling.md` |
| `event_` | System Event | `.yaml` + `.md` | Có event/async | `domain-modeling.md` |
| `dataflow_` | Data Flow | `.md` only | Data pipeline phức tạp | `domain-modeling.md` |
| `ui_` | UI Contract | `.yaml` + `.md` | Có frontend | `frontend-contracts.md` |
| `flow_` | User Flow | `.md` only | Multi-step UX | `frontend-contracts.md` |
| `config_` | Configuration | `.yaml` only | Có runtime config | `runtime-execution.md` |
| `realtime_` | Realtime Channel | `.yaml` only | Có WebSocket/SSE | `testing-contracts.md` |
| `migration_` | Migration | `.md` only | Breaking change | `testing-contracts.md` |

### Thứ tự Agent đọc docs (quan trọng)

```
1. _registry.yaml        → Biết có gì trong dự án
2. domain_*.yaml          → Hiểu luật chơi kinh doanh
3. lifecycle_*.yaml       → Hiểu trạng thái cho phép
4. config_*.yaml          → Hiểu giá trị cấu hình
5. api_*.yaml             → Biết cách gọi API
6. event_*.yaml           → Biết chuyện gì xảy ra sau API
7. ui_*.yaml              → Biết UI hiển thị gì
8. flow_*.md              → Hiểu full user journey
9. realtime_*.yaml        → Biết data realtime
```

> 📖 **Về deprecation API khi breaking change**: xem [`resources/deprecation-flow.md`](./resources/deprecation-flow.md)
> 📖 **Về tương thích OpenAPI**: xem [`resources/openapi-interop.md`](./resources/openapi-interop.md)
> 📖 **Prompt mẫu gọi skill**: xem [`resources/examples.md`](./resources/examples.md) (Section 3 & 4)
> 📖 **Về domain/lifecycle/event**: xem [`resources/domain-modeling.md`](./resources/domain-modeling.md)
> 📖 **Về UI contract/user flow/SDK**: xem [`resources/frontend-contracts.md`](./resources/frontend-contracts.md)
> 📖 **Về behavior nâng cao/failure/config**: xem [`resources/runtime-execution.md`](./resources/runtime-execution.md)
> 📖 **Về testing/realtime/migration**: xem [`resources/testing-contracts.md`](./resources/testing-contracts.md)
