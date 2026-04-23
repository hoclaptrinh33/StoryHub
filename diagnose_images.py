"""Diagnostic script: check every layer of image loading pipeline."""
import sqlite3, os, sys

DB_PATH = os.path.join(os.path.dirname(__file__), "storyhub.db")
STORAGE_COVERS = os.path.join(os.path.dirname(__file__), "storage", "covers")

print("=" * 60)
print("LAYER 1: DATABASE")
print("=" * 60)
try:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT id, name, cover_url FROM title WHERE deleted_at IS NULL")
    rows = cur.fetchall()
    print(f"  Total active titles: {len(rows)}")
    for r in rows:
        status = "NULL" if r["cover_url"] is None else ("EMPTY" if r["cover_url"] == "" else r["cover_url"])
        print(f"  ID={r['id']}  name={r['name']!r:30s}  cover_url={status}")
    conn.close()
except Exception as e:
    print(f"  ERROR reading DB: {e}")

print()
print("=" * 60)
print("LAYER 2: FILE SYSTEM (storage/covers/)")
print("=" * 60)
if os.path.isdir(STORAGE_COVERS):
    files = os.listdir(STORAGE_COVERS)
    print(f"  Files found: {len(files)}")
    for f in files:
        full = os.path.join(STORAGE_COVERS, f)
        sz = os.path.getsize(full)
        print(f"    {f}  ({sz} bytes)")
else:
    print("  WARNING: storage/covers/ directory does NOT exist!")

print()
print("=" * 60)
print("LAYER 3: CROSS-CHECK (DB cover_url vs files on disk)")
print("=" * 60)
try:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT id, name, cover_url FROM title WHERE deleted_at IS NULL")
    rows = cur.fetchall()
    for r in rows:
        url = r["cover_url"]
        if not url:
            print(f"  ID={r['id']} ({r['name']}): NO cover_url in DB -> image will be placeholder")
            continue
        if url.startswith("http"):
            print(f"  ID={r['id']} ({r['name']}): EXTERNAL URL (not downloaded!) -> {url[:80]}")
            print(f"    PROBLEM: External URLs will fail due to Tauri CSP or 429 rate limits!")
        elif url.startswith("/storage/covers/"):
            fname = url.replace("/storage/covers/", "")
            disk_path = os.path.join(STORAGE_COVERS, fname)
            exists = os.path.isfile(disk_path)
            print(f"  ID={r['id']} ({r['name']}): LOCAL path={url} -> file exists: {exists}")
            if not exists:
                print(f"    PROBLEM: File NOT found on disk!")
        else:
            print(f"  ID={r['id']} ({r['name']}): UNKNOWN format: {url}")
    conn.close()
except Exception as e:
    print(f"  ERROR: {e}")

print()
print("=" * 60)
print("LAYER 4: BACKEND STATIC FILES MOUNT")
print("=" * 60)
print(f"  main.py mounts /storage -> parent of covers dir")
print(f"  Expected: GET http://127.0.0.1:8000/storage/covers/XXXXX.jpg")
storage_root = os.path.join(os.path.dirname(__file__), "storage")
print(f"  storage root exists: {os.path.isdir(storage_root)}")

print()
print("=" * 60)
print("LAYER 5: TAURI CSP")
print("=" * 60)
tauri_conf = os.path.join(os.path.dirname(__file__), "frontend", "src-tauri", "tauri.conf.json")
if os.path.isfile(tauri_conf):
    import json
    with open(tauri_conf, "r", encoding="utf-8") as f:
        conf = json.load(f)
    csp = conf.get("app", {}).get("security", {}).get("csp", "NOT SET")
    print(f"  CSP: {csp}")
    if csp and "127.0.0.1:8000" in str(csp):
        print("  OK: CSP allows 127.0.0.1:8000")
    else:
        print("  WARNING: CSP may block images from backend!")
else:
    print("  tauri.conf.json not found")

print()
print("DONE.")
