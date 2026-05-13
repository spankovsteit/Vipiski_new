import gspread

# Путь к вашему JSON файлу
JSON_PATH = r'D:\Выписки\steit-362219-f7abe8bc3429.json'
# Имя вашей таблицы
SHEET_NAME = "План_платежей (день)"  # <-- ЗАМЕНИТЕ на реальное имя!

print("1. Авторизуемся с правильными scope'ами...")
try:
    gc = gspread.service_account(
        filename=JSON_PATH,
        scopes=['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    )
    print("   ✅ Авторизация успешна")
except Exception as e:
    print(f"   ❌ Ошибка авторизации: {e}")
    exit()

print("2. Пробуем открыть таблицу...")
try:
    sh = gc.open(SHEET_NAME)
    print(f"   ✅ Таблица открыта: {sh.title}")
    
    # Дополнительно: показать первый лист
    worksheet = sh.sheet1
    print(f"   📊 Первый лист: {worksheet.title}")
    
except Exception as e:
    print(f"   ❌ Ошибка открытия: {e}")
    print("\nВозможные причины:")
    print("  - Неправильное имя таблицы")
    print("  - Таблицей не поделились с сервисным аккаунтом")
    print(f"  - Email сервисного аккаунта: посмотрите в JSON файле поле 'client_email'")