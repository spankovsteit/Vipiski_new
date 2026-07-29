function appendNegativeRows() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheet1 = ss.getSheetByName('Регулярные');
  var sheet2 = ss.getSheetByName('ToOnTime');
  
  var data = sheet1.getDataRange().getValues();
  var negativeRows = [];
  
  for (var i = 1; i < data.length; i++) {
    var valueR = data[i][17];
    if (typeof valueR === 'number' && valueR < 0) {
      negativeRows.push(data[i]);
    }
  }
  
  if (negativeRows.length > 0) {
    // Добавляем в конец (без очистки предыдущих данных)
    var lastRow = sheet2.getLastRow();
    sheet2.getRange(lastRow + 1, 1, negativeRows.length, negativeRows[0].length).setValues(negativeRows);
    notifyFinGroup(
      'Перенос из регулярки в разовые: добавлено ' + negativeRows.length + ' строк(и)'
    );
  } else {
    notifyFinGroup('Перенос из регулярки в разовые: отрицательных строк не найдено');
  }
}
