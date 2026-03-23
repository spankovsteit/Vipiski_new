"""
DEPRECATED: use `main.py` and the `vipiski` package (Google Raw_balances + no Excel).
This file is kept for reference only.
"""

import imaplib
import email
import datetime
from datetime import datetime
from datetime import timedelta
import os
import shutil
import glob2
from PyPDF2 import PdfFileReader
import regex
import openpyxl
from openpyxl import load_workbook
import locale
import telebot
import requests
from oauth2client.service_account import ServiceAccountCredentials
import gspread
import json
import time
import glob
import pyodbc
import pandas as pd
from dash import Dash, dash_table
import xlwings as xw
import sys

# server = "imap.gmail.com"
# port = "993"
# login = "stvipiska@gmail.com"
# password = "BJw-4fH-U59-p3S"   #"b7X-8AY-zLS-xbd" #"Zks-whs-Ang-4xB"

time.sleep(3)

# Установка локали для русского языка
locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')

SERVER = 'Steit-pb'
DATABASE = 'steitNew'
USERNAME = 'sp'
PASSWORD = 's3'

connectionString = f'DRIVER={{SQL Server Native Client 11.0}};SERVER={SERVER};DATABASE={DATABASE};UID={USERNAME};PWD={PASSWORD}'

connection = pyodbc.connect(connectionString, autocommit=True)
dbCursor = connection.cursor()

# requestString = """ INSERT INTO BankStatement(organisation,summ,date_of_issuance) VALUES ('Клевер','500','20230926'),('Радуга','1000','20230926')"""
# dbCursor.execute(requestString)
# connection.commit()
# Определение текущего месяца и года
current_month = datetime.now().strftime("%B")
current_year = datetime.now().strftime("%Y")

original_stdout = sys.stdout
log_file = open(r'D:\Выписки\vipiski_log.txt', 'w', encoding='utf-8')
sys.stdout = log_file

# Формирование пути к папке
base_path = "D:\\Выписки\\"
folder_path = os.path.join(base_path, current_year, current_month)

# Создание папки, если она не существует
os.makedirs(folder_path, exist_ok=True)

os.chdir(folder_path)
print("Текущая директория:", os.getcwd())

yesterday = datetime.today() - timedelta(days=1)

day1 = datetime.now().strftime("%d-%m-%Y").replace('-', '')
putdir = os.path.join(folder_path, day1)

daysbr = yesterday.strftime("%d")
monthname = yesterday.strftime('%b')
monthsbr = monthname[0]
print(day1,monthname,daysbr,monthsbr)

# Создание папки для текущей даты, если она не существует
os.makedirs(putdir, exist_ok=True)
print("Путь для сохранения файлов:", putdir)

# Копирование PDF файлов, созданных сегодня, из папки "Текущие"
src_dir = os.path.join(base_path, "Текущие")

for root, dirs, files in os.walk(src_dir):
    for file in files:
        if file.endswith('.pdf'):
            timestamp = os.path.getctime(os.path.join(root, file))
            datestamp = datetime.fromtimestamp(timestamp).strftime("%d%m%Y")
            today = datetime.now().strftime('%d%m%Y')
            if datestamp == today:
                shutil.copyfile(os.path.join(root, file), os.path.join(putdir, file))

# Удаление файлов и папок в папке "Текущие"
for root, dirs, files in os.walk(src_dir):
    for file in files:
        os.unlink(os.path.join(root, file))
    for dir in dirs:
        shutil.rmtree(os.path.join(root, dir))

# Определяем исходящий остаток

path_to_dir = putdir

content = os.listdir(path_to_dir)
print(len(content))

pdf_files = glob2.glob(path_to_dir + '\*.pdf')

# Чтение эксельки для загрузки остатков

token = '5617912411:AAFaAFs0NcEOZR5iJwsEOO7iVrRPFFKzFh8'
bot = telebot.TeleBot(token)
chat_id = '-1003124598066'
#chat_id = '1824722729'

reestr_dir = r'\\192.168.1.9\fin\Arenda\_БОРИС'
reestr_copy = r'\\192.168.1.9\fin\Arenda\Reestr_reserv'
os.chdir(reestr_dir)
print(os.getcwd())
# filename = 'Reestr.xlsm'
# if os.path.exists(filename) and os.path.isfile(filename):
#     pass  # Файл существует и является обычным файлом
# else:
input_file = os.path.join(reestr_dir,'Reestr.xlsm')
output_file = os.path.join(reestr_copy, "Reestr"+day1+".xlsm")
try:
    os.rename("Reestr.xlsm","Reestr1.xlsm")
    os.rename("Reestr1.xlsm", "Reestr.xlsm")
    shutil.copyfile(input_file, output_file)
except OSError:
     print('Файл либо не существует, либо кем-то занят!')
     bot.send_message(chat_id, 'Файл Reestr.xlsm занят! Обновление остатков невозможно!')
     quit()

# Функция для замены точки на запятую
def format_ostatok(value):
    return str(value).replace('.', ',')

# Словарь с нужными координатами ячеек и их наименованиями
cells = {
    "ostatok_akvitania": 'L25',
    "ostatok_akvitania_sber": 'L70',
    "ostatok_bergen": 'L27',
    "ostatok_bergen_sber": 'L64',
    "ostatok_immobi": 'L30',
    "ostatok_immobi_sber": 'L71',
    "ostatok_proektnie_reshenia": 'L39',
    "ostatok_proektnie_reshenia_sber": 'L52',
    "ostatok_riteil_park": 'L40',
    "ostatok_riteil_park_sber": 'L73',
    "ostatok_dudergof": 'L28',
    "ostatok_dudergof_sber": 'L61',
    "ostatok_kudrovo_i": 'L32',
    "ostatok_kudrovo_invest_sber": 'L72',
    "ostatok_manevich": 'L7',
    "ostatok_manevich_sber":'L58',
    "ostatok_metro": 'L34',
    "ostatok_metro_sber": 'L65',
    "ostatok_m_invest": 'L35',
    "ostatok_partner": 'L8',
    "partner_vtb": 'L9',
    "partner_sber": 'L59',
    "ostatok_parfenenko": 'L10',
    "ostatok_parfenenko_vtb": 'L11',
    "ostatok_praga": 'L38',
    "ostatok_sityinvest": 'L42',
    "ostatok_sityinvest_sber": 'L60',
    "ostatok_sityinvest_vtb": 'L69',
    "ostatok_ser": 'L45',
    "ostatok_ser_sber": 'L63',
    "ostatok_formula": 'L23',
    "ostatok_formula_vtb": 'L24',
    "ostatok_formula_sber": 'L55',
    "ostatok_frank": 'L47',
    "ostatok_sp_impost": 'L37',
    "ostatok_sp_impost_sber": 'L68',
    "ostatok_ohtinskaya_alleya": 'L12',
    "ostatok_ohtinskaya_alleya_vtb": 'L13',
    "ostatok_ohtinskaya_alleya_sber": 'L54',
    "ostatok_gastropark":'L14',
    "ostatok_H1": 'L56',
    "ostatok_H1_sber": 'L57',
    "ostatok_raduga": 'L15',
    "ostatok_raduga_vtb": 'L16',
    "ostatok_kudrovo_s": 'L33',
    "ostatok_murino_g": 'L36',
    "ostatok_steit": 'L43',
    "steit_ukb": 'L44',
    "ostatok_ankon": 'L26',
    "ostatok_tsn_oazis":'L48',
    "klever_375": 'AF3',
    "klever_852": 'AF4',
    "klever_sbr": 'L6',
    "ostatok_klever_vtb": 'L5',
    "reaktiv": 'L17',
    "ostatok_reaktiv_sbr":'L18',
    "romashki": 'L19',
    "romashki_ukb": 'L20',
    "ostatok_romashki_sber":'L62',
    "ostatok_smart_vtb": 'L21',
    "smart_sbr": 'L22',
    "tsn_vtb": 'L49',
    "tsn_r2_tochka": 'L53',
    "ostatok_sev_zvezda":'L41',
    "ostatok_sev_zvezda_sber":'L66',
    "ostatok_media47":'L50',
    "ostatok_praga_vtb":'L51',
    "ostatok_praga_sber":'L67'
}

# Загрузка книги и листа
reestr = xw.Book(r'\\192.168.1.9\fin\Arenda\_БОРИС\Reestr.xlsm')
sheet = reestr.sheets['Банки']

# Считывание и форматирование данных
ostatki = {name: format_ostatok(sheet[cell].value) for name, cell in cells.items()}

