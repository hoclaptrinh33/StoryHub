# Checklist Phase 3 - Day 4-6

## Day 4 - API Hardening

- [x] Bo sung test auth can ban (AUTH_REQUIRED, AUTH_INVALID_TOKEN).
- [x] Bo sung test idempotency replay cho Inventory reserve.
- [x] Bo sung test idempotency replay cho CRM upsert.
- [x] Bo sung test idempotency replay cho POS create order.
- [x] Bo sung test idempotency replay cho POS refund.
- [x] Bo sung test idempotency replay cho Rental create contract.
- [x] Bo sung test idempotency replay cho Rental return.
- [x] Bo sung test duplicate business-rule cho POS refund (request_id khac).
- [x] Bo sung test duplicate business-rule cho Rental return (request_id khac).

## Day 5 - Tich hop va chuan hoa

- [x] Gom checklist Day 4-6 thanh tai lieu implementation rieng.
- [x] Tich hop frontend voi toan bo ma loi nghiep vu chuan hoa tu backend.
- [x] Them UI smoke test cho 2 luong chinh: POS checkout va Rental return.
- [x] Chot mapping thong diep loi hien thi tren giao dien theo ma loi backend.

## Day 6 - Release Gate noi bo

- [x] Chay full quality gate backend: Ruff check, Ruff format, Pytest.
- [x] Chay smoke run thu cong backend + frontend bang script dev.
- [x] Chot bien ban gate truoc UAT (pass/fail, risk con lai, owner follow-up).

## Ghi chu thuc thi trong luot hien tai

- Da thuc thi xong phan Day 4 o muc backend hardening test.
- Da ket noi frontend cho luong POS checkout va Rental return voi backend endpoint that.
- Da chay smoke test thu cong tren UI cho case thanh cong va case map loi backend.
- Da chot gate report: docs/how-to/howto_phase3-day6-gate-report.md.
