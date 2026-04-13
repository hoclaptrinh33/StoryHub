# Conventions — Quy ước đặt tên, nguyên tắc thiết kế, checklist chất lượng

> File này chứa toàn bộ quy ước mà Agent PHẢI tuân thủ khi sinh docs.
> Tham chiếu từ `SKILL.md` chính.

---

## 1. Quy cách Đặt tên File (Naming Convention)

### 1.1. Bảng prefix chuẩn

| Prefix | Dùng cho | Thư mục chứa | Ví dụ |
|---|---|---|---|
| `api_` | API endpoints | `03-api-reference/` | `api_auth-login_v1.md` |
| `wh_` | Webhooks | `03-api-reference/webhooks/` | `wh_payment-success.md` |
| `schema_` | Database schemas | `02-database/` | `schema_users.md` |
| `logic_` | Business logic docs | `04-business-logic/` | `logic_role-permissions.md` |
| `adr_` | Architecture Decision Records | `01-architecture/` | `adr_001_use-postgresql.md` |
| `system_` | Agent system prompts | `05-agent-prompts/` | `system_router.md` |
| `skill_` | Agent skill definitions | `05-agent-prompts/` | `skill_data-extraction.md` |
| `bp_` | Blueprint docs (Design-First) | Theo tier | `bp_cart-checkout_v1.md` |
| `domain_` | Domain model (invariants, aggregates) | `08-domain/` | `domain_user.yaml` |
| `lifecycle_` | State machine / vòng đời entity | `09-lifecycle/` | `lifecycle_book.yaml` |
| `event_` | System events | `10-events/` | `event_book-borrowed.yaml` |
| `dataflow_` | Data flow / pipeline | `08-domain/` | `dataflow_borrow-book.md` |
| `ui_` | UI contract (frontend spec) | `11-ui-contracts/` | `ui_user-profile.yaml` |
| `flow_` | User flow (UX steps) | `12-user-flows/` | `flow_borrow-book.md` |
| `config_` | Configuration layer | `13-config/` | `config_borrowing.yaml` |
| `realtime_` | Realtime / WebSocket channel | `14-realtime/` | `realtime_library-updates.yaml` |
| `migration_` | Migration / evolution | `15-migrations/` | `migration_v1-to-v2.md` |

### 1.2. Quy tắc đặt tên

```
{prefix}_{tên-mô-tả-ngắn-gọn}[_v{phiên-bản}].{md|yaml}
```

**Chi tiết:**

| Quy tắc | Mô tả | Đúng ✅ | Sai ❌ |
|---|---|---|---|
| **Case** | Luôn dùng `kebab-case` (chữ thường, nối bằng `-`) | `api_auth-login_v1` | `api_AuthLogin_V1` |
| **Prefix bắt buộc** | Mỗi file phải có prefix theo bảng trên | `schema_users.md` | `users-schema.md` |
| **Phân cách** | Dùng `_` để tách prefix/tên/version, dùng `-` bên trong tên mô tả | `api_auth-login_v1` | `api-auth-login-v1` |
| **Version (nếu có)** | Suffix `_v{N}` trước extension | `api_auth-login_v1.md` | `api_auth-login.v1.md` |
| **Extension** | `.md` cho Dev, `.yaml` cho Agent | `api_auth-login_v1.yaml` | `api_auth-login_v1.yml` |
| **ADR đánh số** | Dùng `_NNN_` với 3 chữ số | `adr_001_use-postgresql` | `adr_1_use-postgresql` |

### 1.3. Dual-Output — Luôn đi theo cặp

Khi sinh docs cho API endpoint hoặc webhook, **luôn tạo cặp file**:

```
api_auth-login_v1.md       ← Developer đọc (Human-readable Markdown)
api_auth-login_v1.yaml     ← Agent parse (Machine-readable YAML)
```

**Quy tắc:**
- Cùng tên, chỉ khác extension
- Tạo đồng thời, không tạo lẻ
- Validation kiểm tra cross-file consistency

---

## 2. Nguyên tắc thiết kế quan trọng

### ✅ Nguyên tắc đúng

| Nguyên tắc | Lý do |
|---|---|
| Tách riêng `.yaml` và `.md` | Agent parse nhanh, Dev đọc sạch, validate riêng biệt |
| IR để giữ consistency | Một nguồn sự thật cho cả 2 file output |
| Cross-reference giữa 2 file | `doc_ref` trong YAML, link trong MD → dễ navigate |
| Naming convention thống nhất | Nhìn tên file biết ngay loại, nội dung, version |
| Numbered directories | Thứ tự đọc rõ ràng, dễ onboard (chỉ Tier 3) |
| Validation cross-file | Phát hiện drift giữa 2 file kịp thời |
| Error schema bắt buộc | Agent không biết xử lý lỗi = hệ thống fragile |
| Auth context bắt buộc | Tránh agent gọi tool rồi mới biết không quyền |
| Tool dependencies rõ ràng | Tránh gọi sai thứ tự, gây side effects |
| Behavior contract đầy đủ | Agent orchestration phụ thuộc hoàn toàn vào đây |

