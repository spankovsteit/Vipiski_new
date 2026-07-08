/**
 * Автоматически вызывается при открытии таблицы
 * @param {Object} e - Объект события
 */
function onOpen(e) {
  try {
    // Быстро создаем меню без ожидания (чтобы пользователь сразу его увидел)
    createBaseMenu();
    
    // Если у пользователя есть права на редактирование - запускаем фоновые процессы
    if (e && e.authMode !== ScriptApp.AuthMode.NONE) {
      setupCheckboxes();
    }
  } catch (error) {
    console.error('Ошибка в onOpen:', error);
    // Создаем минимальное меню даже при ошибке
    SpreadsheetApp.getUi()
      .createMenu('Ошибка')
      .addItem('Обновить', 'forceReload')
      .addToUi();
  }
}

/**
 * Создает основное меню
 */
function createBaseMenu() {
  SpreadsheetApp.getUi()
    .createMenu('Действия с Реестром')
    .addItem('Отправить на согласование ФД', 'send_for_approval_FD')
    .addSeparator()
    .addItem('Отправить на согласование РВС', 'sendRoman')
    .addSeparator()
    .addItem('Согласовано ФД', 'approved_by_the_FD')
    .addSeparator()
    .addItem('Согласовано РВС', 'sendZayavka')
    .addSeparator()
    .addItem('Отправить платежи СУ26', 'sendMorozov')
    .addSeparator()
    .addItem('Отправить регулярные в бухгалтерию', 'sendBuh')
    .addSeparator()
    .addItem('Обновить чекбоксы', 'setupCheckboxesFromMenu')
    .addItem('Перенос из регулярки в разовые', 'appendNegativeRows')
    .addItem('Перезагрузить меню', 'forceReload')
    .addToUi();
}

/**
 * Настройка чекбоксов на всех листах
 */
function setupCheckboxes(notify) {
  try {
    var ss = SpreadsheetApp.getActiveSpreadsheet();
    var sheets = ['Разовые', 'Регулярные'];
    
    sheets.forEach(function(sheetName) {
      var sheet = ss.getSheetByName(sheetName);
      if (!sheet) {
        console.warn('Лист "' + sheetName + '" не найден');
        return;
      }
      
      var lastRow = getLastFilledRow(sheet, 'C');
      if (lastRow > 1) {
        var checkboxRange = sheet.getRange('A2:A' + lastRow);
        checkboxRange.removeCheckboxes();
        checkboxRange.insertCheckboxes();
        checkboxRange.setValue(true);
      }
    });
    
    console.log('Чекбоксы успешно обновлены');
    if (notify) {
      notifyFinGroup('Чекбоксы в реестре обновлены');
    }
  } catch (error) {
    console.error('Ошибка в setupCheckboxes:', error);
    throw error;
  }
}

/** Пункт меню «Обновить чекбоксы» — с уведомлением в Telegram и Bitrix24. */
function setupCheckboxesFromMenu() {
  setupCheckboxes(true);
}

/**
 * Определяет последнюю заполненную строку
 * @param {Sheet} sheet - Лист таблицы
 * @param {string} columnLetter - Буква столбца
 * @return {number} Номер последней заполненной строки
 */
function getLastFilledRow(sheet, columnLetter) {
  try {
    var range = sheet.getRange(columnLetter + '2:' + columnLetter);
    var values = range.getValues().flat();
    var lastIndex = values.findLastIndex(function(v) { return v !== ''; });
    return lastIndex >= 0 ? lastIndex + 2 : 1;
  } catch (error) {
    console.error('Ошибка в getLastFilledRow:', error);
    return 1;
  }
}

/**
 * Принудительная перезагрузка меню
 */
function forceReload() {
  try {
    onOpen({authMode: ScriptApp.AuthMode.FULL});
    SpreadsheetApp.getUi().alert('Меню успешно обновлено');
  } catch (error) {
    SpreadsheetApp.getUi().alert('Ошибка при обновлении: ' + error.message);
  }
}


