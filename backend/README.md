# StoryHub Backend

FastAPI service cho StoryHub theo huong local-first.

## Chay nhanh

```bash
python -m venv .venv
.venv\\Scripts\\activate
pip install -e .[dev]
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Health endpoint:

- GET /api/v1/health

## Khoi tao database

Chay migration de tao schema:

```bash
python scripts/migrate.py up
```

Kiem tra trang thai migration:

```bash
python scripts/migrate.py status
```

Seed du lieu mau (idempotent):

```bash
python scripts/seed.py
```

Rollback migration ve trang thai chua tao schema:

```bash
python scripts/migrate.py down
```

## Kiem tra chat luong

```bash
ruff check .
ruff format --check .
pytest
```