# Теперь вы можете использовать эти данные по имени, например:
ostatok_gastropark = ostatki['ostatok_gastropark'] #if ostatki['ostatok_gastropark'] is None else 0
ostatok_H1 = ostatki['ostatok_H1']
ostatok_H1_sber = ostatki['ostatok_H1_sber']
ostatok_tsn_oazis = ostatki['ostatok_tsn_oazis'] #if ostatki['ostatok_tsn_oazis'] is None else 0
ostatok_akvitania = ostatki['ostatok_akvitania'] #if ostatki['ostatok_akvitania'] is None else 0
ostatok_akvitania_sber = ostatki['ostatok_akvitania_sber'] #if ostatki['ostatok_akvitania'] is None else 0
ostatok_bergen = ostatki['ostatok_bergen'] #if ostatki['ostatok_bergen'] is None else 0
ostatok_bergen_sber = ostatki['ostatok_bergen_sber']
ostatok_immobi = ostatki['ostatok_immobi'] #if ostatki['ostatok_immobi'] is None else 0
ostatok_immobi_sber = ostatki['ostatok_immobi_sber']
ostatok_proektnie_reshenia = ostatki['ostatok_proektnie_reshenia'] #if ostatki['ostatok_proektnie_reshenia'] is None else 0
ostatok_proektnie_reshenia_sber = ostatki['ostatok_proektnie_reshenia_sber'] #if ostatki['ostatok_proektnie_reshenia'] is None else 0
ostatok_riteil_park = ostatki['ostatok_riteil_park'] #if ostatki['ostatok_riteil_park'] is None else 0
ostatok_riteil_park_sber = ostatki['ostatok_riteil_park_sber']
ostatok_dudergof = ostatki['ostatok_dudergof'] #if ostatki['ostatok_dudergof'] is None else 0
ostatok_dudergof_sber = ostatki['ostatok_dudergof_sber']
ostatok_kudrovo_i = ostatki['ostatok_kudrovo_i'] #if ostatki['ostatok_kudrovo_i'] is None else 0
ostatok_kudrovo_invest_sber = ostatki['ostatok_kudrovo_invest_sber']
ostatok_manevich = ostatki['ostatok_manevich'] #if ostatki['ostatok_manevich'] is None else 0
ostatok_manevich_sber = ostatki['ostatok_manevich_sber']
ostatok_metro = ostatki['ostatok_metro'] #if ostatki['ostatok_metro'] is None else 0
ostatok_metro_sber = ostatki['ostatok_metro_sber']
ostatok_m_invest = ostatki['ostatok_m_invest'] #if ostatki['ostatok_m_invest'] is None else 0
ostatok_partner = ostatki['ostatok_partner'] #if ostatki['ostatok_partner'] is None else 0
ostatok_partner_vtb = ostatki['partner_vtb'] #if ostatki['partner_vtb'] is None else 0
ostatok_partner_sber = ostatki['partner_sber']
ostatok_parfenenko = ostatki['ostatok_parfenenko'] #if ostatki['ostatok_parfenenko'] is None else 0
ostatok_parfenenko_vtb = ostatki['ostatok_parfenenko_vtb'] #if ostatki['ostatok_parfenenko_vtb'] is None else 0
ostatok_praga = ostatki['ostatok_praga'] #if ostatki['ostatok_praga'] is None else 0
ostatok_sev_zvezda = ostatki['ostatok_sev_zvezda'] #if ostatki['ostatok_sev_zvezda'] is None else 0
ostatok_sev_zvezda_sber = ostatki['ostatok_sev_zvezda_sber']
ostatok_sityinvest = ostatki['ostatok_sityinvest'] #if ostatki['ostatok_sityinvest'] is None else 0
ostatok_sityinvest_sber = ostatki['ostatok_sityinvest_sber'] #if ostatki['ostatok_sityinvest'] is None else 0
ostatok_sityinvest_vtb = ostatki['ostatok_sityinvest_vtb']
ostatok_ser = ostatki['ostatok_ser'] #if ostatki['ostatok_ser'] is None else 0
ostatok_ser_sber = ostatki['ostatok_ser_sber']
ostatok_formula = ostatki['ostatok_formula'] #if ostatki['ostatok_formula'] is None else 0
ostatok_formula_vtb = ostatki['ostatok_formula_vtb'] #if ostatki['ostatok_formula_vtb'] is None else 0
ostatok_formula_sber = ostatki['ostatok_formula_sber']
ostatok_frank = ostatki['ostatok_frank'] #if ostatki['ostatok_frank'] is None else 0
ostatok_sp_impost = ostatki['ostatok_sp_impost'] #if ostatki['ostatok_sp_impost'] is None else 0
ostatok_sp_impost_sber = ostatki['ostatok_sp_impost_sber']
ostatok_ohtinskaya_alleya = ostatki['ostatok_ohtinskaya_alleya'] #if ostatki['ostatok_ohtinskaya_alleya'] is None else 0
ostatok_ohtinskaya_alleya_vtb = ostatki['ostatok_ohtinskaya_alleya_vtb'] #if ostatki['ostatok_ohtinskaya_alleya_vtb'] is None else 0
ostatok_ohtinskaya_alleya_sber = ostatki['ostatok_ohtinskaya_alleya_sber']
ostatok_raduga = ostatki['ostatok_raduga'] #if ostatki['ostatok_raduga'] is None else 0
ostatok_raduga_vtb = ostatki['ostatok_raduga_vtb']
ostatok_kudrovo_s = ostatki['ostatok_kudrovo_s'] #if ostatki['ostatok_kudrovo_s'] is None else 0
ostatok_murino_g = ostatki['ostatok_murino_g'] #if ostatki['ostatok_murino_g'] is None else 0
ostatok_steit = ostatki['ostatok_steit'] #if ostatki['ostatok_steit'] is None else 0
steit_ukb = ostatki['steit_ukb'] #if ostatki['steit_ukb'] is None else 0
ostatok_ankon = ostatki['ostatok_ankon'] #if ostatki['ostatok_ankon'] is None else 0
ostatok_tsn_oazis = ostatki['ostatok_tsn_oazis'] #if ostatki['ostatok_tsn_oazis'] is None else 0
klever_375 = ostatki['klever_375'] #if ostatki['klever_375'] is None else float(0)
klever_852 = ostatki['klever_852'] #if ostatki['klever_852'] is None else float(0)
klever_sbr = ostatki['klever_sbr'] #if ostatki['klever_sbr'] is None else 0
ostatok_klever_vtb = ostatki['ostatok_klever_vtb'] #if ostatki['klever_kard'] is None else 0
reaktiv = ostatki['reaktiv'] #if ostatki['reaktiv'] is None else 0
ostatok_reaktiv_sbr = ostatki['ostatok_reaktiv_sbr'] #if ostatki['ostatok_reaktiv_sbr'] is None else 0
romashki = ostatki['romashki'] #if ostatki['romashki'] is None else 0
ostatok_romashki_sber = ostatki['ostatok_romashki_sber'] #if ostatki['romashki'] is None else 0
romashki_ukb = ostatki['romashki_ukb'] #if ostatki['romashki_ukb'] is None else 0
ostatok_smart_vtb = ostatki['ostatok_smart_vtb'] #if ostatki['smart'] is None else 0
smart_sbr = ostatki['smart_sbr'] #if ostatki['smart_sbr'] is None else 0
ostatok_tsn_vtb = ostatki['tsn_vtb'] #if ostatki['tsn_vtb'] is None else 0
ostatok_tsn_r2_tochka = ostatki['tsn_r2_tochka']
ostatok_media47 = ostatki['ostatok_media47'] #if ostatki['ostatok_media47'] is None else 0
ostatok_praga_vtb = ostatki['ostatok_praga_vtb']
ostatok_praga_sber = ostatki['ostatok_praga_sber']