---

## 3. Chống mẫu xấu (Anti-patterns)

### Về cấu trúc file
- ❌ Gộp YAML frontmatter vào file `.md` (dùng cách cũ)
- ❌ Tạo file `.yaml` mà đặt tên không theo naming convention
- ❌ Bỏ qua error schema vì "function đơn giản"
- ❌ Copy behavior contract giống nhau cho mọi function
- ❌ Để `description` quá ngắn kiểu "Does stuff" hoặc quá dài

### Về cấu trúc thư mục
- ❌ Tạo thư mục trống "phòng hờ" (vi phạm nguyên tắc grow-on-demand)
- ❌ Dùng numbered prefix (`01-`, `02-`...) cho Tier 1 hoặc Tier 2 (chỉ Tier 3 mới cần)
- ❌ Ép dự án nhỏ theo cấu trúc Enterprise — để skill tự chọn tier
- ❌ Trộn lẫn docs và source code trong cùng thư mục
- ❌ Không tạo thư mục version (`v1/`) cho API docs khi ở Tier 2+
- ❌ Hạ tier khi restructure — tier chỉ tăng, không giảm
- ❌ Sửa tay `_registry.yaml` — file này auto-generated

### Về nội dung
- ❌ Examples không khớp giữa `.yaml` và `.md`
- ❌ Auth context trong `.yaml` nói "required: true" nhưng `.md` không đề cập security
- ❌ Behavior nói "read-only" nhưng function thực tế write database
- ❌ Dependencies liệt kê nhưng thiếu `requires` tool thực sự cần

### Về consistency (cross-file)
- ❌ Parameters trong `.yaml` có 3 fields nhưng bảng Tham số trong `.md` liệt kê 5
- ❌ Error code trong `.yaml` khác tên với Edge Cases trong `.md`
- ❌ Version trong `.yaml` khác với Changelog trong `.md`
- ❌ `doc_ref` trong `.yaml` trỏ sai tên file `.md`
- ❌ Link schema trong `.md` trỏ sai tên file `.yaml`

### Về bảo mật
- ❌ Hardcode API key, database credentials trong examples
- ❌ Liệt kê internal endpoints không nên public
- ❌ Bỏ qua auth context cho function có side effects

### Về Domain / Lifecycle / Event (v2.0)
- ❌ Tạo domain doc mà không có invariant nào
- ❌ Lifecycle chỉ có 2 states (quá đơn giản, không cần state machine)
- ❌ Event không có consumer nào (event mà không ai lắng nghe = vô nghĩa)
- ❌ `lifecycle_*.via` trỏ đến API không tồn tại
- ❌ `event_*.triggered_by` trỏ đến API không tồn tại
- ❌ Domain doc nhưng không liệt kê `related_apis`

### Về Frontend / UI Contract (v2.0)
- ❌ UI contract không có error state (chỉ có success = incomplete)
- ❌ UI contract không có loading state
- ❌ `data_binding.source` trỏ đến API không tồn tại
- ❌ Error codes trong `error_handling` không match với API
- ❌ User flow không có edge case nào
- ❌ User flow không có error recovery

### Về Runtime / Behavior (v2.0)
- ❌ Precondition nhưng không chỉ định `check_via` (agent không biết verify bằng cách nào)
- ❌ Failure strategy nói retry nhưng không có `max_retries`
- ❌ Config không có default value
- ❌ Copy behavior contract giống nhau cho mọi function (thiếu preconditions riêng)

---

## 4. Checklist Quality Gates

### Bắt buộc (MUST PASS)

**File `.yaml`:**
- [ ] YAML parse thành công, không lỗi syntax
- [ ] Có đủ 6 phần bắt buộc: Identity, Parameters, Returns, Behavior, Errors, Auth
- [ ] `name` không rỗng và unique trong project
- [ ] `description` mô tả rõ ràng, dưới 200 ký tự
- [ ] `doc_ref` trỏ đúng file `.md` tương ứng
- [ ] Mỗi parameter có `type` và `description`
- [ ] Required parameters được đánh dấu
- [ ] Ít nhất 1 error case được định nghĩa
- [ ] Behavior contract hợp lý (không mâu thuẫn logic)
- [ ] File name đúng naming convention

