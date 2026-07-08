function sendMorozov() {

  var day = Utilities.formatDate(new Date(), "GMT+1", "dd.MM.yyyy")

  //sendText(clientIdChat1,"Оплаты СУ26 на "+ day +" отправлены Морозову, Егорову");
  //sendText(nelli,"Оплаты СУ26 на "+ day +" отправлены Морозову, Егорову");

  var spreadsheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName("План_на_день");
  var searchValue = "СУ 26 ООО"; // замените на значение, которое вы ищете
  var columnNumber = 4; // замените на номер столбца, в котором вы ищете значение
  var values = spreadsheet.getRange(1, columnNumber, spreadsheet.getLastRow()).getValues(); // получаем значения из указанного столбца
  var send_to_mos = "";
  var amount = 0
  for (var i = 1; i < values.length; i++) {
    if (values[i][0] == searchValue) {
      var org = spreadsheet.getRange("C"+(i+1)).getValue();
      var range_ds = spreadsheet.getRange("N"+(i+1)).getValue();
      var range_sum = spreadsheet.getRange("E"+(i+1)).getValue();
      amount = amount+range_sum
      var to_mos = org + " - " + range_ds + ". Сумма - " + range_sum.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ' ') +"<br/>";
      var amount_org = "Всего " + " - " + amount.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ' ')+"<br/>"; //.setNumberFormat('# ###')
      send_to_mos=send_to_mos+to_mos;
      //Logger.log(send_to_mos);
    } else {
      
    }

  }
 if (send_to_mos != ""){

  var message1 = {
    to: "mos@steit.ru, egorov@steit.ru, pankov@steit.ru, v.chemodanova@steit.ru",
    subject: "Оплаты СТЕЙТ и МЕТРО на "+day,
    htmlBody:'Добрый день, Олег Сергеевич! <br/> <br/> Оплаты в СУ26 от СТЕЙТ, МЕТРО и Проектные решения на ' + day + '<br/>' + send_to_mos + '<br/>' + amount_org + '<br/> С уважением,<br/> "" <br/> Финансовый менеджер <br/> Инвестиционно-управляющая компания STEIT <br/> Телефон: +7(812)777-77-07 (221) <br/> Мобильный: +7(999)999-99-99 <br/> Веб-сайт: www.steit.ru <br/> Санкт-Петербург,<br/>Набережная реки Карповки, д.19 лит.А',
    name: "Отдел финансового контроля",
  }
  //GmailApp.sendEmail("pankov@steit.ru","day",day);
  //Logger.log(message1);
  MailApp.sendEmail(message1);
  notifyFinGroup('Оплаты СУ26 на ' + day + ' отправлены Морозову, Егорову');

 }

}

function sendText(chatId, text, keyBoard) {
  let data = {
    method: 'post',
    payload: {
      method: 'sendMessage',
      chat_id: String(chatId),
      text: text,
      parse_mode: 'HTML',
      reply_markup: JSON.stringify(keyBoard)
    }
  }
  UrlFetchApp.fetch('https://api.telegram.org/bot' + token + '/', data);
} 