# createSystemBackup (Blueprint)

> ⚠️ BLUEPRINT — Tài liệu sinh từ yêu cầu nghiệp vụ, chưa có code thực tế.

> Schema file: [bp_system-create-backup_v1.yaml](./bp_system-create-backup_v1.yaml)
> Version: 0.1.0-blueprint | Status: Blueprint | Confidence: High

## Ý tưởng gốc

System bắt buộc có backup dữ liệu để tránh mất mát khi lỗi máy, đồng thời cần audit rõ ai đã chạy backup.

## Mô tả chức năng (dự kiến)

Tạo backup job theo chế độ full hoặc incremental, có lock tránh chạy song song và trả thông tin file backup cùng checksum.

## Tham số (dự kiến)

| Tên                     | Kiểu    | Bắt buộc | Mô tả                            |
| ----------------------- | ------- | -------- | -------------------------------- |
| backup_type             | string  | Có       | full/incremental                 |
| include_media           | boolean | Không    | Có backup ảnh đính kèm hay không |
| encryption_password_ref | string  | Không    | Tham chiếu khóa mã hóa           |
| request_id              | string  | Có       | Idempotency key                  |

## Response Schema (dự kiến)

```json
{
  "backup_job_id": "BKP-20260413-001",
  "status": "queued",
  "file_path": "backups/2026-04-13/full-001.bak",
  "checksum": "sha256:...",
  "created_at": "2026-04-13T23:08:30+07:00"
}
```

## Edge Cases (dự kiến)

| Case              | Input                        | Kết quả dự kiến            |
| ----------------- | ---------------------------- | -------------------------- |
| Storage lỗi       | ổ đĩa đầy hoặc mất quyền ghi | BACKUP_STORAGE_UNAVAILABLE |
| Thiếu khóa mã hóa | encryption ref sai           | ENCRYPTION_KEY_NOT_FOUND   |
| Job đang chạy     | gửi request backup mới       | BACKUP_ALREADY_RUNNING     |
| Job treo quá lâu  | backup vượt timeout          | BACKUP_JOB_TIMEOUT         |

## Giả định (Assumptions)

- [ ] Backup chạy nền, không khóa luồng bán hàng.
- [ ] Mỗi thời điểm chỉ một backup active.
- [ ] Checksum được dùng để verify và audit.

## Câu hỏi mở (Open Questions)

- [ ] Có cần API restore riêng và flow phê duyệt không?
- [ ] Có cần đồng bộ backup sang thiết bị ngoài tự động không?

## Tiêu chí nghiệm thu (Acceptance Criteria)

- [ ] Backup job tạo đúng trạng thái và metadata trả về.
- [ ] Không có trường hợp backup chạy song song trái policy.
- [ ] Lịch sử backup có thể truy vết đầy đủ actor và kết quả.

## Gợi ý khi implement

- Tech stack gợi ý: background task queue + encrypt at rest.
- Lưu ý bảo mật dự kiến: chỉ manager/owner được trigger backup.
- Lưu ý hiệu năng dự kiến: backup incremental theo lịch để giảm I/O giờ cao điểm.
