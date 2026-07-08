function onOpen1() {

//var ReestrlastRow1 = SpreadsheetApp.getActiveSpreadsheet().getSheetByName("Разовые").getLastRow();
//var ReestrlastRow2 = SpreadsheetApp.getActiveSpreadsheet().getSheetByName("Регулярные").getLastRow();

//SpreadsheetApp.getActiveSpreadsheet().getSheetByName("Разовые")
//  .getRange("A2:A"+ReestrlastRow1)
//  .removeCheckboxes()

//SpreadsheetApp.getActiveSpreadsheet().getSheetByName("Регулярные")
//  .getRange("A2:A"+ReestrlastRow2)
//  .removeCheckboxes()

//if (checkUser()) {

  SpreadsheetApp.getUi()  
  .createMenu('Действия с Реестром')  
  .addItem('Согласовано', 'sendZayavka')
  .addSeparator() 
  .addItem('Отправить на согласование', 'sendRoman')
  .addSeparator() 
  .addItem('Отправить платежи СУ26', 'sendMorozov')    
  //.addSeparator()  
  //.addSubMenu(SpreadsheetApp.getUi().createMenu('Кастом подменю')
  //.addItem('-Функция 2', 'myFunction2')
  //.addItem('-Функция 3', 'myFunction3')
  //.addItem('Функция 4', 'myFunction4')
  .addToUi();

//else return;

//var ReestrlastRow1 = SpreadsheetApp.getActiveSpreadsheet().getSheetByName("Разовые").getLastRow();
//var ReestrlastRow2 = SpreadsheetApp.getActiveSpreadsheet().getSheetByName("Регулярные").getLastRow();

//SpreadsheetApp.getActiveSpreadsheet().getSheetByName("Разовые")
//    .getRange("A2:A"+ReestrlastRow1)
//    .insertCheckboxes().check()

//SpreadsheetApp.getActiveSpreadsheet().getSheetByName("Регулярные")
//    .getRange("A2:A"+ReestrlastRow2)
//    .insertCheckboxes().check()

}

/*function checkUser() {
    var okUsers = ["stvipiska@gmail.com", "klochikhin.k@gmail.com", "rs@agses.su", "spankovsteit@gmail.com", "v7272.rs@gmail.com"];
    Logger.log(okUsers)
    var user = Session.getEffectiveUser().getEmail();
    Logger.log(user)
    for (var u in okUsers)  if (user == okUsers[u]) return true;
    SpreadsheetApp.getUi().alert("Your email is not authorized to use this function.333");
    return false;
}*/