# Чтение PDF и загрузка в эксель
for num_of_files in range(len(pdf_files)):
    pdf_document = pdf_files[num_of_files]
    with open(pdf_document, "rb") as filehandle:
        pdf = PdfFileReader(filehandle)
        pages = pdf.getNumPages()
        text_all = []
        for i in range(pages):
            page = pdf.getPage(i)
            text_all.append(page.extractText())
            text = ''.join(str(x) for x in text_all)

        # ЮКБ

        if 'holder: ООО"Аквитания"' in text:
            ostatok_akvitania = regex.search(r'(Исходящий .+?)$', text).group(1).replace('.', '').split(' /')[1]
            print('ООО АКВИТАНИЯ' + ';' + ostatok_akvitania)
            sheet['L25'].value = float(ostatok_akvitania.replace(',', '.'))

        elif 'holder: ООО"БЕРГЕН"' in text:
            ostatok_bergen = regex.search(r'(Исходящий .+?)$', text).group(1).replace('.', '').split(' /')[1]
            print('ООО БЕРГЕН' + ';' + ostatok_bergen)
            sheet['L27'].value = float(ostatok_bergen.replace(',', '.'))

        elif 'holder: ООО"ИММОБИ"' in text:
            ostatok_immobi = regex.search(r'(Исходящий .+?)$', text).group(1).replace('.', '').split(' /')[1]
            print('ООО "ИММОБИ"' + ';' + ostatok_immobi)
            sheet['L30'].value = float(ostatok_immobi.replace(',', '.'))

        elif 'holder: ООО"Проектные Решения"' in text:
            ostatok_proektnie_reshenia = regex.search(r'(Исходящий .+?)$', text).group(1).replace('.', '').split(' /')[
                1]
            print('ООО "Проектные Решения"' + ';' + ostatok_proektnie_reshenia)
            sheet['L39'].value = float(ostatok_proektnie_reshenia.replace(',', '.'))

        elif 'holder: ООО"Ритейл Парк"' in text:
            ostatok_riteil_park = regex.search(r'(Исходящий .+?)$', text).group(1).replace('.', '').split(' /')[1]
            print('ООО "Ритейл Парк"' + ';' + ostatok_riteil_park)
            sheet['L40'].value = float(ostatok_riteil_park.replace(',', '.'))

        elif 'holder: ООО"Дудергоф"' in text:
            ostatok_dudergof = regex.search(r'(Исходящий .+?)$', text).group(1).replace('.', '').split(' /')[1]
            print('ООО "Дудергоф"' + ';' + ostatok_dudergof)
            sheet['L28'].value = float(ostatok_dudergof.replace(',', '.'))

        elif 'holder: ООО"Кудрово-Инвест"' in text:
            ostatok_kudrovo_i = regex.search(r'(Исходящий .+?)$', text).group(1).replace('.', '').split(' /')[1]
            print('ООО "Кудрово-Инвест"' + ';' + ostatok_kudrovo_i)
            sheet['L32'].value = float(ostatok_kudrovo_i.replace(',', '.'))

        elif 'holder: ИПМАНЕВИЧ АЛЛАЕФИМОВНА' in text:
            ostatok_manevich = regex.search(r'(Исходящий .+?)$', text).group(1).replace('.', '').split(' /')[1]
            print('ИП МАНЕВИЧ А. Е.' + ';' + ostatok_manevich)
            sheet['L7'].value = float(ostatok_manevich.replace(',', '.'))

        elif 'holder: ООО"Метро"' in text:
            ostatok_metro = regex.search(r'(Исходящий .+?)$', text).group(1).replace('.', '').split(' /')[1]
            print('ООО "МЕТРО"' + ';' + ostatok_metro)
            sheet['L34'].value = float(ostatok_metro.replace(',', '.'))

        elif 'holder: ООО"М-Инвест"' in text:
            ostatok_m_invest = regex.search(r'(Исходящий .+?)$', text).group(1).replace('.', '').split(' /')[1]
            print('ООО "М-Инвест"' + ';' + ostatok_m_invest)
            sheet['L35'].value = float(ostatok_m_invest.replace(',', '.'))

        elif 'holder: ООО"Партнер"' in text:
            ostatok_partner = regex.search(r'(Исходящий .+?)$', text).group(1).replace('.', '').split(' /')[1]
            print('ООО "Партнер"' + ';' + ostatok_partner)
            sheet['L8'].value = float(ostatok_partner.replace(',', '.'))

        elif 'holder: ИППарфененко Мария Александровна' in text:
            ostatok_parfenenko = regex.search(r'(Исходящий .+?)$', text).group(1).replace('.', '').split(' /')[1]
            print('ИП Парфененко М. А.' + ';' + ostatok_parfenenko)
            sheet['L10'].value = float(ostatok_parfenenko.replace(',', '.'))

        elif 'holder: ООО"Прага"' in text:
            ostatok_praga = regex.search(r'(Исходящий .+?)$', text).group(1).replace('.', '').split(' /')[1]
            print('ООО "Прага"' + ';' + ostatok_praga)
            sheet['L38'].value = float(ostatok_praga.replace(',', '.'))

        elif 'holder: ООО"Северная звезда"' in text:
            ostatok_sev_zvezda = regex.search(r'(Исходящий .+?)$', text).group(1).replace('.', '').split(' /')[1]
            print('ООО "Северная звезда"' + ';' + ostatok_sev_zvezda)
            sheet['L41'].value = float(ostatok_sev_zvezda.replace(',', '.'))

        elif 'holder: ООО"СитиИнвест"' in text:
            ostatok_sityinvest = regex.search(r'(Исходящий .+?)$', text).group(1).replace('.', '').split(' /')[1]
            print('ООО "СитиИнвест"' + ';' + ostatok_sityinvest)
            sheet['L42'].value = float(ostatok_sityinvest.replace(',', '.'))

        elif 'holder: ООО"СтройЭкспертРитейл"' in text:
            ostatok_ser = regex.search(r'(Исходящий .+?)$', text).group(1).replace('.', '').split(' /')[1]
            print('ООО "СЭР"' + ';' + ostatok_ser)
            sheet['L45'].value = float(ostatok_ser.replace(',', '.'))

        elif 'holder: ООО"Формула"' in text:
            ostatok_formula = regex.search(r'(Исходящий .+?)$', text).group(1).replace('.', '').split(' /')[1]
            print('ООО "Формула"' + ';' + ostatok_formula)
            sheet['L23'].value = float(ostatok_formula.replace(',', '.'))

        elif 'holder: ООО"Франк"' in text:
            ostatok_frank = regex.search(r'(Исходящий .+?)$', text).group(1).replace('.', '').split(' /')[1]
            print('ООО "Франк"' + ';' + ostatok_frank)
            sheet['L47'].value = float(ostatok_frank.replace(',', '.'))

        elif 'holder: ООО"СП-Импост"' in text:
            ostatok_sp_impost = regex.search(r'(Исходящий .+?)$', text).group(1).replace('.', '').split(' /')[1]
            print('ООО "СП-Импост"' + ';' + ostatok_sp_impost)
            sheet['L37'].value = float(ostatok_sp_impost.replace(',', '.'))

        elif 'holder: ООО"Охтинская аллея"' in text:
            ostatok_ohtinskaya_alleya = regex.search(r'(Исходящий .+?)$', text).group(1).replace('.', '').split(' /')[1]
            print('ООО "Охтинская аллея"' + '; ' + ostatok_ohtinskaya_alleya)
            sheet['L12'].value = float(ostatok_ohtinskaya_alleya.replace(',', '.'))

        elif 'holder: ООО"Ромашки"' in text:
            ostatok_romashki_ukb = regex.search(r'(Исходящий .+?)$', text).group(1).replace('.', '').split(' /')[1]
            romashki_ukb = ostatok_romashki_ukb
            print('ООО "Ромашки ЮКБ"' + '; ' + ostatok_romashki_ukb)
            sheet['L20'].value = float(ostatok_romashki_ukb.replace(',', '.'))

        elif 'holder: ООО"СТЕЙТ"' in text:
            ostatok_steit_ukb = regex.search(r'(Исходящий .+?)$', text).group(1).replace('.', '').split(' /')[1]
            steit_ukb = ostatok_steit_ukb
            print('ООО "СТЕЙТ ЮКБ"' + '; ' + steit_ukb)
            sheet['L44'].value = float(steit_ukb.replace(',', '.'))

        # Сбер

        elif 'ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ "РАДУГА"' in text and 'СберБизнес' in text:  # ООО "Радуга"
            ostatok_raduga = \
                regex.search(r'(Исходящий .+?)\n', text).group(1).replace(' ', '').split('0,00')[1].split(daysbr+monthsbr)[0]
            print('ООО "Радуга"' + '; ' + ostatok_raduga)
            sheet['L15'].value = float(ostatok_raduga.replace(',', '.'))

        elif 'ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ "КУДРОВО-СТРОЙ"' in text and 'СберБизнес' in text:
            ostatok_kudrovo_s = \
                regex.search(r'(Исходящий .+?)\n', text).group(1).replace(' ', '').split('0,00')[1].split(daysbr+monthsbr)[0]
            print('ООО "КУДРОВО-СТРОЙ"' + '; ' + ostatok_kudrovo_s)
            sheet['L33'].value = float(ostatok_kudrovo_s.replace(',', '.'))

        elif 'ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ "МУРИНО-ГРАД"' in text and 'СберБизнес' in text:
            ostatok_murino_g = \
                regex.search(r'(Исходящий .+?)\n', text).group(1).replace(' ', '').split('0,00')[1].split(daysbr+monthsbr)[0]
            print('ООО "Мурино-Град"' + '; ' + ostatok_murino_g)
            sheet['L36'].value = float(ostatok_murino_g.replace(',', '.'))

        elif 'ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ "СТЕЙТ"' in text and 'СберБизнес' in text:
            ostatok_steit = \
                regex.search(r'(Исходящий .+?)\n', text).group(1).replace(' ', '').split('0,00')[1].split(daysbr+monthsbr)[0]
            print('ООО "СТЕЙТ"' + '; ' + ostatok_steit)
            sheet['L43'].value = float(ostatok_steit.replace(',', '.'))

        elif 'ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ "КЛЕВЕР"' in text and 'СберБизнес' in text:
            klever_sbr = \
                regex.search(r'(Исходящий .+?)\n', text).group(1).replace(' ', '').split('0,00')[1].split(daysbr+monthsbr)[0]
            print('ООО "КЛЕВЕР" СБЕР' + '; ' + klever_sbr)

            sheet['L6'].value = float(klever_sbr.replace(',', '.'))

        elif 'ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ "СМАРТ СОЛЮШН"' in text and 'СберБизнес' in text:
            ostatok_smart_sbr = \
                regex.search(r'(Исходящий .+?)\n', text).group(1).replace(' ', '').split('0,00')[1].split(daysbr+monthsbr)[0]
            print('ООО "СМАРТ СОЛЮШН" СБЕР' + '; ' + ostatok_smart_sbr)
            smart_sbr = ostatok_smart_sbr
            sheet['L22'].value = float(smart_sbr.replace(',', '.'))

        elif 'ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ "РЕАКТИВ"' in text and 'СберБизнес' in text:
            ostatok_reaktiv_sbr = \
                regex.search(r'(Исходящий .+?)\n', text).group(1).replace(' ', '').split('0,00')[1].split(daysbr+monthsbr)[0]
            print('ООО "РЕАКТИВ" СБЕР' + '; ' + ostatok_reaktiv_sbr)
            sheet['L18'].value = float(ostatok_reaktiv_sbr.replace(',', '.'))

        elif 'ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ "МЕДИА 47"' in text and 'СберБизнес' in text:
            ostatok_media47 = \
                regex.search(r'Исходящий остаток 0,00 ([\d\s]+,\d{2})', text).group(1).replace(' ', '')
            print('ООО "МЕДИА 47"' + '; ' + ostatok_media47)
            sheet['L50'].value = float(ostatok_media47.replace(',', '.'))

        elif 'ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ "ПРОЕКТНЫЕ РЕШЕНИЯ"' in text and 'СберБизнес' in text:
            ostatok_proektnie_reshenia_sber = \
                regex.search(r'Исходящий остаток 0,00 ([\d\s]+,\d{2})', text).group(1).replace(' ', '')
            print('ООО "ПРОЕКТНЫЕ РЕШЕНИЯ" СБЕР' + '; ' + ostatok_proektnie_reshenia_sber)
            sheet['L52'].value = float(ostatok_proektnie_reshenia_sber.replace(',', '.'))

        elif 'ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ "ОХТИНСКАЯ АЛЛЕЯ"' in text and 'СберБизнес' in text:
            ostatok_ohtinskaya_alleya_sber = \
                regex.search(r'Исходящий остаток 0,00 ([\d\s]+,\d{2})', text).group(1).replace(' ', '')
            print('ООО "ОХТИНСКАЯ АЛЛЕЯ" СБЕР' + '; ' + ostatok_ohtinskaya_alleya_sber)
            sheet['L54'].value = float(ostatok_ohtinskaya_alleya_sber.replace(',', '.'))

        elif 'ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ "ФОРМУЛА"' in text and 'СберБизнес' in text:
            ostatok_formula_sber = \
                regex.search(r'Исходящий остаток 0,00 ([\d\s]+,\d{2})', text).group(1).replace(' ', '')
            print('ООО "ФОРМУЛА" СБЕР' + '; ' + ostatok_formula_sber)
            sheet['L55'].value = float(ostatok_formula_sber.replace(',', '.'))

        elif 'ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ "Н1"' in text and 'СберБизнес' in text:
            ostatok_H1_sber = \
                regex.search(r'Исходящий остаток 0,00 ([\d\s]+,\d{2})', text).group(1).replace(' ', '')
            print('ООО "Н1" СБЕР' + '; ' + ostatok_H1_sber)
            sheet['L57'].value = float(ostatok_H1_sber.replace(',', '.'))

        elif 'ИНДИВИДУАЛЬНЫЙ ПРЕДПРИНИМАТЕЛЬ МАНЕВИЧ АЛЛА ЕФИМОВНА' in text and 'СберБизнес' in text:
            ostatok_manevich_sber = \
                regex.search(r'Исходящий остаток 0,00 ([\d\s]+,\d{2})', text).group(1).replace(' ', '')
            print('ИП Маневич СБЕР' + '; ' + ostatok_manevich_sber)
            sheet['L58'].value = float(ostatok_manevich_sber.replace(',', '.'))

        elif 'ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ "ПАРТНЕР"' in text and 'СберБизнес' in text:
            ostatok_partner_sber = \
                regex.search(r'Исходящий остаток 0,00 ([\d\s]+,\d{2})', text).group(1).replace(' ', '')
            print('ООО Партнер СБЕР' + '; ' + ostatok_partner_sber)
            sheet['L59'].value = float(ostatok_partner_sber.replace(',', '.'))
        elif 'ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ "СИТИИНВЕСТ"' in text and 'СберБизнес' in text:
            ostatok_sityinvest_sber = \
                regex.search(r'Исходящий остаток 0,00 ([\d\s]+,\d{2})', text).group(1).replace(' ', '')
            print('ООО СИТИИНВЕСТ СБЕР' + '; ' + ostatok_sityinvest_sber)
            sheet['L60'].value = float(ostatok_sityinvest_sber.replace(',', '.'))
        elif 'ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ "ДУДЕРГОФ"' in text and 'СберБизнес' in text:
            ostatok_dudergof_sber = \
                regex.search(r'Исходящий остаток 0,00 ([\d\s]+,\d{2})', text).group(1).replace(' ', '')
            print('ООО ДУДЕРГОФ СБЕР' + '; ' + ostatok_dudergof_sber)
            sheet['L61'].value = float(ostatok_dudergof_sber.replace(',', '.'))
        elif 'ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ "РОМАШКИ"' in text and 'СберБизнес' in text:
            ostatok_romashki_sber = \
                regex.search(r'Исходящий остаток 0,00 ([\d\s]+,\d{2})', text).group(1).replace(' ', '')
            print('ООО Ромашки СБЕР' + '; ' + ostatok_romashki_sber)
            sheet['L62'].value = float(ostatok_romashki_sber.replace(',', '.'))
        elif 'ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ "СТРОЙЭКСПЕРТРИТЕЙЛ"' in text and 'СберБизнес' in text:
            ostatok_ser_sber = \
                regex.search(r'Исходящий остаток 0,00 ([\d\s]+,\d{2})', text).group(1).replace(' ', '')
            print('ООО СЭР СБЕР' + '; ' + ostatok_ser_sber)
            sheet['L63'].value = float(ostatok_ser_sber.replace(',', '.'))
        elif 'ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ "БЕРГЕН"' in text and 'СберБизнес' in text:
            ostatok_bergen_sber = \
                regex.search(r'Исходящий остаток 0,00 ([\d\s]+,\d{2})', text).group(1).replace(' ', '')
            print('ООО БЕРГЕН СБЕР' + '; ' + ostatok_bergen_sber)
            sheet['L64'].value = float(ostatok_bergen_sber.replace(',', '.'))
        elif 'ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ "МЕТРО"' in text and 'СберБизнес' in text:
            ostatok_metro_sber = \
                regex.search(r'Исходящий остаток 0,00 ([\d\s]+,\d{2})', text).group(1).replace(' ', '')
            print('ООО МЕТРО СБЕР' + '; ' + ostatok_metro_sber)
            sheet['L65'].value = float(ostatok_metro_sber.replace(',', '.'))
        elif 'ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ "СЕВЕРНАЯ ЗВЕЗДА"' in text and 'СберБизнес' in text:
            ostatok_sev_zvezda_sber = \
                regex.search(r'Исходящий остаток 0,00 ([\d\s]+,\d{2})', text).group(1).replace(' ', '')
            print('ООО СЕВЕРНАЯ ЗВЕЗДА СБЕР' + '; ' + ostatok_sev_zvezda_sber)
            sheet['L66'].value = float(ostatok_sev_zvezda_sber.replace(',', '.'))
        elif 'ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ "ПРАГА"' in text and 'СберБизнес' in text:
            ostatok_praga_sber = \
                regex.search(r'Исходящий остаток 0,00 ([\d\s]+,\d{2})', text).group(1).replace(' ', '')
            print('ООО ПРАГА СБЕР' + '; ' + ostatok_praga_sber)
            sheet['L67'].value = float(ostatok_praga_sber.replace(',', '.'))
        elif 'ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ  "СП-ИМПОСТ"' in text and 'СберБизнес' in text:
            ostatok_sp_impost_sber = \
                regex.search(r'Исходящий остаток 0,00 ([\d\s]+,\d{2})', text).group(1).replace(' ', '')
            print('ООО СП-ИМПОСТ СБЕР' + '; ' + ostatok_sp_impost_sber)
            sheet['L68'].value = float(ostatok_sp_impost_sber.replace(',', '.'))
        elif 'ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ "АКВИТАНИЯ"' in text and 'СберБизнес' in text:
            ostatok_akvitania_sber = \
                regex.search(r'Исходящий остаток 0,00 ([\d\s]+,\d{2})', text).group(1).replace(' ', '')
            print('ООО АКВИТАНИЯ СБЕР' + '; ' + ostatok_akvitania_sber)
            sheet['L70'].value = float(ostatok_akvitania_sber.replace(',', '.'))
        elif 'ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ "ИММОБИ"' in text and 'СберБизнес' in text:
            ostatok_immobi_sber = \
                regex.search(r'Исходящий остаток 0,00 ([\d\s]+,\d{2})', text).group(1).replace(' ', '')
            print('ООО ИММОБИ СБЕР' + '; ' + ostatok_immobi_sber)
            sheet['L71'].value = float(ostatok_immobi_sber.replace(',', '.'))
        elif 'ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ "КУДРОВО-ИНВЕСТ"' in text and 'СберБизнес' in text:
            ostatok_kudrovo_invest_sber = \
                regex.search(r'Исходящий остаток 0,00 ([\d\s]+,\d{2})', text).group(1).replace(' ', '')
            print('ООО КУДРОВО-ИНВЕСТ СБЕР' + '; ' + ostatok_kudrovo_invest_sber)
            sheet['L72'].value = float(ostatok_kudrovo_invest_sber.replace(',', '.'))
        elif 'ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ "РИТЕЙЛ ПАРК"' in text and 'СберБизнес' in text:
            ostatok_riteil_park_sber = \
                regex.search(r'Исходящий остаток 0,00 ([\d\s]+,\d{2})', text).group(1).replace(' ', '')
            print('ООО РИТЕЙЛ ПАРК СБЕР' + '; ' + ostatok_riteil_park_sber)
            sheet['L73'].value = float(ostatok_riteil_park_sber.replace(',', '.'))

            # Райффайзен

        elif 'АНКОН' in text:
            ostatok_ankon = \
                regex.search(r'(Исходящий .+?)\n', text).group(1).replace(' ', '').replace('.', ',').split('balance')[1]
            print('ООО АНКОН' + '; ' + ostatok_ankon)
            sheet['L26'].value = float(ostatok_ankon.replace(',', '.'))

        # Открытие

        # elif 'ТОВАРИЩЕС ТВО СОБСТВЕННИКОВ НЕДВИЖИМОС ТИ "РЕПИНСКОЕ"' in text:
        #     ostatok_tsn = \
        #         regex.search(r'(ИСХОДЯЩИЙ .+?)\n\d+...', text).group(0).replace(' ', '').replace('.', ',').split('\n')[
        #             1]
        #     print('ТСН "РЕПИНСКОЕ"' + ';' + ostatok_tsn)
        #     sheet['L48'].value = float(ostatok_tsn.replace(',', '.'))


        # Банк Санкт-Петербург

        elif 'Счёт: 40702 810 3 9027 0000375' in text:
            ostatok_klever_375 = regex.search(r'(Списание .+?)\n', text).group(1).replace(' ', '').replace('.', ',')
            klever_375 = regex.split(',..', ostatok_klever_375)[2] + ',' + regex.split(',', ostatok_klever_375)[3]
            print('ООО "КЛЕВЕР375"' + '; ' + klever_375)
            sheet['AB3'].value = float(klever_375.replace(',', '.'))

        elif 'Счёт: 40702 810 7 9027 0000852' in text:
            ostatok_klever_852 = regex.search(r'(Списание .+?)\n', text).group(1).replace(' ', '').replace('.', ',')
            klever_852 = regex.split(',..', ostatok_klever_852)[2] + ',' + regex.split(',', ostatok_klever_852)[3]
            print('ООО "КЛЕВЕР852"' + '; ' + klever_852)
            sheet['AB4'].value = float(klever_852.replace(',', '.'))

        # elif 'Счёт: 40702 810 2 9027 0700610' in text:
        #     ostatok_klever_kard = regex.search(r'(Списание .+?)\n', text).group(1).replace(' ', '').replace('.', ',')
        #     klever_kard = regex.split(',..', ostatok_klever_kard)[2] + ',' + regex.split(',', ostatok_klever_kard)[3]
        #     print('ООО "КЛЕВЕР карта"' + '; ' + klever_kard)
        #     sheet['L5'].value = float(klever_kard.replace(',', '.'))

        elif 'Счёт: 40702 810 3 9027 0000414' in text:
            ostatok_reaktiv = regex.search(r'(Списание .+?)\n', text).group(1).replace(' ', '').replace('.', ',')
            reaktiv = regex.split(',..', ostatok_reaktiv)[2] + ',' + regex.split(',', ostatok_reaktiv)[3]
            print('ООО "Реактив"' + '; ' + reaktiv)
            sheet['L17'].value = float(reaktiv.replace(',', '.'))

        elif '0001648' in text:
            ostatok_romashki = regex.search(r'(Списание .+?)\n', text).group(1).replace(' ', '').replace('.', ',')
            romashki = regex.split(',..', ostatok_romashki)[2] + ',' + regex.split(',', ostatok_romashki)[3]
            print('ООО "Ромашки"' + '; ' + romashki)
            sheet['L19'].value = float(romashki.replace(',', '.'))

        # elif '0000296' in text:
        #     ostatok_smart = regex.search(r'(Списание .+?)\n', text).group(1).replace(' ', '').replace('.', ',')
        #     smart = regex.split(',..', ostatok_smart)[2] + ',' + regex.split(',', ostatok_smart)[3]
        #     print('ООО "Смарт Солюшн"' + '; ' + smart)
        #     sheet['L21'].value = float(smart.replace(',', '.'))


        # Точка

        # elif '40702810920000005223' in text:
        #     ostatok_zvezda1 = \
        #         regex.search(r'(Исходящее сальдо: .+?)$', text).group(0).replace(' ', '').replace('.', ',').split(':')[
        #             1]
        #     print('ООО "ЗВЕЗДА"' + ';' + ostatok_zvezda1)
        #     sheet['L45'].value = float(ostatok_zvezda1.replace(',', '.'))
        #
        # elif '40702810320000005674' in text:
        #     ostatok_zvezda2 = \
        #         regex.search(r'(Исходящее сальдо: .+?)$', text).group(0).replace(' ', '').replace('.', ',').split(':')[
        #             1]
        #     print('ООО "ЗВЕЗДА"' + ';' + ostatok_zvezda2)
        #     sheet['L46'].value = float(ostatok_zvezda2.replace(',', '.'))
        elif 'Клиент: ТОВАРИЩЕСТВО СОБСТВЕННИКОВ НЕДВИЖИМОСТИ "ОАЗИС"' in text:

            ostatok_tsn_oazis = regex.search(r'Исходящее сальдо:\s*([\d\s,.]+)', text).group(0).replace(' ', '').replace('.', ',').split(':')[
                    1]
            print(f'ТСН "ОАЗИС"'+'; '+ ostatok_tsn_oazis)
            sheet['L48'].value = float(ostatok_tsn_oazis.replace(',', '.'))

        elif 'Клиент: ТОВАРИЩЕСТВО СОБСТВЕННИКОВ НЕДВИЖИМОСТИ "РЕПИНСКОЕ 2"' in text:

            ostatok_tsn_r2_tochka = regex.search(r'Исходящее сальдо:\s*([\d\s,.]+)', text).group(0).replace(' ', '').replace('.', ',').split(':')[
                    1]
            print(f'ТСН "РЕПИНСКОЕ 2"'+'; '+ ostatok_tsn_r2_tochka)
            sheet['L53'].value = float(ostatok_tsn_r2_tochka.replace(',', '.'))

        # ВТБ

        elif 'Владелец счета: ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ "ОХТИНСКАЯ АЛЛЕЯ"' in text:

            ostatok_ohtinskaya_alleya_vtb = \
            regex.search(r'(ИСХОДЯЩИЙ ОСТАТОК\s*\d[\d\s]*.\d{2})', text).group(1).split('\n')[

                1].replace('\xa0', '').replace('.', ',')

            print('ООО "Охтинская аллея ВТБ"' + '; ' + ostatok_ohtinskaya_alleya_vtb)
            sheet['L13'].value = float(ostatok_ohtinskaya_alleya_vtb.replace(',', '.'))

        elif 'Владелец счета: ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ "ПАРТНЕР' in text:

            ostatok_partner_vtb = \
            regex.search(r'(ИСХОДЯЩИЙ ОСТАТОК\s*\d[\d\s]*.\d{2})', text).group(1).split('\n')[

                1].replace('\xa0', '').replace('.', ',')

            print('ООО "ПАРТНЕР" ВТБ"' + '; ' + ostatok_partner_vtb)
            sheet['L9'].value = float(ostatok_partner_vtb.replace(',', '.'))

        elif 'Владелец счета: ТОВАРИЩЕСТВО СОБСТВЕННИКОВ НЕДВИЖИМОСТИ "РЕПИНСКОЕ"' in text:

            ostatok_tsn_vtb = \
            regex.search(r'(ИСХОДЯЩИЙ ОСТАТОК\s*\d[\d\s]*.\d{2})', text).group(1).split('\n')[

                1].replace('\xa0', '').replace('.', ',')

            print('ТСН "РЕПИНСКОЕ ВТБ"' + '; ' + ostatok_tsn_vtb)
            sheet['L49'].value = float(ostatok_tsn_vtb.replace(',', '.'))

        elif 'Владелец счета: ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ "ФОРМУЛА' in text:

            ostatok_formula_vtb = \
            regex.search(r'(ИСХОДЯЩИЙ ОСТАТОК\s*\d[\d\s]*.\d{2})', text).group(1).split('\n')[

                1].replace('\xa0', '').replace('.', ',')

            print('ООО "ФОРМУЛА ВТБ"' + '; ' + ostatok_formula_vtb)
            sheet['L24'].value = float(ostatok_formula_vtb.replace(',', '.'))

        elif 'Владелец счета: Индивидуальный предприниматель ПАРФЕНЕНКО МАРИЯ АЛЕКСАНДРОВНА' in text:

            ostatok_parfenenko_vtb = \
            regex.search(r'(ИСХОДЯЩИЙ ОСТАТОК\s*\d[\d\s]*.\d{2})', text).group(1).split('\n')[

                1].replace('\xa0', '').replace('.', ',')

            print('ООО "ПАРФЕНЕНКО М.А. ВТБ"' + '; ' + ostatok_parfenenko_vtb)
            sheet['L11'].value = float(ostatok_parfenenko_vtb.replace(',', '.'))

        elif 'Владелец счета: ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ "СМАРТ СОЛЮШН"' in text:

            ostatok_smart_vtb = \
            regex.search(r'(ИСХОДЯЩИЙ ОСТАТОК\s*\d[\d\s]*.\d{2})', text).group(1).split('\n')[

                1].replace('\xa0', '').replace('.', ',')

            print('ООО Смарт Солюшн ВТБ"' + ';' + ostatok_smart_vtb)
            sheet['L21'].value = float(ostatok_smart_vtb.replace(',', '.'))

        elif 'Владелец счета: ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ "КЛЕВЕР"' in text:

            ostatok_klever_vtb = \
                regex.search(r'(ИСХОДЯЩИЙ ОСТАТОК\s*\d[\d\s]*.\d{2})', text).group(1).split('\n')[

                    1].replace('\xa0', '').replace('.', ',')

            print('ООО Клевер ВТБ"' + ';' + ostatok_klever_vtb)
            sheet['L5'].value = float(ostatok_klever_vtb.replace(',', '.'))

        elif 'Владелец счета: ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ "ПРАГА"' in text:

            ostatok_praga_vtb = \
                regex.search(r'(ИСХОДЯЩИЙ ОСТАТОК\s*\d[\d\s]*.\d{2})', text).group(1).split('\n')[

                    1].replace('\xa0', '').replace('.', ',')

            print('ООО Прага ВТБ"' + ';' + ostatok_praga_vtb)
            sheet['L51'].value = float(ostatok_praga_vtb.replace(',', '.'))

        elif 'Владелец счета: ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ "РАДУГА"' in text:

            ostatok_raduga_vtb = \
                regex.search(r'(ИСХОДЯЩИЙ ОСТАТОК\s*\d[\d\s]*.\d{2})', text).group(1).split('\n')[

                    1].replace('\xa0', '').replace('.', ',')

            print('ООО Радуга ВТБ"' + ';' + ostatok_raduga_vtb)
            sheet['L16'].value = float(ostatok_raduga_vtb.replace(',', '.'))

        elif 'Владелец счета: ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ "СИТИИНВЕСТ"' in text:

            ostatok_sityinvest_vtb = \
                regex.search(r'(ИСХОДЯЩИЙ ОСТАТОК\s*\d[\d\s]*.\d{2})', text).group(1).split('\n')[

                    1].replace('\xa0', '').replace('.', ',')

            print('ООО Ситиинвест ВТБ"' + ';' + ostatok_sityinvest_vtb)
            sheet['L69'].value = float(ostatok_sityinvest_vtb.replace(',', '.'))


        # СОВКОМБАНК

        elif 'Общество с ограниченной ответственностью "ГАСТРОПАРК"' in text:

            ostatok_gastropark = \
            regex.search(r'Исходящий остаток:\s*\n?\s*(?:Пассив\s*)?([\d\s,.]+)', text).group(1).replace(' ', '').replace('.', ',')

            print('ООО "ГАСТРОПАРК"' + '; ' + ostatok_gastropark)
            sheet['L24'].value = float(ostatok_gastropark.replace(',', '.'))


        elif 'Общество с ограниченной ответственностью "Н1"' in text:

            ostatok_H1 = \
            regex.search(r'Исходящий остаток:\s*\n?\s*(?:Пассив\s*)?([\d\s,.]+)', text).group(1).replace(' ', '').replace('.', ',')

            print('ООО "Н1"' + '; ' + ostatok_H1)
            sheet['L56'].value = float(ostatok_H1.replace(',', '.'))

        else:
            print('Другая организация')

