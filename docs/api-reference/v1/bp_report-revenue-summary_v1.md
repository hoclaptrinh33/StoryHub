# getRevenueSummaryReport (Blueprint)

> ⚠️ BLUEPRINT — Tài liệu sinh từ yêu cầu nghiệp vụ, chưa có code thực tế.

> Schema file: [bp_report-revenue-summary_v1.yaml](./bp_report-revenue-summary_v1.yaml)
> Version: 0.1.0-blueprint | Status: Blueprint | Confidence: High

## Ý tưởng gốc

Báo cáo phải phản ánh đúng doanh thu thực tế tại thời điểm giao dịch, không bị ảnh hưởng khi bảng giá thay đổi về sau.

## Mô tả chức năng (dự kiến)

Tổng hợp doanh thu bán, thuê, tiền phạt theo khoảng thời gian và trả thêm top truyện cùng cảnh báo tồn kho.

## Tham số (dự kiến)

| Tên                     | Kiểu     | Bắt buộc | Mô tả            |
| ----------------------- | -------- | -------- | ---------------- |
| from_date               | datetime | Có       | Mốc bắt đầu      |
| to_date                 | datetime | Có       | Mốc kết thúc     |
| group_by                | string   | Có       | day/week/month   |
| include_top_titles      | boolean  | Không    | Trả top truyện   |
| include_inventory_alert | boolean  | Không    | Trả cảnh báo kho |
| request_id              | string   | Có       | Idempotency key  |

## Response Schema (dự kiến)

```json
{
  "sell_revenue": 35000000,
  "rental_revenue": 12000000,
  "penalty_revenue": 1800000,
  "total_revenue": 48800000,
  "top_sell_titles": [{ "title": "One Piece", "qty": 120 }],
  "top_rent_titles": [{ "title": "Conan", "qty": 200 }],
  "inventory_alerts": [{ "title": "Doraemon", "available_items": 2 }]
}
```

## Edge Cases (dự kiến)

| Case               | Input                | Kết quả dự kiến        |
| ------------------ | -------------------- | ---------------------- |
| Date range sai     | from_date > to_date  | INVALID_DATE_RANGE     |
| Date range quá dài | vượt hạn mức query   | REPORT_RANGE_TOO_LARGE |
| Dữ liệu đang lock  | tác vụ nền đang chạy | DATA_SOURCE_LOCKED     |

## Giả định (Assumptions)

- [ ] Báo cáo dựa trên snapshot giá giao dịch.
- [ ] API read-only và có thể cache.
- [ ] Chỉ manager hoặc owner được truy cập.

## Câu hỏi mở (Open Questions)

- [ ] Có cần thêm biểu đồ so sánh theo kỳ trước không?
- [ ] Có cần xuất thẳng CSV/PDF từ API này không?

## Tiêu chí nghiệm thu (Acceptance Criteria)

- [ ] Tổng doanh thu bằng tổng các thành phần sell + rental + penalty.
- [ ] Top titles chính xác theo khoảng thời gian lọc.
- [ ] API vẫn ổn định khi dữ liệu lớn.

## Gợi ý khi implement

- Tech stack gợi ý: aggregate SQL + cache theo tham số báo cáo.
- Lưu ý bảo mật dự kiến: kiểm soát role trước khi chạy query nặng.
- Lưu ý hiệu năng dự kiến: dùng index theo `created_at` cho bảng order/rental_settlement.
