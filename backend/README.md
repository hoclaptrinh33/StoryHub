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
