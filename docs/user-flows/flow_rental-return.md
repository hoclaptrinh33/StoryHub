# Flow: Rental Return and Inspection

> Actors: Cashier, Manager (optional override), System
> Preconditions: Có contract hợp lệ và item đang trạng thái rented.
> Postconditions: Settlement được tạo, contract cập nhật trạng thái đúng.

## Tổng quan

Flow trả truyện ưu tiên scan nhanh, chọn condition nhanh và hiển thị ngay kết quả tiền cọc hoặc nợ.

## Happy Path

| Bước | Actor   | Hành động                       | System Response              | API/Event                 | UI State         |
| ---- | ------- | ------------------------------- | ---------------------------- | ------------------------- | ---------------- |
| 1    | Cashier | Scan item trả                   | Xác định contract liên quan  | local match               | empty -> success |
| 2    | Cashier | Duyệt condition mặc định tốt    | Tính tạm phí theo rule       | local fee calc            | success          |
| 3    | Cashier | Dùng phím 1/2/3/4 đổi condition | Cập nhật damage fee realtime | local state               | success          |
| 4    | Cashier | Nhấn Enter xác nhận             | Gọi settle API               | bp_rental-return-items_v1 | settling         |
| 5    | System  | Trả breakdown phí + cọc + nợ    | Cập nhật contract status     | event_rental-settled      | success          |

## Sơ đồ luồng

```text
Scan item -> Validate contract -> Inspect -> Submit settlement -> Show result
                           \-> invalid item -> warning
```

## Alternative Paths

### Alt 1: Trả một phần

| Bước | Thay đổi          | Xử lý                        |
| ---- | ----------------- | ---------------------------- |
| 5    | Còn item chưa trả | contract -> partial_returned |

### Alt 2: Item bị mất

| Bước | Thay đổi         | Xử lý                       |
| ---- | ---------------- | --------------------------- |
| 3    | condition = lost | tăng lost_fee, item -> lost |

## Edge Cases

| Case                           | Trigger         | System Response      | UI Response    |
| ------------------------------ | --------------- | -------------------- | -------------- |
| Scan item không thuộc contract | sai item        | ITEM_NOT_IN_CONTRACT | toast đỏ       |
| Item đã trả rồi                | scan trùng      | RETURN_DUPLICATED    | warning vàng   |
| Contract không tồn tại         | contract_id sai | CONTRACT_NOT_FOUND   | fullpage error |

## Error Recovery

| Lỗi                          | Bước xảy ra       | Recovery                        |
| ---------------------------- | ----------------- | ------------------------------- |
| INVALID_CONDITION_TRANSITION | trước submit      | ép chọn lại condition hợp lệ    |
| NETWORK_ERROR                | submit settlement | giữ local draft, cho retry ngay |
| LOCK_CONFLICT                | submit settlement | retry có backoff ngắn           |

## Related Docs

| Doc                                                                                  | Vai trò trong flow      |
| ------------------------------------------------------------------------------------ | ----------------------- |
| [bp_rental-return-items_v1.yaml](../api-reference/v1/bp_rental-return-items_v1.yaml) | API settle trả truyện   |
| [ui_rental-return-inspection.yaml](../ui-contracts/ui_rental-return-inspection.yaml) | Giao diện inspection    |
| [lifecycle_rental-contract.yaml](../lifecycle/lifecycle_rental-contract.yaml)        | Trạng thái contract     |
| [domain_rental-contract.yaml](../domain/domain_rental-contract.yaml)                 | Invariants tài chính    |
| [event_rental-settled.yaml](../events/event_rental-settled.yaml)                     | Side effects sau settle |
