# returnRentalItems (Blueprint)

> ⚠️ BLUEPRINT — Tài liệu sinh từ yêu cầu nghiệp vụ, chưa có code thực tế.

> Schema file: [bp_rental-return-items_v1.yaml](./bp_rental-return-items_v1.yaml)
> Version: 0.1.0-blueprint | Status: Blueprint | Confidence: High

## Ý tưởng gốc

Luồng trả truyện là cốt lõi: scan item, kiểm định tình trạng, tính phí, khấu trừ cọc và hoàn tiền ngay tại quầy.

## Mô tả chức năng (dự kiến)

API xử lý trả item cho một contract, hỗ trợ trả thiếu nhiều lần, item mất, và tính settlement chi tiết theo rule.

## Tham số (dự kiến)

| Tên          | Kiểu          | Bắt buộc | Mô tả                              |
| ------------ | ------------- | -------- | ---------------------------------- |
| contract_id  | string        | Có       | Hợp đồng thuê cần xử lý            |
| return_lines | array<object> | Có       | Danh sách item + condition sau trả |
| returned_at  | datetime      | Không    | Thời điểm trả                      |
| request_id   | string        | Có       | Idempotency key                    |

## Response Schema (dự kiến)

```json
{
  "settlement_id": "RST-0001",
  "contract_id": "RCT-0001",
  "rental_fee": 30000,
  "late_fee": 10000,
  "damage_fee": 5000,
  "lost_fee": 0,
  "total_fee": 45000,
  "deducted_from_deposit": 45000,
  "refund_to_customer": 55000,
  "remaining_debt": 0,
  "contract_status": "partial_returned"
}
```

## Edge Cases (dự kiến)

| Case                      | Input                 | Kết quả dự kiến              |
| ------------------------- | --------------------- | ---------------------------- |
| Contract không tồn tại    | contract_id sai       | CONTRACT_NOT_FOUND           |
| Item không thuộc contract | return_lines sai item | ITEM_NOT_IN_CONTRACT         |
| Trả trùng item            | item đã trả trước đó  | RETURN_DUPLICATED            |
| Condition không hợp lệ    | state không đúng rule | INVALID_CONDITION_TRANSITION |

## Giả định (Assumptions)

- [ ] Rule phí có thể cấu hình từ backend.
- [ ] Trả một phần nhiều lần là luồng hợp lệ.
- [ ] Trường hợp item mất sẽ chuyển item status sang `lost`.

## Câu hỏi mở (Open Questions)

- [ ] Có cần chụp ảnh kiểm định trước/sau trả ngay trong API này không?
- [ ] Có cần in biên lai settle ngay sau khi trả không?

## Tiêu chí nghiệm thu (Acceptance Criteria)

- [ ] Settlement luôn trả breakdown đầy đủ và đúng công thức.
- [ ] Không thể trả item không thuộc contract.
- [ ] request_id trùng không tạo settle trùng.

## Gợi ý khi implement

- Tech stack gợi ý: fee engine độc lập + transaction contract-level lock.
- Lưu ý bảo mật dự kiến: cashier có quyền xử lý, manager có quyền override theo policy.
- Lưu ý hiệu năng dự kiến: prefetch rental_items theo contract trước khi validate từng line.
