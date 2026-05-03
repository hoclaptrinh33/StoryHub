import py_compile
import os

files = [
    r'backend\app\api\v1\endpoints\inventory.py',
    r'backend\app\api\v1\endpoints\checkout.py',
    r'backend\app\api\v1\endpoints\pos.py'
]

print("--- Syntax Check ---")
for f in files:
    try:
        py_compile.compile(f, doraise=True)
        print(f"{f}: OK")
    except Exception as e:
        print(f"{f}: ERROR")
        print(e)
