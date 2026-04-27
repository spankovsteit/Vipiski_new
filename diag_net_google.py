import os
import socket
import traceback
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError

import gspread

# --- Настройки ---
CRED_PATH = Path(r"c:\Users\s.pankov\.cursor\projects\Vipiski\credentials\steit-362219-4985af158276.json")
SPREADSHEET_ID = "115N5lK0LuHldMhjEhCDHcjegiMC_L1D-38GGv9LoUc8"  # часть URL между /d/ и /edit
TIMEOUT = 20

socket.setdefaulttimeout(TIMEOUT)

def step(name):
    print(f"\n=== {name} ===", flush=True)

def show_proxy_env():
    for k in ["HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy", "NO_PROXY", "no_proxy"]:
        print(f"{k}={os.environ.get(k)}")

def test_dns(host):
    print(f"DNS resolve: {host}", flush=True)
    info = socket.getaddrinfo(host, 443)
    addrs = sorted({x[4][0] for x in info})
    print(f"Resolved: {addrs}", flush=True)

def test_https(url):
    print(f"HTTPS GET: {url}", flush=True)
    req = Request(url, method="GET")
    try:
        with urlopen(req, timeout=TIMEOUT) as r:
            print(f"Reachable, HTTP {r.status}", flush=True)
            return True
    except HTTPError as e:
        # 400/401/403/404 часто нормальны для тестового GET.
        print(f"Reachable, HTTP {e.code} ({e.reason})", flush=True)
        return True
    except URLError as e:
        print(f"UNREACHABLE: {e}", flush=True)
        return False

def main():
    try:
        step("0) Proxy env")
        show_proxy_env()

        step("1) Credentials file")
        print("Exists:", CRED_PATH.is_file(), CRED_PATH, flush=True)
        if not CRED_PATH.is_file():
            raise RuntimeError("Credentials file not found")

        step("2) DNS")
        test_dns("oauth2.googleapis.com")
        test_dns("www.googleapis.com")
        test_dns("sheets.googleapis.com")

        step("3) HTTPS to Google endpoints")
        ok1 = test_https("https://oauth2.googleapis.com/token")
        ok2 = test_https("https://www.googleapis.com/discovery/v1/apis/sheets/v4/rest")
        ok3 = test_https("https://sheets.googleapis.com/$discovery/rest?version=v4")
        print(f"HTTPS summary: {ok1=}, {ok2=}, {ok3=}", flush=True)

        step("4) gspread auth")
        gc = gspread.service_account(filename=str(CRED_PATH))
        print("Auth object created", flush=True)

        step("5) open_by_key")
        sh = gc.open_by_key(SPREADSHEET_ID)
        print("Spreadsheet title:", sh.title, flush=True)

        step("6) worksheets")
        print([ws.title for ws in sh.worksheets()], flush=True)

        print("\nSUCCESS: all checks passed", flush=True)

    except Exception as e:
        print("\nFAILED:", repr(e), flush=True)
        traceback.print_exc()

if __name__ == "__main__":
    main()