function ZPClear() {
  var range = SpreadsheetApp
 .getActive()
 .getSheetByName("ЗП")
 .getRange(2,2,18,1);
 range.clear();
}
