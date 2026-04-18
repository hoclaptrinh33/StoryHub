# How-to: Các bước thực hiện dự án StoryHub

> Loại tài liệu: How-to Guide  
> Đối tượng: Team triển khai (PM, Backend, Frontend, QA, DevOps)  
> Mục tiêu: Đi từ bộ docs blueprint hiện tại đến bản chạy thử nội bộ có thể demo end-to-end.

## 1) Phạm vi và đầu ra

Tài liệu này mô tả các bước triển khai dự án theo giai đoạn, tập trung vào:

- Dựng kiến trúc local-first theo đúng blueprint
- Triển khai API cốt lõi và UI vận hành kiosk
- Kết nối dữ liệu, realtime, báo cáo, backup
- Đạt chuẩn kiểm thử để sẵn sàng UAT

Đầu ra kỳ vọng:

- 01 bản ứng dụng desktop chạy được luồng bán và thuê-trả
- 01 backend local service ổn định với dữ liệu SQLite
- 01 bộ kiểm thử tối thiểu (API contract + UI flow smoke)

## 2) Điều kiện tiên quyết

- Đã có docs trong thư mục `docs/` (API, domain, lifecycle, UI contracts, migration).
- Mỗi vai trò có owner rõ ràng cho từng module.
- Chốt môi trường phát triển thống nhất:
  - Python + FastAPI cho backend
  - Vue 3 + Tauri cho frontend desktop
  - SQLite cho local database

## 3) Lộ trình thực hiện theo giai đoạn (chi tiết)

### Giai đoạn 0: Khởi động dự án (0.5-1 ngày)

Mục tiêu: Chốt phạm vi đợt 1, thiết lập cách làm việc thống nhất, khóa rủi ro ngay từ đầu.

Đầu vào bắt buộc:

- Bộ tài liệu tại `docs/` đã được team xác nhận.
- Danh sách nhân sự theo vai trò PM, Backend, Frontend, QA.
- Mốc thời gian triển khai dự kiến.

Công việc chi tiết:

1. PM chốt phạm vi MVP: Inventory, CRM, POS, Rental Return, Revenue Report cơ bản.
2. Tech Lead chốt kiến trúc logic: local-first, backend service nội bộ, desktop kiosk.
3. PM tạo backlog theo module và gán owner từng hạng mục.
4. Team chốt Definition of Done cho ticket backend, frontend, test, tài liệu.
5. QA tạo khung test plan mức cao cho các luồng chính và lỗi chính.
6. PM lập risk register phiên bản đầu, ghi rõ rủi ro và người theo dõi.

Tiêu chí hoàn thành giai đoạn:

- Backlog sprint 1 đã ưu tiên theo mức độ phụ thuộc.
- Mỗi epic có owner, reviewer, hạn hoàn thành.
- Có lịch họp daily, review, retrospective rõ ràng.

Sản phẩm bàn giao:

- Backlog sprint 1.
- Biên bản kickoff và danh sách quyết định kiến trúc.
- Tài liệu quy ước làm việc của team.

### Giai đoạn 1: Dựng khung kỹ thuật (1-2 ngày) - Đã hoàn thành ✅

Mục tiêu: Có skeleton chạy local cho cả backend và frontend, sẵn sàng cho phát triển song song.

Đầu vào bắt buộc:

- Quy ước branch, commit, code review từ giai đoạn 0.
- Runtime config chuẩn tại `docs/config/config_storyhub-runtime.yaml`.

Công việc chi tiết:

1. Backend tạo project FastAPI với cấu trúc module theo nhóm API v1.
2. Backend thêm route health check, chuẩn hóa response envelope thành công và lỗi.
3. Frontend khởi tạo Vue 3 + Tauri, tạo shell layout kiosk và route chính.
4. Team tạo script chạy local đồng nhất cho dev mới.
5. Thiết lập logging cơ bản cho cả backend và frontend.
6. Thiết lập kiểm tra chất lượng tối thiểu: lint, format, pre-commit hoặc tương đương.

Tiêu chí hoàn thành giai đoạn:

- Dev mới có thể clone và chạy app theo hướng dẫn trong dưới 30 phút.
- Health check backend và shell frontend đều chạy ổn định.
- Không còn cấu hình thủ công nằm ngoài tài liệu.

Sản phẩm bàn giao:

- Skeleton backend/frontend chạy local.
- Script khởi động môi trường dev.
- Tài liệu setup nhanh cho thành viên mới.

### Giai đoạn 2: Dữ liệu và schema cốt lõi (2-3 ngày) - Đã hoàn thành ✅

Mục tiêu: Hoàn tất mô hình dữ liệu bền vững cho luồng bán và thuê-trả.

Đầu vào bắt buộc:

- `docs/database/schema_storyhub-core.md`.
- Domain docs và lifecycle docs.

Công việc chi tiết:

1. Thiết kế bảng theo ba lớp Title, Volume, Item và các bảng giao dịch liên quan.
2. Thêm ràng buộc dữ liệu bắt buộc: không âm, khóa ngoại, trạng thái hợp lệ.
3. Tạo index cho truy vấn nóng: barcode item, contract theo trạng thái, order theo thời gian.
4. Bổ sung cột phục vụ audit và soft delete cho bảng nghiệp vụ trọng yếu.
5. Viết migration script khởi tạo mới và script rollback tương ứng.
6. Seed dữ liệu mẫu phục vụ test POS, Rental, Report.

Tiêu chí hoàn thành giai đoạn:

- Database có thể dựng mới hoàn toàn bằng migration script.
- Truy vấn chính không bị full scan bất thường trên dữ liệu seed.
- Constraint vi phạm trả lỗi rõ ràng và nhất quán.

Sản phẩm bàn giao:

- Bộ migration đầu tiên và rollback.
- Dữ liệu seed mẫu theo kịch bản nghiệp vụ.
- Danh sách index và lý do thiết kế.

### Giai đoạn 3: Triển khai API cốt lõi (3-5 ngày) - Đã hoàn thành ✅

Mục tiêu: Hoàn thành API có thể chạy luồng nghiệp vụ chính và chịu được lỗi vận hành cơ bản.

Đầu vào bắt buộc:

- Bộ API blueprint tại `docs/api-reference/v1/`.
- Logic docs tại `docs/business-logic/`.

Công việc chi tiết:

1. Tạo lớp dùng chung cho auth, kiểm tra role, request_id, error mapping.
2. Triển khai Inventory reserve item với lock, expiry và cleanup.
3. Triển khai CRM upsert customer có kiểm tra dữ liệu đầu vào.
4. Triển khai POS create/refund với snapshot giá tại thời điểm giao dịch.
5. Triển khai Rental create/extend/return với tính phí, cọc, hoàn cọc.
6. Bổ sung idempotency cho endpoint có side effects.
7. Ghi audit log before/after cho thao tác tạo và cập nhật quan trọng.
8. Chuẩn hóa mã lỗi theo blueprint để frontend xử lý ổn định.

Tiêu chí hoàn thành giai đoạn:

- API trả đúng status code và payload theo blueprint.
- Không tạo giao dịch trùng khi replay cùng request_id.
- Không cho phép thao tác sai trạng thái item hoặc contract.

Sản phẩm bàn giao:

- Bộ API cốt lõi chạy được trên môi trường dev.
- Contract test pass cho nhóm endpoint đã triển khai.
- Log audit đọc được và truy vết được actor.

### Giai đoạn 4: Triển khai UI kiosk chính (3-4 ngày) - Đã hoàn thành ✅

Mục tiêu: Người vận hành có thể thực hiện trọn luồng bán và thuê-trả trên desktop app.

Đầu vào bắt buộc:

- UI contract docs tại `docs/ui-contracts/`.
- User flow docs tại `docs/user-flows/`.

Công việc chi tiết:

1. Xây dựng màn POS kiosk 3 cột ưu tiên thao tác nhanh. **Áp dụng "Fast Checkout" UX**: Luồng Mua đứt (POS) mặc định không bắt buộc thu thập/tạo thông tin khách hàng để giảm tối đa rào cản.
2. Xây dựng flow Thuê truyện (Rental). **Áp dụng "Zero Friction CRM"**: Ở đơn thuê, tích hợp gõ tên tìm kiếm khách hoặc tự động tạo khách hàng mới ngầm định ngay tại form, loại bỏ hoàn toàn các Modal Thêm Khách Hàng cồng kềnh.
3. Tích hợp barcode listener toàn cục, không phụ thuộc focus input.
4. Cài buffer timeout để tách scanner và nhập tay.
5. Xây dựng màn Rental return inspection theo đúng state machine.
6. Đồng bộ loading, error, success theo frontend scenarios trong blueprint.
7. Chuẩn hóa keyboard shortcuts cho tác vụ thường dùng.
8. Hiển thị cảnh báo rõ ràng khi lock conflict hoặc dữ liệu hết hiệu lực.

Tiêu chí hoàn thành giai đoạn:

- Flow POS checkout chạy trọn vẹn không cần chuột trong kịch bản chuẩn.
- Flow rental return hiển thị đúng phí, cọc, trạng thái kết toán.
- Người dùng nội bộ thao tác được sau thời gian hướng dẫn ngắn.

Sản phẩm bàn giao:

- Hai màn hình nghiệp vụ chính ở mức production-ready nội bộ.
- Danh sách keyboard shortcuts và hướng dẫn thao tác nhanh.
- Bộ ảnh hoặc video ngắn minh họa flow chính.

### Giai đoạn 5: Realtime và đồng bộ trạng thái (1-2 ngày)

Mục tiêu: Trạng thái item và settlement cập nhật gần realtime để giảm thao tác làm mới thủ công.

Đầu vào bắt buộc:

- `docs/realtime/realtime_item-live-updates.yaml`.
- Event docs tại `docs/events/`.

Công việc chi tiết:

1. Thiết lập websocket endpoint và handshake xác thực.
2. Phát sự kiện `item_status_changed` khi có thay đổi trạng thái item.
3. Phát sự kiện `rental_settlement_finished` khi kết toán hợp đồng hoàn tất.
4. Triển khai heartbeat, reconnect backoff và giới hạn reconnect.
5. Lọc subscription theo role và branch để tránh lộ dữ liệu chéo.
6. Thêm fallback polling nhẹ khi websocket gián đoạn kéo dài.

Tiêu chí hoàn thành giai đoạn:

- UI nhận sự kiện trong thời gian đáp ứng chấp nhận được.
- Mất kết nối ngắn hạn không làm vỡ phiên thao tác của người dùng.
- Không có sự kiện trái quyền theo role.

Sản phẩm bàn giao:

- Kênh realtime hoạt động ổn định trong môi trường dev/staging.
- Bộ test kết nối lại và kiểm tra phân quyền subscription.

### Giai đoạn 6: Báo cáo, metadata, backup (2-3 ngày)

Mục tiêu: Hoàn thiện nhóm tính năng vận hành và an toàn dữ liệu trước UAT.

Đầu vào bắt buộc:

- Blueprint cho report, metadata, backup.
- Logic tài chính từ các API POS và Rental.

Công việc chi tiết:

1. Triển khai revenue summary tách doanh thu bán, thuê, phạt.
2. Đảm bảo report dùng dữ liệu snapshot giao dịch, không dùng giá hiện tại.
3. Triển khai metadata autofill với chiến lược cache và timeout fallback.
4. Triển khai create backup job có trạng thái hàng đợi và mã checksum.
5. Bổ sung khả năng xem trạng thái backup gần nhất trên giao diện vận hành.
6. Chạy thử kịch bản restore mẫu để xác thực backup có thể sử dụng.

Tiêu chí hoàn thành giai đoạn:

- Report trả đúng số liệu trên dataset kiểm thử đã khóa.
- Metadata không làm treo luồng nhập liệu khi nguồn ngoài chậm.
- Backup tạo được file hợp lệ và có log theo dõi.

Sản phẩm bàn giao:

- Module report, metadata, backup đạt mức sẵn sàng UAT.
- Biên bản thử restore tối thiểu một lần thành công.

### Giai đoạn 7: Kiểm thử tích hợp và hardening (2-3 ngày)