sys.stdout = original_stdout
log_file.close()
        # АЛЬФА



reestr.save(r'\\192.168.1.9\fin\Arenda\_БОРИС\Reestr.xlsm')
reestr.close()

scopes = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

credentials = ServiceAccountCredentials.from_json_keyfile_name(
    r"D:\Users\user\Desktop\Выписки\steit-362219-f7abe8bc3429.json",
    scopes)  # access the json key you downloaded earlier
file = gspread.authorize(credentials)  # authenticate the JSON key with gspread
sheet = file.open("План_платежей (день)").worksheet("Account_balances")  # open sheet

def prepare_value(value):
    """Форматирует значение для корректной вставки в Google Sheets"""
    if isinstance(value, str):
        # Обработка формул (начинаются с =)
        if value.startswith('='):
            # Заменяем запятые на точки в числах внутри формулы
            parts = value[1:].split('+')
            formatted_parts = []
            for part in parts:
                try:
                    # Пробуем преобразовать в число, заменяя запятые
                    num = float(part.strip().replace('.', ','))
                    formatted_parts.append(str(num))
                except ValueError:
                    # Если не число, оставляем как есть
                    formatted_parts.append(part.strip())
            return '=' + '+'.join(formatted_parts)

        # Обработка обычных числовых значений
        try:
            return float(value.replace('.', ','))
        except ValueError:
            return value
    return value


