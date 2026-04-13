# Migration: blueprint-to-implementation-v1

> Type: api_version
> Status: planned
> Date: 2026-04-14
> Breaking: no

## Tong quan

Migration nay chuyen bo docs tu trang thai blueprint sang implemented khi backend co source code that. Muc tieu la giu naming va contract, thay the gia dinh bang hanh vi da verify.

## Impact Analysis

### Affected Docs

| Doc                                                                                                              | Thay doi                                                                             |
| ---------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------ |
| [docs/api-reference/v1/bp_inventory-reserve-item_v1.yaml](../api-reference/v1/bp_inventory-reserve-item_v1.yaml) | Chuyen status blueprint -> implemented, thay blueprint_tracking bang source_tracking |
| [docs/api-reference/v1/bp_pos-create-order_v1.yaml](../api-reference/v1/bp_pos-create-order_v1.yaml)             | Dong bo preconditions va failure strategy theo code that                             |
| [docs/api-reference/v1/bp_rental-return-items_v1.yaml](../api-reference/v1/bp_rental-return-items_v1.yaml)       | Xac nhan rule fee va edge cases theo implementation                                  |
| [docs/ui-contracts/ui_pos-main-kiosk.yaml](../ui-contracts/ui_pos-main-kiosk.yaml)                               | Verify data binding voi API that                                                     |
| [docs/ui-contracts/ui_rental-return-inspection.yaml](../ui-contracts/ui_rental-return-inspection.yaml)           | Verify settlement states va errors                                                   |

### Affected Consumers

| Consumer            | Impact                   | Action Required                          |
| ------------------- | ------------------------ | ---------------------------------------- |
| Frontend kiosk app  | Mapping data co the doi  | Chay contract tests + frontend scenarios |
| Reporting layer     | Event payload can verify | Chay regression report tests             |
| Agent orchestration | Status docs thay doi     | Reload registry va clear cache           |

## Migration Steps

### Pre-migration

1. [ ] Dong bang schema docs va tag ban hien tai.
2. [ ] Chay full contract tests tren docs blueprint.
3. [ ] Chot danh sach API da implemented that.

### Execution

1. [ ] Chay skill mode code-first cho tung module da code xong.
2. [ ] Chuyen `status: blueprint` thanh `status: implemented`.
3. [ ] Them `source_tracking` va loai bo assumptions khong con dung.
4. [ ] Cap nhat [docs/\_registry.yaml](../_registry.yaml) theo status moi.

### Post-migration

1. [ ] Chay YAML + cross-reference validation.
2. [ ] Chay UI flow test scenarios tren kiosk.
3. [ ] Ghi changelog va thong bao cho team.

## Rollback Plan

Neu migration gay lech contract:

1. Checkout tag docs truoc migration.
2. Restore cac file API/YAML bi lech.
3. Khoi phuc `status: blueprint` va dat migration ve planned.

## Data Migration (neu co)

```sql
-- Forward migration example
-- ALTER TABLE rental_item ADD COLUMN condition_after TEXT;

-- Rollback example
-- ALTER TABLE rental_item DROP COLUMN condition_after;
```

## Timeline

| Moc                        | Ngay       | Trang thai |
| -------------------------- | ---------- | ---------- |
| Announced                  | 2026-04-14 | done       |
| Migration window open      | 2026-04-21 | planned    |
| First implemented docs set | 2026-04-28 | planned    |
| Full blueprint retirement  | 2026-05-31 | planned    |

## Related

- [docs/overview.md](../overview.md)
- [docs/\_registry.yaml](../_registry.yaml)
