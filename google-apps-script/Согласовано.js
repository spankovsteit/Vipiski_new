function sendZayavka() {
  try {
    const spreadsheet = SpreadsheetApp.getActiveSpreadsheet();
    const sheet = spreadsheet.getSheetByName("План_на_день");
    
    if (!sheet) {
      throw new Error("Лист 'План_на_день' не найден");
    }

    // Находим последнюю заполненную строку в колонке C
    const lastRow = getLastFilledRow(sheet, 'C');
    if (lastRow < 2) {
      throw new Error("Нет данных для обработки");
    }

    // Получаем данные (учитываем, что заголовки в строке 1)
    const dataRange = sheet.getRange(2, 1, lastRow-1, 9).getValues();
    
    // Обрабатываем данные
    const unsettledPayments = [];
    let countC = 0;
    let sumE = 0;

    dataRange.forEach(row => {
      const checkbox = row[0]; // Столбец A - чекбокс
      const org = row[2];      // Столбец C - организация
      const counterparty = row[3]; // Столбец D - контрагент
      const amount = row[4];   // Столбец E - сумма
      const address = row[8];  // Столбец I - адрес
      
      // Если чекбокс не отмечен (false) - платеж не согласован
      if (checkbox === false) {
        unsettledPayments.push(`${org} | ${counterparty} | ${amount} руб. | ${address}`);
      }
      
      // Считаем заполненные строки (по организации)
      if (org && org.toString().trim() !== "") countC++;
      
      // Суммируем платежи
      if (amount && !isNaN(amount)) sumE += parseFloat(amount);
    });

    const unsettledCount = unsettledPayments.length;
    const day = Utilities.formatDate(new Date(), "GMT+1", "dd.MM.yyyy");
    const formattedSum = sumE.toLocaleString('ru-RU', { 
      minimumFractionDigits: 2, 
      maximumFractionDigits: 2 
    });

    // Формируем сообщения
    const unsettledText = unsettledCount > 0 
      ? "Несогласованные платежи:\n" + unsettledPayments.join("\n") 
      : `Все платежи согласованы. Строк в реестре - ${countC}. Сумма: ${formattedSum} руб.`;

    const emailBody = `Реестр на ${day} согласован.
Несогласованных платежей - ${unsettledCount}, строк в реестре - ${countC}
Сумма всех платежей - ${formattedSum} руб.

С уважением,
Отдел финансового контроля
STEIT`;

    // Отправляем письмо с вложением
    const fileBlob = getSpreadsheetAsBlob(spreadsheet, day);
    MailApp.sendEmail({
      to: CONFIG.EMAIL.RECIPIENTS,
      subject: `Реестр платежей на ${day} (согласован)`,
      body: emailBody,
      name: CONFIG.EMAIL.SENDER_NAME,
      attachments: [fileBlob]
    });

    notifyFinGroup(`✅ Реестр на ${day} согласован\n${unsettledText}`);

  } catch (error) {
    console.error('Ошибка в sendZayavka:', error);
    notifyBot(`⚠️ Ошибка при отправке согласованного реестра: ${error.message}`);
  }
}

function getSpreadsheetAsBlob(spreadsheet, day) {
  const sheet = spreadsheet.getSheetByName("План_на_день");
  if (!sheet) throw new Error("Лист 'План_на_день' не найден");

  const url = `https://docs.google.com/spreadsheets/d/${spreadsheet.getId()}/export?format=xlsx&gid=${sheet.getSheetId()}`;
  const params = {
    method: "GET",
    headers: { "Authorization": "Bearer " + ScriptApp.getOAuthToken() },
    muteHttpExceptions: true
  };
  
  const response = UrlFetchApp.fetch(url, params);
  if (response.getResponseCode() !== 200) {
    throw new Error(`Ошибка экспорта: ${response.getContentText()}`);
  }
  
  return response.getBlob().setName(`Реестр платежей ${day}.xlsx`);
}