**File `.md`:**
- [ ] Markdown render đúng
- [ ] Có link đến file `.yaml` ở đầu trang
- [ ] Có ít nhất: mô tả, tham số, 1 example
- [ ] File name khớp với file `.yaml` (chỉ khác extension)
- [ ] Không chứa secrets, tokens, passwords thật

**Cross-file:**
- [ ] Parameters khớp nhau giữa 2 file
- [ ] Error codes khớp nhau giữa 2 file
- [ ] Version khớp nhau giữa 2 file

### Khuyến khích (SHOULD PASS)

- [ ] Có ít nhất 2 structured examples trong `.yaml` (1 happy path + 1 error case)
- [ ] Có edge cases documentation trong `.md`
- [ ] Có performance notes trong `.md`
- [ ] Có security notes trong `.md`
- [ ] Type matching giữa `.yaml` và `.md`: 0 mismatch
- [ ] Semantic validation: 0 issues
- [ ] Tags và category được gán hợp lý trong `.yaml`
- [ ] Dependencies chain không circular
- [ ] Rate limit được cấu hình

### Optional (NICE TO HAVE)

- [ ] Observability metrics defined trong `.yaml`
- [ ] Environment constraints specified
- [ ] Version changelog đầy đủ trong cả 2 file
- [ ] Migration hints cho breaking changes
- [ ] Response schema example trong `.md`

---

## 5. CI/CD Validation Script (Mẫu)

### GitHub Actions — Validate tính nhất quán docs

```yaml
# File: .github/workflows/validate-docs.yml
name: Validate Docs Consistency

on:
  pull_request:
    paths:
      - 'docs/**'

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      # Kiểm tra mọi file .yaml parse thành công
      - name: Validate YAML syntax
        run: |
          find docs/ -name "*.yaml" ! -name "_registry.yaml" | while read f; do
            echo "Checking $f..."
            python3 -c "import yaml; yaml.safe_load(open('$f'))" || exit 1
          done

      # Kiểm tra mỗi file .yaml (trong api-reference/) có file .md tương ứng
      - name: Check dual-output pairing
        run: |
          find docs/ -path "*/api-reference/*.yaml" | while read yaml_file; do
            md_file="${yaml_file%.yaml}.md"
            if [ ! -f "$md_file" ]; then
              echo "❌ MISSING pair: $yaml_file has no matching .md file"
              exit 1
            fi
          done
          echo "✅ All YAML/MD pairs are complete"

      # Kiểm tra naming convention
      - name: Check naming convention
        run: |
          find docs/ -name "*.yaml" -o -name "*.md" | while read f; do
            basename=$(basename "$f")
            # Bỏ qua README, overview, _registry
            if [[ "$basename" =~ ^(README|overview|_registry) ]]; then continue; fi
            # Kiểm tra prefix pattern
            if ! echo "$basename" | grep -qE '^(api|wh|schema|logic|adr|system|skill|bp)_'; then
              echo "❌ BAD NAME: $basename — phải bắt đầu bằng prefix chuẩn"
              exit 1
            fi
          done
          echo "✅ All files follow naming convention"

      # Kiểm tra doc_ref trong .yaml trỏ đúng file
      - name: Check doc_ref links
        run: |
          find docs/ -name "*.yaml" ! -name "_registry.yaml" | while read f; do
            doc_ref=$(python3 -c "import yaml; d=yaml.safe_load(open('$f')); print(d.get('doc_ref',''))" 2>/dev/null)
            if [ -n "$doc_ref" ] && [ "$doc_ref" != "None" ]; then
              dir=$(dirname "$f")
              if [ ! -f "$dir/$doc_ref" ]; then
                echo "❌ BROKEN doc_ref: $f → $doc_ref (file not found)"
                exit 1
              fi
            fi
          done
          echo "✅ All doc_ref links are valid"
```

### Dependency Detection Annotations

Khi code quá phức tạp để Agent tự phát hiện dependency, developer có thể dùng annotation trong source code:

```typescript
// @doc-requires: authenticate, validateUserRole
// @doc-provides: user_context, user_permissions
// @doc-conflicts: deleteUser
// @doc-category: core/user
// @doc-priority: high
export async function getUserData(userId: string) { ... }
```

```python
# @doc-requires: authenticate, validate_user_role
# @doc-provides: user_context
# @doc-side-effects: read-only
def get_user_data(user_id: str) -> dict: ...
```

Agent khi quét code sẽ **ưu tiên annotation `@doc-*`** hơn tự suy luận từ import. Nếu không tìm thấy annotation → fallback về phân tích import/require như bình thường.