Mục tiêu: Giảm rủi ro lỗi nghiệp vụ trước khi đưa vào UAT nội bộ.

Đầu vào bắt buộc:

- Toàn bộ module từ giai đoạn 1-6 đã tích hợp.
- Danh sách test cases và tiêu chí pass/fail rõ ràng.

Công việc chi tiết:

1. Chạy full contract tests cho toàn bộ API đã khai báo.
2. Chạy smoke test UI cho POS checkout và Rental return.
3. Chạy test lỗi trọng yếu: lock conflict, idempotency replay, timeout metadata.
4. Soát bảo mật theo role/scope và hành vi khi token không hợp lệ.
5. Soát audit log, backup log, và mức độ đầy đủ của telemetry cơ bản.
6. Tổ chức bug bash nội bộ để tìm lỗi UX thao tác nhanh.

Tiêu chí hoàn thành giai đoạn:

- Không còn lỗi blocker và critical mở.
- Lỗi major có kế hoạch xử lý trước ngày UAT.
- Các lỗi còn lại đã triage và có deadline rõ ràng.

Sản phẩm bàn giao:

- Báo cáo test tổng hợp.
- Danh sách bug theo mức độ và kế hoạch xử lý.
- Biên bản hardening và các quyết định chấp nhận rủi ro.

### Giai đoạn 8: UAT nội bộ và chuẩn bị release (1-2 ngày)

Mục tiêu: Xác nhận sản phẩm đáp ứng nhu cầu vận hành thực tế và sẵn sàng cho bản thử nghiệm.

Đầu vào bắt buộc:

- Build release candidate ổn định từ giai đoạn 7.
- Kịch bản UAT theo vai trò nhân viên vận hành.

Công việc chi tiết:

1. Demo luồng chuẩn và luồng lỗi cho đại diện nghiệp vụ.
2. Cho người dùng nội bộ thao tác trực tiếp theo checklist UAT.
3. Thu phản hồi định lượng và định tính về tốc độ thao tác, độ dễ dùng, độ tin cậy.
4. Chốt danh sách cải tiến bắt buộc và cải tiến nâng cao sau UAT.
5. Gắn tag release candidate, đóng gói ghi chú phát hành nội bộ.

Tiêu chí hoàn thành giai đoạn:

- UAT không còn lỗi blocker ngăn vận hành.
- Stakeholder ký xác nhận phạm vi đã đạt cho đợt chạy thử.
- Kế hoạch hậu UAT và mốc triển khai tiếp theo đã được duyệt.

Sản phẩm bàn giao:

- Biên bản UAT và danh sách action items.
- Release candidate kèm release notes.

## 4) Checklist nghiệm thu toàn dự án (chi tiết)

Checklist kiến trúc và dữ liệu:

- [ ] Database dựng mới thành công từ migration script.
- [ ] Có rollback script cho migration chính.
- [ ] Constraint dữ liệu trọng yếu hoạt động đúng.

Checklist API và nghiệp vụ:

- [ ] Tất cả API v1 có contract test và test lỗi chính.
- [ ] Idempotency hoạt động đúng trên endpoint có side effects.
- [ ] Locking ngăn được thao tác đồng thời gây xung đột.
- [ ] Audit log đủ before/after và actor cho thao tác quan trọng.

Checklist frontend và vận hành:

- [ ] Flow POS checkout chạy thông suốt bằng keyboard-first.
- [ ] Flow rental return tính phí và hoàn cọc chính xác.
- [ ] Realtime cập nhật trạng thái item/settlement ổn định.

Checklist an toàn và phát hành:

- [ ] Backup tạo được file hợp lệ và đã thử restore tối thiểu một lần.
- [ ] Không còn lỗi blocker hoặc critical trước UAT.
- [ ] Tài liệu docs đã cập nhật đồng bộ trạng thái blueprint hoặc implemented.

## 5) Tài liệu tham chiếu

- [Overview](../overview.md)
- [Registry](../_registry.yaml)
- [Runtime config](../config/config_storyhub-runtime.yaml)
- [Realtime contract](../realtime/realtime_item-live-updates.yaml)
- [Migration runbook](../migrations/migration_blueprint-to-implementation-v1.md)