/*
// Дополнительные ваши функции
function sendZayavka() {  
  const currentUser = Session.getEffectiveUser().getEmail();
  const spreadsheet = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = spreadsheet.getSheetByName("План_на_день");
  const lastRow = sheet.getLastRow() - 4;
  
  // Получаем данные один раз
  const dataRange = sheet.getRange("A2:I" + lastRow).getValues();
  
  // Подготовка данных
  const { unsettledPayments, countC, sumE } = processData(dataRange);
  const unsettledCount = unsettledPayments.length;
  
  // Форматирование данных
  const day = Utilities.formatDate(new Date(), "GMT+1", "dd.MM.yyyy");
  const formattedSum = sumE.toLocaleString('ru-RU', { 
    minimumFractionDigits: 2, 
    maximumFractionDigits: 2 
  });
  
  // Формирование сообщений
  const unsettledText = unsettledCount > 0 
    ? "Несогласованные платежи:\n" + unsettledPayments.join("\n") 
    : `Все платежи согласованы. Строк в реестре - ${countC}. Сумма всех платежей по реестру: ${formattedSum}`;
  
  const emailBody = `Реестр на ${day} согласован.
Несогласованных платежей - ${unsettledCount}, количество строк в реестре - ${countC}
Сумма всех платежей по реестру - ${formattedSum}

С уважением,
Роман Стогов
STEIT`;
  
  // Подготовка и отправка файла
  const fileBlob = getSpreadsheetAsBlob(spreadsheet, sheet, day);
  
  // Отправка письма
  sendEmail(day, emailBody, fileBlob);
  
  // Отправка в Telegram
  clientIdChat = '-867279475'
  sendText(clientIdChat, "Реестр согласован.\n" + unsettledText);
}

// Вспомогательные функции
function processData(dataRange) {
  const unsettledPayments = [];
  let countC = -4;
  let sumE = 0;

  dataRange.forEach(row => {
    const [checkbox, , org, counterparty, amount, , , , address] = row;
    
    if (checkbox === false) {
      unsettledPayments.push(`${org} | ${counterparty} | ${amount} | ${address}`);
    }
    
    if (org !== "") countC++;
    if (!isNaN(amount) && amount !== "") sumE += parseFloat(amount);
  });

  return { unsettledPayments, countC, sumE };
}

function getSpreadsheetAsBlob(spreadsheet, sheet, day) {
  const url = `https://docs.google.com/spreadsheets/d/${spreadsheet.getId()}/export?format=xlsx&gid=${sheet.getSheetId()}`;
  const params = {
    method: "GET",
    headers: { "authorization": "Bearer " + ScriptApp.getOAuthToken() }
  };
  
  return UrlFetchApp.fetch(url, params)
    .getBlob()
    .setName(`Реестр платежей план на ${day}.xlsx`);
}

function sendEmail(day, emailBody, attachment) {
  const recipients = "roman@steit.ru, v.chernyy@steit.ru, eva@steit.ru, v.chemodanova@steit.ru, skv@steit.ru, pankov@steit.ru";
  
  MailApp.sendEmail({
    to: recipients,
    subject: `Реестр платежей на ${day}`,
    body: emailBody,
    name: "Стогов Р.В.",
    attachments: [attachment]
  });}


function sendRoman() {
  try {
    const currentDate = Utilities.formatDate(new Date(), "GMT+1", "dd.MM.yyyy");
    
    // Отправка email
    sendApprovalEmail(currentDate);
    
    // Отправка уведомлений в Telegram
    sendTelegramNotification(
      CONFIG.TELEGRAM.CHATS.FIN_GROUP, 
      `Реестр на ${currentDate} отправлен на согласование Стогову Р.В.`
    );
    
    // Логирование успешной отправки
    console.log(`Реестр успешно отправлен на согласование ${currentDate}`);
  } catch (error) {
    handleError(error, 'sendRoman');
  }
}

function sendZayavka() {
  const currentUser = Session.getEffectiveUser().getEmail();
  const spreadsheet = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = spreadsheet.getSheetByName("План_на_день");
  const lastRow = sheet.getLastRow() - 4;
  
  // Получаем данные один раз
  const dataRange = sheet.getRange("A2:I" + lastRow).getValues();
  
  // Подготовка данных
  const { unsettledPayments, countC, sumE } = processData(dataRange);
  const unsettledCount = unsettledPayments.length;
  
  // Форматирование данных
  const day = Utilities.formatDate(new Date(), "GMT+1", "dd.MM.yyyy");
  const formattedSum = sumE.toLocaleString('ru-RU', { 
    minimumFractionDigits: 2, 
    maximumFractionDigits: 2 
  });
  
  // Формирование сообщений
  const unsettledText = unsettledCount > 0 
    ? "Несогласованные платежи:\n" + unsettledPayments.join("\n") 
    : `Все платежи согласованы. Строк в реестре - ${countC}. Сумма всех платежей по реестру: ${formattedSum}`;
  
  const emailBody = `Реестр на ${day} согласован.
Несогласованных платежей - ${unsettledCount}, количество строк в реестре - ${countC}
Сумма всех платежей по реестру - ${formattedSum}

С уважением,
Роман Стогов
STEIT`;
  
  // Подготовка и отправка файла
  const fileBlob = getSpreadsheetAsBlob(spreadsheet, sheet, day);
  
  // Отправка письма
  sendEmail(day, emailBody, fileBlob);
  
  // Отправка в Telegram
  clientIdChat = '-867279475'
  sendText(clientIdChat, "Реестр согласован.\n" + unsettledText);}

  function sendMorozov() {

  var day = Utilities.formatDate(new Date(), "GMT+1", "dd.MM.yyyy")

  sendText(clientIdChat1,"Оплаты СУ26 на "+ day +" отправлены Морозову, Егорову");
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
    to: "mos@steit.ru, v.chernyy@steit.ru, egorov@steit.ru, pankov@steit.ru",
    subject: "Оплаты СТЕЙТ и МЕТРО на "+day,
    htmlBody:'Добрый день, Олег Сергеевич! <br/> <br/> Оплаты в СУ26 от СТЕЙТ, МЕТРО и Проектные решения на ' + day + '<br/>' + send_to_mos + '<br/>' + amount_org + '<br/> С уважением,<br/> "" <br/> Финансовый менеджер <br/> Инвестиционно-управляющая компания STEIT <br/> Телефон: +7(812)777-77-07 (202) <br/> Мобильный: +7(999)999-99-99 <br/> Веб-сайт: www.steit.ru <br/> Санкт-Петербург,<br/>Набережная реки Карповки, д.19 лит.А',
    name: "Отдел финансового контроля",
  }
  //GmailApp.sendEmail("pankov@steit.ru","day",day);
  //Logger.log(message1);
  MailApp.sendEmail(message1);
  //sendText(clientIdChat1,message1);

 }

}*/