# Подготовка данных с правильным форматированием
updates = [
    {'range': 'D2', 'values': [[prepare_value(ostatok_parfenenko)]]},
    {'range': 'D3', 'values': [[prepare_value(f"={ostatok_manevich}+{ostatok_manevich_sber}")]]},
    {'range': 'D5', 'values': [[prepare_value(f"={ostatok_steit}+{steit_ukb}")]]},
    {'range': 'D6', 'values': [[prepare_value(f"={ostatok_metro}+{ostatok_metro_sber}")]]},
    {'range': 'D8', 'values': [[prepare_value(ostatok_tsn_vtb)]]},
    {'range': 'D9', 'values': [[prepare_value(ostatok_tsn_r2_tochka)]]},
    {'range': 'D10', 'values': [[prepare_value(ostatok_tsn_oazis)]]},
    {'range': 'D12', 'values': [[prepare_value(ostatok_ankon)]]},
    {'range': 'D13', 'values': [[prepare_value(ostatok_kudrovo_s)]]},
    {'range': 'D14', 'values': [[prepare_value(f"={klever_375}+{klever_852}+{klever_sbr}+{ostatok_klever_vtb}")]]},
    {'range': 'D15', 'values': [[prepare_value(f"={ostatok_partner}+{ostatok_partner_vtb}+{ostatok_partner_sber}")]]},
    {'range': 'D16', 'values': [[prepare_value(f"={ostatok_ohtinskaya_alleya}+{ostatok_ohtinskaya_alleya_vtb}+{ostatok_ohtinskaya_alleya_sber}")]]},
    #{'range': 'D17', 'values': [[prepare_value(ostatok_gastropark)]]},
    {'range': 'D17', 'values': [[prepare_value(f"={ostatok_H1}+{ostatok_H1_sber}")]]},
    {'range': 'D18', 'values': [[prepare_value(f"={ostatok_raduga}+{ostatok_raduga_vtb}")]]},
    {'range': 'D19', 'values': [[prepare_value(f"={reaktiv}+{ostatok_reaktiv_sbr}")]]},
    {'range': 'D20', 'values': [[prepare_value(f"={romashki}+{romashki_ukb}+{ostatok_romashki_sber}")]]},
    {'range': 'D21', 'values': [[prepare_value(f"={ostatok_smart_vtb}+{smart_sbr}")]]},
    {'range': 'D22', 'values': [[prepare_value(f"={ostatok_formula}+{ostatok_formula_vtb}+{ostatok_formula_sber}")]]},
    {'range': 'D24', 'values': [[prepare_value(f"={ostatok_sityinvest}+{ostatok_sityinvest_sber}+{ostatok_sityinvest_vtb}")]]},
    {'range': 'D25', 'values': [[prepare_value(f"={ostatok_sev_zvezda}+{ostatok_sev_zvezda_sber}")]]},
    {'range': 'D26', 'values': [[prepare_value(f"={ostatok_dudergof}+{ostatok_dudergof_sber}")]]},
    {'range': 'D27', 'values': [[prepare_value(ostatok_m_invest)]]},
    {'range': 'D28', 'values': [[prepare_value(f"={ostatok_sp_impost}+{ostatok_sp_impost_sber}")]]},
    {'range': 'D29', 'values': [[prepare_value(f"={ostatok_praga}+{ostatok_praga_vtb}+{ostatok_praga_sber}")]]},
    {'range': 'D30', 'values': [[prepare_value(ostatok_frank)]]},
    {'range': 'D32', 'values': [[prepare_value(f"={ostatok_ser}+{ostatok_ser_sber}")]]},
    {'range': 'D33', 'values': [[prepare_value(ostatok_murino_g)]]},
    {'range': 'D34', 'values': [[prepare_value(f"={ostatok_akvitania}+{ostatok_akvitania_sber}")]]},
    {'range': 'D35', 'values': [[prepare_value(f"={ostatok_bergen}+{ostatok_bergen_sber}")]]},
    {'range': 'D37', 'values': [[prepare_value(f"={ostatok_immobi}+{ostatok_immobi_sber}")]]},
    {'range': 'D39', 'values': [[prepare_value(f"={ostatok_kudrovo_i}+{ostatok_kudrovo_invest_sber}")]]},
    {'range': 'D40', 'values': [[prepare_value(f"={ostatok_proektnie_reshenia}+{ostatok_proektnie_reshenia_sber}")]]},
    {'range': 'D41', 'values': [[prepare_value(f"={ostatok_riteil_park}+{ostatok_riteil_park_sber}")]]},
    {'range': 'D42', 'values': [[prepare_value(ostatok_media47)]]},
    {'range': 'D44', 'values': [[prepare_value(ostatok_parfenenko_vtb)]]}
]

