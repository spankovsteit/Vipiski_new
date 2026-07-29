function clearTransferSheets() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  
  // Очищаем лист ToRegular
  const toRegularSheet = ss.getSheetByName('ToRegular');
  if (toRegularSheet) {
    const lastRow = toRegularSheet.getLastRow();
    if (lastRow > 1) {
      toRegularSheet.getRange(2, 1, lastRow - 1, toRegularSheet.getLastColumn()).clear();
    }
  }
  
  // Очищаем лист ToOnTime
  const toOnTimeSheet = ss.getSheetByName('ToOnTime');
  if (toOnTimeSheet) {
    const lastRow = toOnTimeSheet.getLastRow();
    if (lastRow > 1) {
      toOnTimeSheet.getRange(2, 1, lastRow - 1, toOnTimeSheet.getLastColumn()).clear();
    }
  }
  
  //SpreadsheetApp.getUi().alert('Листы ToRegular и ToOnTime очищены (кроме заголовков)');
}
