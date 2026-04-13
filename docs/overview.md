# StoryHub Documentation Overview

> Tài liệu này tổng hợp blueprint cho hệ thống StoryHub theo mode design-first (chưa có code).
> Mục tiêu: đủ rõ để team có thể bắt đầu build và giữ nhất quán giữa backend, frontend, và vận hành.

## 1) Phạm vi hệ thống

StoryHub gồm 6 khối nghiệp vụ:

1. Inventory (Kho)
2. CRM (Khách hàng)
3. POS (Bán hàng)
4. Rental (Cho thuê)
5. Report (Báo cáo)
6. System (Phân quyền, log, backup, tích hợp)

## 2) Kiến trúc đề xuất

- Frontend: Vue 3 + Tauri (desktop kiosk)
- Backend: FastAPI (local service)
- ORM/DB: SQLAlchemy + SQLite, lộ trình SQLCipher
- Mô hình triển khai: offline-first, local-first, đồng bộ tùy chọn

## 3) Mô hình dữ liệu cốt lõi

Truyện phải tách thành 3 tầng:

1. Title (đầu truyện)
2. Volume (tập)
3. Item (cuốn vật lý)

Toàn bộ giao dịch thuê/bán thao tác trên `Item`.

Bắt buộc có snapshot giá tại thời điểm giao dịch:

- `final_sell_price`
- `final_rent_price`
- `final_deposit`

Mục đích: tránh sai lịch sử khi bảng giá thay đổi.

## 4) Ràng buộc bắt buộc (critical)

- Transaction locking để tránh 2 người thao tác cùng 1 item
- Idempotency để chống scan/click lặp gây nhân đôi giao dịch
- Soft delete để giữ lịch sử và phục vụ audit
- Audit log có before/after và actor
- Validation chống dữ liệu âm, sai số lượng, sai trạng thái
- Reservation có expiry real-time + cron cleanup

## 5) Nguyên tắc UI/UX vận hành

- Keyboard-first, mouse-optional
- Global barcode listener không phụ thuộc focus input
- Buffer scanner + timeout khoảng 50ms để phân biệt gõ tay
- Mỗi hành động có feedback màu + âm thanh + highlight
- Layout POS 3 cột: Scan/Tìm kiếm - Giỏ hàng/Phiếu thuê - Thanh toán
- Mục tiêu thao tác: tối đa 3 bước cho luồng chuẩn

## 6) Danh sách API Blueprint

| Nhóm      | API                       | File docs                                                                               |
| --------- | ------------------------- | --------------------------------------------------------------------------------------- |
| Inventory | Reserve item              | [bp_inventory-reserve-item_v1.md](./api-reference/v1/bp_inventory-reserve-item_v1.md)   |
| CRM       | Upsert customer           | [bp_crm-upsert-customer_v1.md](./api-reference/v1/bp_crm-upsert-customer_v1.md)         |
| POS       | Create order              | [bp_pos-create-order_v1.md](./api-reference/v1/bp_pos-create-order_v1.md)               |
| POS       | Refund order              | [bp_pos-refund-order_v1.md](./api-reference/v1/bp_pos-refund-order_v1.md)               |
| Rental    | Create contract           | [bp_rental-create-contract_v1.md](./api-reference/v1/bp_rental-create-contract_v1.md)   |
| Rental    | Return items + settlement | [bp_rental-return-items_v1.md](./api-reference/v1/bp_rental-return-items_v1.md)         |
| Rental    | Extend contract           | [bp_rental-extend-contract_v1.md](./api-reference/v1/bp_rental-extend-contract_v1.md)   |
| Metadata  | Autofill title data       | [bp_metadata-autofill-title_v1.md](./api-reference/v1/bp_metadata-autofill-title_v1.md) |
| Report    | Revenue summary           | [bp_report-revenue-summary_v1.md](./api-reference/v1/bp_report-revenue-summary_v1.md)   |
| System    | Create backup             | [bp_system-create-backup_v1.md](./api-reference/v1/bp_system-create-backup_v1.md)       |

## 7) Tài liệu nền bổ sung

### Domain và Lifecycle

- Domain Item: [domain_item.md](./domain/domain_item.md)
- Domain Rental Contract: [domain_rental-contract.md](./domain/domain_rental-contract.md)
- Data Flow Rental Return Settlement: [dataflow_rental-return-settlement.md](./domain/dataflow_rental-return-settlement.md)
- Lifecycle Item: [lifecycle_item.md](./lifecycle/lifecycle_item.md)
- Lifecycle Rental Contract: [lifecycle_rental-contract.md](./lifecycle/lifecycle_rental-contract.md)

### Event System

- Item status changed: [event_item-status-changed.md](./events/event_item-status-changed.md)
- Rental settled: [event_rental-settled.md](./events/event_rental-settled.md)

### UI Contract và User Flow

- UI POS Main Kiosk: [ui_pos-main-kiosk.md](./ui-contracts/ui_pos-main-kiosk.md)
- UI Rental Return Inspection: [ui_rental-return-inspection.md](./ui-contracts/ui_rental-return-inspection.md)
- Flow POS Checkout: [flow_pos-checkout.md](./user-flows/flow_pos-checkout.md)
- Flow Rental Return: [flow_rental-return.md](./user-flows/flow_rental-return.md)

### Configuration và nền tảng kỹ thuật

- Runtime Config: [config_storyhub-runtime.yaml](./config/config_storyhub-runtime.yaml)
- Database schema: [schema_storyhub-core.md](./database/schema_storyhub-core.md)
- Rental lifecycle logic: [logic_rental-lifecycle.md](./business-logic/logic_rental-lifecycle.md)
- Barcode listener logic: [logic_barcode-keyboard-buffer.md](./business-logic/logic_barcode-keyboard-buffer.md)
- Security, audit, locking: [logic_security-audit-and-locking.md](./business-logic/logic_security-audit-and-locking.md)

### Realtime và Migration

- Realtime Item Live Updates: [realtime_item-live-updates.yaml](./realtime/realtime_item-live-updates.yaml)
- Migration Blueprint -> Implementation v1: [migration_blueprint-to-implementation-v1.md](./migrations/migration_blueprint-to-implementation-v1.md)

### Lộ trình thực hiện dự án

- How-to triển khai theo giai đoạn: [howto_project-implementation-steps.md](./how-to/howto_project-implementation-steps.md)

## 8) Trạng thái tài liệu

- Tất cả API hiện ở trạng thái `blueprint`
- Domain, Lifecycle, Event, UI Contract và User Flow đang ở trạng thái design-first
- Realtime contract và migration runbook đã có bản v1 để team triển khai đồng bộ
- Khi có code thật: chạy lại skill ở code-first mode để chuyển `blueprint -> implemented`
- Chỉ export OpenAPI cho endpoint đã implemented hoặc verified

## 9) Chuẩn phát triển và phát hành

- Từ điển thuật ngữ chuẩn: [standard_terminology-glossary.md](./standards/standard_terminology-glossary.md)
- Quy ước coding và workflow cộng tác: [standard_coding-and-collaboration.md](./standards/standard_coding-and-collaboration.md)
- Hướng dẫn setup môi trường cho developer mới: [howto_development-environment-setup.md](./how-to/howto_development-environment-setup.md)
- Lịch sử thay đổi theo phiên bản phát hành: [CHANGELOG.md](../CHANGELOG.md)