# Выполнение обновлений
sheet.batch_update(updates, value_input_option='USER_ENTERED')

# === ПОЛУЧАЕМ ИНФОРМАЦИЮ О ДЕПОЗИТАХ ===
# Получаем все данные из листа
all_data = sheet.get_all_values()

# Словарь для хранения депозитов по компаниям
deposits_dict = {}

# Проходим по всем строкам листа
for i, row in enumerate(all_data):
    # Проверяем, что строка содержит данные
    if len(row) >= 10:  # Нужны хотя бы столбцы до J
        company_name = row[0]  # Столбец A
        deposit_amount = row[6]  # Столбец G
        deposit_date = row[9]  # Столбец J

        # Проверяем, есть ли депозит (не пустые значения)
        if deposit_amount and deposit_amount.strip() and deposit_date and deposit_date.strip():
            # Убираем лишние пробелы
            company_name = company_name.strip()
            deposit_amount = deposit_amount.strip()
            deposit_date = deposit_date.strip()

            try:
                # Парсим сумму депозита (убираем пробелы, заменяем запятые на точки)
                amount_str = deposit_amount.replace(' ', '').replace(',', '.')
                # Убираем нечисловые символы, кроме точки
                clean_amount = ''.join(c for c in amount_str if c.isdigit() or c == '.')
                if clean_amount:
                    amount = float(clean_amount)

                    # Форматируем сумму с разделителями тысяч
                    formatted_amount = f"{amount:,.0f}".replace(',', '.')

                    # Форматируем дату
                    formatted_date = deposit_date

                    # Если дата в числовом формате Excel/Google Sheets
                    try:
                        date_value = float(deposit_date)
                        import datetime

                        base_date = datetime.datetime(1899, 12, 30)
                        date_obj = base_date + datetime.timedelta(days=date_value)
                        formatted_date = date_obj.strftime("%d.%m.%Y")
                    except:
                        # Если не удалось преобразовать в число, оставляем как есть
                        pass

                    # Добавляем информацию о депозите в словарь
                    if company_name not in deposits_dict:
                        deposits_dict[company_name] = []
                    deposits_dict[company_name].append(
                        f"Размещен депозит на сумму {formatted_amount} до {formatted_date}")

            except ValueError as e:
                # Пропускаем строки с некорректными данными
                print(f"Ошибка обработки строки {i + 1}: {e}")
                continue

