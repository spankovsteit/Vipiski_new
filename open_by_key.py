from pathlib import Path
import gspread
import socket

socket.setdefaulttimeout(20)  # чтобы не висело бесконечно

cred_path = Path(r"c:\Users\s.pankov\.cursor\projects\Vipiski\credentials\steit-362219-4985af158276.json")
SPREADSHEET_ID = "115N5lK0LuHldMhjEhCDHcjegiMC_L1D-38GGv9LoUc8"

gc = gspread.service_account(filename=str(cred_path))

print("open_by_key...")
sh = gc.open_by_key(SPREADSHEET_ID)
print("OK:", sh.title)
print([ws.title for ws in sh.worksheets()])