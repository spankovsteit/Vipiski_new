from pathlib import Path
import json
import traceback
import gspread

cred_path = Path(r"c:\Users\s.pankov\.cursor\projects\Vipiski\credentials\steit-362219-4985af158276.json")
spreadsheet_name = "План_платежей (день)"  # при необходимости замените

print("== Step 1: file exists ==")
print("credentials path:", cred_path)
print("exists:", cred_path.is_file())
if not cred_path.is_file():
    raise SystemExit("ERROR: credentials file not found")

print("\n== Step 2: read json ==")
raw = json.loads(cred_path.read_text(encoding="utf-8"))
client_email = raw.get("client_email")
project_id = raw.get("project_id")
print("project_id:", project_id)
print("client_email:", client_email)
if not client_email:
    raise SystemExit("ERROR: no client_email in credentials json")

print("\n== Step 3: gspread auth ==")
try:
    gc = gspread.service_account(filename=str(cred_path))
    print("OK: authorized")
except Exception as e:
    print("AUTH ERROR:", repr(e))
    traceback.print_exc()
    raise SystemExit(2)

print("\n== Step 4: open spreadsheet by name ==")
try:
    sh = gc.open(spreadsheet_name)
    print("OK: opened spreadsheet")
    print("title:", sh.title)
    print("id:", sh.id)
except Exception as e:
    print("OPEN ERROR:", repr(e))
    traceback.print_exc()
    print("\nHint: share the sheet with this service account email:")
    print(client_email)
    raise SystemExit(3)

print("\n== Step 5: list worksheets ==")
try:
    ws_titles = [ws.title for ws in sh.worksheets()]
    print("worksheets:", ws_titles)
except Exception as e:
    print("WORKSHEETS ERROR:", repr(e))
    traceback.print_exc()
    raise SystemExit(4)

print("\nSUCCESS: Google connection is working.")