# === ФОРМИРУЕМ ТЕКСТ С ОСТАТКАМИ И ДЕПОЗИТАМИ ===

text = 'Остатки на счетах обновлены' + '\n''\n' + \
       'Управляющие компании:' + '\n' + '\n' \
                                        f'ИП Маневич А.Е. - {float(ostatok_manevich.replace(",", ".")):,}'
if 'ИП Маневич А.Е.' in deposits_dict:
    for deposit_info in deposits_dict['ИП Маневич А.Е.']:
        text += f'\n  {deposit_info}'
text += '\n' + \
        f'ИП Маневич А.Е. СБЕР - {float(ostatok_manevich_sber.replace(",", ".")):,}' + '\n' + \
        f'ИП Парфененко М.А. - {float(ostatok_parfenenko.replace(",", ".")):,}'
if 'ИП Парфененко М.А.' in deposits_dict:
    for deposit_info in deposits_dict['ИП Парфененко М.А.']:
        text += f'\n  {deposit_info}'
text += '\n' + \
        f'ИП Парфененко М.А. ВТБ - {float(ostatok_parfenenko_vtb.replace(",", ".")):,}' + '\n' + \
        'ООО "Клевер"' + ' - ' + '{:,}'.format(
    float(klever_375.replace(',', '.')) + float(klever_852.replace(',', '.')) + float(
        klever_sbr.replace(',', '.')) + float(ostatok_klever_vtb.replace(',', '.')), 2)
if 'ООО "Клевер"' in deposits_dict:
    for deposit_info in deposits_dict['ООО "Клевер"']:
        text += f'\n  {deposit_info}'
text += '\n' + \
        'ООО "Формула"' + ' - ' + '{:,}'.format(round(
    float(ostatok_formula.replace(',', '.')) + float(ostatok_formula_vtb.replace(',', '.')) + float(
        ostatok_formula_sber.replace(',', '.')), 2))
if 'ООО "Формула"' in deposits_dict:
    for deposit_info in deposits_dict['ООО "Формула"']:
        text += f'\n  {deposit_info}'
text += '\n' + \
        f'ООО "Партнер" - {float(ostatok_partner.replace(",", ".")):,}'
if 'ООО "Партнер"' in deposits_dict:
    for deposit_info in deposits_dict['ООО "Партнер"']:
        text += f'\n  {deposit_info}'
text += '\n' + \
        f'ООО "Партнер" СБЕР - {float(ostatok_partner_sber.replace(",", ".")):,}' + '\n' + \
        f'ООО "Партнер" ВТБ - {float(ostatok_partner_vtb.replace(",", ".")):,}' + '\n' + \
        'ООО "Радуга"' + ' - ' + '{:,}'.format(
    round(float(ostatok_raduga.replace(',', '.')) + float(ostatok_raduga_vtb.replace(',', '.')), 2))
if 'ООО "Радуга"' in deposits_dict:
    for deposit_info in deposits_dict['ООО "Радуга"']:
        text += f'\n  {deposit_info}'
text += '\n' + \
        'ООО "Реактив"' + ' - ' + '{:,}'.format(
    round(float(reaktiv.replace(',', '.')) + float(ostatok_reaktiv_sbr.replace(',', '.')), 2))
if 'ООО "Реактив"' in deposits_dict:
    for deposit_info in deposits_dict['ООО "Реактив"']:
        text += f'\n  {deposit_info}'
text += '\n' + \
        'ООО "Ромашки"' + ' - ' + '{:,}'.format(round(
    float(romashki.replace(',', '.')) + float(romashki_ukb.replace(',', '.')) + float(
        ostatok_romashki_sber.replace(',', '.')), 2))
if 'ООО "Ромашки"' in deposits_dict:
    for deposit_info in deposits_dict['ООО "Ромашки"']:
        text += f'\n  {deposit_info}'
text += '\n' + \
        'ООО "Смарт Солюшн"' + ' - ' + '{:,}'.format(
    round(float(ostatok_smart_vtb.replace(',', '.')) + float(smart_sbr.replace(',', '.')), 2))
if 'ООО "Смарт Солюшн"' in deposits_dict:
    for deposit_info in deposits_dict['ООО "Смарт Солюшн"']:
        text += f'\n  {deposit_info}'
text += '\n' + \
        f'ООО "КУДРОВО-СТРОЙ" - {float(ostatok_kudrovo_s.replace(",", ".")):,}'
if 'ООО "КУДРОВО-СТРОЙ"' in deposits_dict:
    for deposit_info in deposits_dict['ООО "КУДРОВО-СТРОЙ"']:
        text += f'\n  {deposit_info}'
text += '\n' + \
        'ООО "Охтинская аллея"' + ' - ' + '{:,}'.format(round(
    float(ostatok_ohtinskaya_alleya.replace(',', '.')) + float(
        ostatok_ohtinskaya_alleya_vtb.replace(',', '.')) + +float(ostatok_ohtinskaya_alleya_sber.replace(',', '.')), 2))
if 'ООО "Охтинская аллея"' in deposits_dict:
    for deposit_info in deposits_dict['ООО "Охтинская аллея"']:
        text += f'\n  {deposit_info}'
text += '\n' + \
        f'ООО "ГАСТРОПАРК" - {float(ostatok_gastropark.replace(",", ".")):,}'
if 'ООО "ГАСТРОПАРК"' in deposits_dict:
    for deposit_info in deposits_dict['ООО "ГАСТРОПАРК"']:
        text += f'\n  {deposit_info}'
text += '\n' + \
        f'ООО "Н1" - {float(ostatok_H1.replace(",", ".")):,}'
if 'ООО "Н1"' in deposits_dict:
    for deposit_info in deposits_dict['ООО "Н1"']:
        text += f'\n  {deposit_info}'
text += '\n' + \
        f'ООО "Н1" СБЕР - {float(ostatok_H1_sber.replace(",", ".")):,}' + '\n' + \
        f'ООО "АНКОН" - {float(ostatok_ankon.replace(",", ".")):,}'
if 'ООО "АНКОН"' in deposits_dict:
    for deposit_info in deposits_dict['ООО "АНКОН"']:
        text += f'\n  {deposit_info}'
text += '\n' + \
        f'ТСН "ОАЗИС" - {float(ostatok_tsn_oazis.replace(",", ".")):,}'
if 'ТСН "ОАЗИС"' in deposits_dict:
    for deposit_info in deposits_dict['ТСН "ОАЗИС"']:
        text += f'\n  {deposit_info}'
text += '\n' + \
        f'ТСН "РЕПИНСКОЕ ВТБ" - {float(ostatok_tsn_vtb.replace(",", ".")):,}'
if 'ТСН "РЕПИНСКОЕ ВТБ"' in deposits_dict:
    for deposit_info in deposits_dict['ТСН "РЕПИНСКОЕ ВТБ"']:
        text += f'\n  {deposit_info}'
text += '\n' + \
        f'ТСН "РЕПИНСКОЕ 2 ТОЧКА" - {float(ostatok_tsn_r2_tochka.replace(",", ".")):,}'
if 'ТСН "РЕПИНСКОЕ 2 ТОЧКА"' in deposits_dict:
    for deposit_info in deposits_dict['ТСН "РЕПИНСКОЕ 2 ТОЧКА"']:
        text += f'\n  {deposit_info}'
text += '\n' + \
        f'МЕДИА 47" - {float(ostatok_media47.replace(",", ".")):,}'
if 'МЕДИА 47"' in deposits_dict:
    for deposit_info in deposits_dict['МЕДИА 47"']:
        text += f'\n  {deposit_info}'
text += '\n' + '\n' + \
        'Балансо-держатели:' + '\n' + '\n' \
                                      f'ООО "Дудергоф" - {float(ostatok_dudergof.replace(",", ".")):,}'
if 'ООО "Дудергоф"' in deposits_dict:
    for deposit_info in deposits_dict['ООО "Дудергоф"']:
        text += f'\n  {deposit_info}'
text += '\n' + \
        f'ООО "Дудергоф СБЕР" - {float(ostatok_dudergof_sber.replace(",", ".")):,}' + '\n' + \
        f'ООО "М-Инвест" - {float(ostatok_m_invest.replace(",", ".")):,}'
