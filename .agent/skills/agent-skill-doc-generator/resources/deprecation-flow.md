# Deprecation Flow — Quy trình khi API breaking change (v1 → v2)

> Tham chiếu từ `SKILL.md` chính.
> File này mô tả chi tiết quy trình deprecate một API version.

---

## 1. Quy trình deprecation

```
1. Tạo thư mục mới: docs/03-api-reference/v2/
2. Sinh cặp file mới: api_{tên}_v2.md + api_{tên}_v2.yaml
3. Cập nhật file v1:
   - Trong .yaml: đặt deprecated: true, thêm deprecated_by trỏ đến v2
   - Trong .md: thêm banner cảnh báo deprecated ở đầu trang
4. Giữ nguyên file v1 (KHÔNG xóa) cho đến khi hết sunset period
```

---

## 2. Đánh dấu deprecated trong file `.yaml` (v1)

```yaml
# File: api_get-user-data_v1.yaml (đã deprecated)
name: getUserData
version: 1.2.0
deprecated: true                          # ← Đánh dấu deprecated
deprecated_info:
  deprecated_since: "2024-06-01"          # Ngày bắt đầu deprecated
  sunset_date: "2024-12-01"               # Ngày ngừng hỗ trợ hoàn toàn
  replaced_by: "api_get-user-data_v2"     # Tên tool thay thế
  migration_guide: "api_get-user-data_v2.md#migration-từ-v1"  # Link hướng dẫn migrate
  reason: "Thay đổi response schema, thêm pagination support"
```

---

## 3. Banner deprecated trong file `.md` (v1)

```markdown
> ⚠️ **DEPRECATED** — API này sẽ ngừng hỗ trợ vào 2024-12-01.
> Vui lòng chuyển sang [getUserData v2](../v2/api_get-user-data_v2.md).
> Xem [hướng dẫn migrate](../v2/api_get-user-data_v2.md#migration-từ-v1).

# getUserData (v1) — DEPRECATED
...
```

---

## 4. Lifecycle tổng quan

```
┌──────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────┐
│  Active  │ ──→ │  Deprecated  │ ──→ │   Sunset     │ ──→ │ Archived │
│  (v1)    │     │  (v1 + v2)   │     │  (chỉ v2)    │     │ (xóa v1) │
└──────────┘     └──────────────┘     └──────────────┘     └──────────┘
     │                  │                    │                   │
   Hoạt động      v2 ra mắt,           Hết sunset          Xóa file v1
   bình thường    v1 deprecated         period              khỏi docs/
                  cả 2 version                              (hoặc move
                  cùng tồn tại                              vào archive/)
```

---

## 5. Quy tắc xử lý trong Registry

Khi deprecated:
- File `.yaml` v1 vẫn nằm trong `_registry.yaml` nhưng có `deprecated: true`
- Agent orchestration **ưu tiên gọi v2**, chỉ fallback sang v1 nếu v2 chưa sẵn sàng
- Sau sunset date: agent loại v1 khỏi registry hoàn toàn
