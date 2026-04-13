# autofillTitleMetadata (Blueprint)

> ⚠️ BLUEPRINT — Tài liệu sinh từ yêu cầu nghiệp vụ, chưa có code thực tế.

> Schema file: [bp_metadata-autofill-title_v1.yaml](./bp_metadata-autofill-title_v1.yaml)
> Version: 0.1.0-blueprint | Status: Blueprint | Confidence: Medium

## Ý tưởng gốc

Khi nhập truyện mới, nhân viên chỉ cần nhập tên hoặc ISBN để hệ thống tự điền metadata, giảm nhập tay và sai sót.

## Mô tả chức năng (dự kiến)

API tìm metadata truyện từ cache local hoặc nguồn ngoài. Kết quả trả về có `source` để biết dữ liệu lấy từ đâu và độ tin cậy.

## Tham số (dự kiến)

| Tên           | Kiểu    | Bắt buộc | Mô tả                   |
| ------------- | ------- | -------- | ----------------------- |
| query_text    | string  | Không    | Tên truyện hoặc từ khóa |
| isbn          | string  | Không    | ISBN                    |
| force_refresh | boolean | Không    | Bỏ qua cache            |
| request_id    | string  | Có       | Idempotency key         |

## Response Schema (dự kiến)

```json
{
  "source": "cache",
  "cache_hit": true,
  "metadata": {
    "name": "Doraemon",
    "author": "Fujiko F. Fujio",
    "publisher": "Kim Dong",
    "genre": "Thiếu nhi",
    "description": "Mèo máy đến từ tương lai",
    "cover_url": "https://...",
    "confidence": 0.92
  }
}
```

## Edge Cases (dự kiến)

| Case              | Input                       | Kết quả dự kiến      |
| ----------------- | --------------------------- | -------------------- |
| Thiếu query       | query_text và isbn đều rỗng | INVALID_QUERY        |
| ISBN sai          | isbn không đúng chuẩn       | INVALID_ISBN         |
| API ngoài timeout | force_refresh=true          | EXTERNAL_API_TIMEOUT |
| Không có dữ liệu  | mọi nguồn fail              | METADATA_NOT_FOUND   |

## Giả định (Assumptions)

- [ ] Cache local luôn là nguồn ưu tiên.
- [ ] Có fallback khi nguồn ngoài lỗi.
- [ ] Metadata trả về có thể cần nhân viên xác nhận trước khi lưu.

## Câu hỏi mở (Open Questions)

- [ ] Có cho phép chỉnh sửa metadata trước khi lưu vào title không?
- [ ] Có lưu lịch sử nguồn metadata để audit không?

## Tiêu chí nghiệm thu (Acceptance Criteria)

- [ ] Trả kết quả đúng với nguồn dữ liệu thực tế.
- [ ] Timeout từ nguồn ngoài không làm treo luồng nhập kho.
- [ ] Có thể vận hành hoàn toàn offline bằng cache/fallback nội bộ.

## Gợi ý khi implement

- Tech stack gợi ý: adapter pattern cho nhiều metadata provider.
- Lưu ý bảo mật dự kiến: không lưu API key trong client desktop.
- Lưu ý hiệu năng dự kiến: cache theo khóa ISBN hoặc normalized query.