if 'ООО "М-Инвест"' in deposits_dict:
    for deposit_info in deposits_dict['ООО "М-Инвест"']:
        text += f'\n  {deposit_info}'
text += '\n' + \
        f'ООО "СП-Импост" - {float(ostatok_sp_impost.replace(",", ".")):,}'
if 'ООО "СП-Импост"' in deposits_dict:
    for deposit_info in deposits_dict['ООО "СП-Импост"']:
        text += f'\n  {deposit_info}'
text += '\n' + \
        f'ООО "СП-Импост СБЕР" - {float(ostatok_sp_impost_sber.replace(",", ".")):,}' + '\n' + \
        'ООО "Прага"' + ' - ' + '{:,}'.format(round(
    float(ostatok_praga.replace(",", ".")) + float(ostatok_praga_vtb.replace(",", ".")) + float(
        ostatok_praga_sber.replace(",", ".")), 2))
if 'ООО "Прага"' in deposits_dict:
    for deposit_info in deposits_dict['ООО "Прага"']:
        text += f'\n  {deposit_info}'
text += '\n' + \
        f'ООО "Северная звезда" - {float(ostatok_sev_zvezda.replace(",", ".")):,}'
if 'ООО "Северная звезда"' in deposits_dict:
    for deposit_info in deposits_dict['ООО "Северная звезда"']:
        text += f'\n  {deposit_info}'
text += '\n' + \
        f'ООО "Северная звезда" СБЕР - {float(ostatok_sev_zvezda_sber.replace(",", ".")):,}' + '\n' + \
        f'ООО "СитиИнвест" - {float(ostatok_sityinvest.replace(",", ".")):,}'
if 'ООО "СитиИнвест"' in deposits_dict:
    for deposit_info in deposits_dict['ООО "СитиИнвест"']:
        text += f'\n  {deposit_info}'
text += '\n' + \
        f'ООО "СитиИнвест СБЕР" - {float(ostatok_sityinvest_sber.replace(",", ".")):,}' + '\n' + \
        f'ООО "СитиИнвест ВТБ" - {float(ostatok_sityinvest_vtb.replace(",", ".")):,}' + '\n' + \
        f'ООО "Франк" - {float(ostatok_frank.replace(",", ".")):,}'
if 'ООО "Франк"' in deposits_dict:
    for deposit_info in deposits_dict['ООО "Франк"']:
        text += f'\n  {deposit_info}'
text += '\n' + \
        f'ООО "МЕТРО" - {float(ostatok_metro.replace(",", ".")):,}'
if 'ООО "МЕТРО"' in deposits_dict:
    for deposit_info in deposits_dict['ООО "МЕТРО"']:
        text += f'\n  {deposit_info}'
text += '\n' + \
        f'ООО "МЕТРО" СБЕР - {float(ostatok_metro_sber.replace(",", ".")):,}' + '\n' + \
        'ООО "СТЕЙТ"' + ' - ' + '{:,}'.format(
    round(float(ostatok_steit.replace(',', '.')) + float(steit_ukb.replace(',', '.')), 2))
if 'ООО "СТЕЙТ"' in deposits_dict:
    for deposit_info in deposits_dict['ООО "СТЕЙТ"']:
        text += f'\n  {deposit_info}'
text += '\n' + '\n' + \
        'Инвестиционные компании' + '\n' + '\n' + \
        f'ООО "АКВИТАНИЯ" - {float(ostatok_akvitania.replace(",", ".")):,}' + '\n' + \
        f'ООО "АКВИТАНИЯ СБЕР" - {float(ostatok_akvitania_sber.replace(",", ".")):,}'
if 'ООО "АКВИТАНИЯ"' in deposits_dict:
    for deposit_info in deposits_dict['ООО "АКВИТАНИЯ"']:
        text += f'\n  {deposit_info}'
text += '\n' + \
        f'ООО "БЕРГЕН" - {float(ostatok_bergen.replace(",", ".")):,}'
if 'ООО "БЕРГЕН"' in deposits_dict:
    for deposit_info in deposits_dict['ООО "БЕРГЕН"']:
        text += f'\n  {deposit_info}'
text += '\n' + \
        f'ООО "БЕРГЕН СБЕР" - {float(ostatok_bergen_sber.replace(",", ".")):,}' + '\n' + \
        f'ООО "ИММОБИ СБЕР" - {float(ostatok_immobi_sber.replace(",", ".")):,}' + '\n' + \
        f'ООО "ИММОБИ" - {float(ostatok_immobi.replace(",", ".")):,}'
if 'ООО "ИММОБИ"' in deposits_dict:
    for deposit_info in deposits_dict['ООО "ИММОБИ"']:
        text += f'\n  {deposit_info}'
text += '\n' + \
        f'ООО "Ритейл Парк" - {float(ostatok_riteil_park.replace(",", ".")):,}' + '\n' + \
        f'ООО "Ритейл Парк СБЕР" - {float(ostatok_riteil_park_sber.replace(",", ".")):,}'
if 'ООО "Ритейл Парк"' in deposits_dict:
    for deposit_info in deposits_dict['ООО "Ритейл Парк"']:
        text += f'\n  {deposit_info}'
text += '\n' + \
        f'ООО "Кудрово-Инвест" - {float(ostatok_kudrovo_i.replace(",", ".")):,}' + '\n' + \
        f'ООО "Кудрово-Инвест СБЕР" - {float(ostatok_kudrovo_invest_sber.replace(",", ".")):,}'
if 'ООО "Кудрово-Инвест"' in deposits_dict:
    for deposit_info in deposits_dict['ООО "Кудрово-Инвест"']:
        text += f'\n  {deposit_info}'
text += '\n' + \
        f'ООО "Мурино-Град" - {float(ostatok_murino_g.replace(",", ".")):,}'
if 'ООО "Мурино-Град"' in deposits_dict:
    for deposit_info in deposits_dict['ООО "Мурино-Град"']:
        text += f'\n  {deposit_info}'
text += '\n' + \
        f'ООО "Проектные решения" - {float(ostatok_proektnie_reshenia.replace(",", ".")):,}'
if 'ООО "Проектные решения"' in deposits_dict:
    for deposit_info in deposits_dict['ООО "Проектные решения"']:
        text += f'\n  {deposit_info}'
text += '\n' + \
        f'ООО "Проектные решения" СБЕР - {float(ostatok_proektnie_reshenia_sber.replace(",", ".")):,}' + '\n' + '\n' + \
        'Ген подрядные компании' + '\n' + '\n' + \
        f'ООО "СЭР" - {float(ostatok_ser.replace(",", "."))}'
if 'ООО "СЭР"' in deposits_dict:
    for deposit_info in deposits_dict['ООО "СЭР"']:
        text += f'\n  {deposit_info}'
text += '\n' + \
        f'ООО "СЭР" СБЕР - {float(ostatok_ser_sber.replace(",", "."))}'
if 'ООО "СЭР" СБЕР' in deposits_dict:
    for deposit_info in deposits_dict['ООО "СЭР" СБЕР']:
        text += f'\n  {deposit_info}'

# Если нужно, можно добавить отдельный раздел с депозитами в конце:
# Дополнительно добавляем все депозиты, которые не попали в основные списки
text += '\n\n' + 'Дополнительные депозиты:' + '\n'
added_deposits = set(['ИП Маневич А.Е.', 'ИП Парфененко М.А.', 'ООО "Клевер"', 'ООО "Формула"',
                      'ООО "Партнер"', 'ООО "Радуга"', 'ООО "Реактив"', 'ООО "Ромашки"',
                      'ООО "Смарт Солюшн"', 'ООО "КУДРОВО-СТРОЙ"', 'ООО "Охтинская аллея"',
                      'ООО "ГАСТРОПАРК"', 'ООО "Н1"', 'ООО "АНКОН"', 'ТСН "ОАЗИС"',
                      'ТСН "РЕПИНСКОЕ ВТБ"', 'ТСН "РЕПИНСКОЕ 2 ТОЧКА"', 'МЕДИА 47"',
                      'ООО "Дудергоф"', 'ООО "М-Инвест"', 'ООО "СП-Импост"', 'ООО "Прага"',
                      'ООО "Северная звезда"', 'ООО "СитиИнвест"', 'ООО "Франк"',
                      'ООО "МЕТРО"', 'ООО "СТЕЙТ"', 'ООО "АКВИТАНИЯ"', 'ООО "БЕРГЕН"',
                      'ООО "ИММОБИ"', 'ООО "Ритейл Парк"', 'ООО "Кудрово-Инвест"',
                      'ООО "Мурино-Град"', 'ООО "Проектные решения"', 'ООО "СЭР"',
                      'ООО "СЭР" СБЕР'])

for company_name, deposit_list in deposits_dict.items():
    if company_name not in added_deposits:
        text += f'\n{company_name}:'
        for deposit_info in deposit_list:
            text += f'\n  {deposit_info}'


bot.send_message(chat_id, text)


def send_telegram(text: str):
    token = "5617912411:AAFaAFs0NcEOZR5iJwsEOO7iVrRPFFKzFh8"
    url = "https://api.telegram.org/bot"
    channel_id = chat_id #"@SteitVipiska_bot"
    url += token
    method = url + "/sendMessage"

    r = requests.post(method, data={
        "chat_id": chat_id,
        "text": text
    })

    if r.status_code != 200:
        raise Exception(f"Error: {r.status_code}-{r.text}")