# OpenAPI Interop — Tương thích chuẩn mở

> Tham chiếu từ `SKILL.md` chính.
> File này mô tả cách tương tác giữa skill doc format và OpenAPI/Swagger spec.

---

## 1. Vấn đề

Nhiều dự án đã có OpenAPI/Swagger spec. Skill không nên tạo hệ thống docs song song bị cô lập.

---

## 2. Hướng xử lý

| Tình huống | Hành động |
|---|---|
| Dự án **đã có** `openapi.yaml` | **Import**: Đọc OpenAPI spec → sinh IR → sinh dual-output |
| Dự án **chưa có** OpenAPI | **Generate**: Sinh dual-output từ source code (bình thường) |
| Cần **export** cho Swagger UI | **Export**: Từ `_registry.yaml` + các file `.yaml` → tổng hợp thành `openapi.yaml` |

---

## 3. Mapping giữa skill format và OpenAPI

| Skill `.yaml` field | OpenAPI equivalent | Ghi chú |
|---|---|---|
| `name` | `operationId` | Unique identifier |
| `description` | `summary` + `description` | OpenAPI tách 2 level |
| `http.method` | HTTP method key | `get`, `post`... |
| `http.path` | `paths.{path}` | Path pattern |
| `parameters` | `parameters` + `requestBody` | OpenAPI tách path/query/body riêng |
| `returns` | `responses.200.content.schema` | Chỉ map response thành công |
| `errors[]` | `responses.{status}` | Mỗi error → 1 response entry |
| `auth` | `security` + `securitySchemes` | OpenAPI dùng scheme reference |
| `tags[]` | `tags[]` | Tương đương |

---

## 4. Import từ OpenAPI

Khi phát hiện file `openapi.yaml`, `openapi.json`, hoặc `swagger.yaml` trong project:

```
1. Parse OpenAPI spec
2. Với MỖI path + method:
   a. Tạo IR từ OpenAPI fields (mapping theo bảng trên)
   b. BỔ SUNG thêm từ source code: behavior contract, dependencies, rate limit
      (những thứ OpenAPI KHÔNG có)
   c. Sinh cặp .yaml + .md như bình thường
3. Lợi ích: Không cần parse source code cho HTTP info — đã có trong OpenAPI
```

> ⚠️ **OpenAPI thiếu gì?** Behavior contract, tool dependencies, rate limiting,
> structured examples với input/output, auth ở mức tool-level.
> → Đó chính là giá trị thêm mà skill này cung cấp so với OpenAPI thuần.

---

## 5. Export sang OpenAPI

Khi user yêu cầu export:

```
1. Đọc docs/_registry.yaml để lấy danh sách tất cả API tools
2. Với mỗi tool có http.method + http.path:
   a. Map ngược từ skill format → OpenAPI format (theo bảng trên)
   b. Gộp vào 1 file openapi.yaml
3. Chỉ export tools KHÔNG deprecated
4. Output: openapi.yaml chuẩn 3.0+ đặt ở root project
```

> ⚠️ **Blueprint docs KHÔNG được export sang OpenAPI**.
> Vì blueprint chưa có code thật, export sẽ tạo OpenAPI spec sai lệch thực tế.
> Chỉ export docs có `status: implemented` hoặc `status: verified` (hoặc không có field status = mặc định là implemented).

---

## 6. Prompt mẫu

```
"Import OpenAPI spec từ docs/openapi.yaml, bổ sung behavior contracts từ source code"
```
→ Đọc OpenAPI → sinh IR → bổ sung từ code → sinh dual-output

```
"Export tất cả API docs thành file openapi.yaml"
```
→ Đọc registry → map ngược → tạo openapi.yaml chuẩn 3.0

```
"So sánh docs hiện có với openapi.yaml, tìm endpoints thiếu docs"
```
→ Diff registry vs OpenAPI spec → liệt kê endpoints chưa có docs
