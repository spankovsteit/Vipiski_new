function onOpen2() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheetRazovye = ss.getSheetByName("Разовые");
  var sheetRegulyarnye = ss.getSheetByName("Регулярные");
  var planNaDen = ss.getSheetByName("План_на_день");

  // Ждём, пока данные загрузятся
  waitForImportRange(planNaDen, "B6");
  waitForImportRange(sheetRazovye, "B2");
  waitForImportRange(sheetRegulyarnye, "B2");

  // Определяем последнюю заполненную строку по столбцу C
  var lastRow1 = getLastFilledRow(sheetRazovye, "C");
  var lastRow2 = getLastFilledRow(sheetRegulyarnye, "C");
  var lastRow3 = getLastFilledRow(planNaDen, "C");

  // Удаление старых чекбоксов
  sheetRazovye.getRange("A2:A" + lastRow1).removeCheckboxes();
  sheetRegulyarnye.getRange("A2:A" + lastRow2).removeCheckboxes();

  // Добавление чекбоксов
  sheetRazovye.getRange("A2:A" + lastRow1).insertCheckboxes();
  sheetRegulyarnye.getRange("A2:A" + lastRow2).insertCheckboxes();

  // Установка значения TRUE для всех новых чекбоксов
  if (lastRow1 > 1) sheetRazovye.getRange("A2:A" + lastRow1).setValue(true);
  if (lastRow2 > 1) sheetRegulyarnye.getRange("A2:A" + lastRow2).setValue(true);

  // Добавление меню в интерфейс
  SpreadsheetApp.getUi()
    .createMenu('Действия с Реестром')
    .addItem('Согласовано', 'sendZayavka')
    .addSeparator()
    .addItem('Отправить на согласование', 'sendRoman')
    .addSeparator()
    .addItem('Отправить платежи СУ26', 'sendMorozov')
    .addToUi();
}

// Функция ожидания загрузки IMPORTRANGE
function waitForImportRange(sheet, checkCell) {
  var maxAttempts = 5;
  var attempt = 0;

  while (attempt < maxAttempts) {
    var value = sheet.getRange(checkCell).getValue();
    if (value !== "") return;
    Utilities.sleep(2000);
    attempt++;
  }

  SpreadsheetApp.getUi().alert("Данные на листе '" + sheet.getName() + "' не загрузились.");
}

// Функция определения последней заполненной строки в указанном столбце
function getLastFilledRow(sheet, columnLetter) {
  var column = sheet.getRange(columnLetter + "2:" + columnLetter).getValues(); // Берем значения со 2-й строки
  for (var i = column.length - 1; i >= 0; i--) {
    if (column[i][0] !== "") return i + 2; // Смещаем индекс на 2, так как начинаем со 2-й строки
  }
  return 1; // Если всё пусто, возвращаем 1 (чтобы чекбоксы не проставлялись)
}