/**
 * Основная функция для отправки реестра в бухгалтерию
 */
function sendBuh() {
  try {
    const currentDate = Utilities.formatDate(new Date(), "GMT+1", "dd.MM.yyyy");
    const spreadsheet = SpreadsheetApp.getActiveSpreadsheet();
    const sheet = spreadsheet.getSheetByName("Регулярные");

    if (!sheet) {
      throw new Error("Лист 'Регулярные' не найден");
    }

    // Находим последнюю заполненную строку (минус заголовок)
    const lastRow = getLastFilledRow(sheet, 'C');
    if (lastRow < 2) {
      throw new Error("Нет данных для обработки");
    }

    // Получаем данные из таблицы
    const dataRange = sheet.getRange("A2:I" + lastRow).getValues();
    const { countC, sumE } = processData(dataRange);

    // Форматируем сумму с разделителями тысяч и 2 знаками после запятой
    const formattedSum = sumE.toLocaleString('ru-RU', { 
      minimumFractionDigits: 2, 
      maximumFractionDigits: 2 
    });

    // Отправляем email
    sendApprovalEmail2(currentDate, countC, formattedSum);

    notifyFinGroup(
      `Реестр регулярных платежей на ${currentDate} отправлен в бухгалтерию. Строк в реестре: ${countC}, сумма: ${formattedSum} руб.`
    );
    
    // Логируем успешную отправку
    console.log(`Реестр успешно отправлен ${currentDate}`);
  } catch (error) {
    handleError(error, 'sendBuh');
  }
}

/**
 * Обрабатывает данные из таблицы
 */
function processData(dataRange) {
  
  let countC = 0; // Счетчик строк
  let sumE = 0;   // Общая сумма

  dataRange.forEach(row => {
    const [checkbox, , org, counterparty, amount, , , , address] = row;
    // Считаем заполненные строки и суммируем платежи
    if (org && org.toString().trim() !== "") countC++;
    if (amount && !isNaN(amount)) sumE += parseFloat(amount);
  });

  return { countC, sumE };
}

/**
 * Отправляет email с реестром
 */
function sendApprovalEmail2(date, countC, formattedSum) {
  const emailTemplate = `
Добрый день!

Реестр регулярных платежей на ${date} готов. 
Количество строк: ${countC} 
Общая сумма: ${formattedSum} руб.

Ссылка на таблицу:
${CONFIG.SPREADSHEET_URL}

С уважением,
Финансовый менеджер
Инвестиционно-управляющая компания STEIT
Телефон: +7(812)777-77-07 (221)
`;

  MailApp.sendEmail({
    to: CONFIG.EMAIL.RECIPIENTS_BUH,
    subject: `Реестр регулярных платежей на ${date}`,
    body: emailTemplate,
    name: CONFIG.EMAIL.SENDER_NAME
  });
}

/**
 * Находит последнюю заполненную строку в колонке
 */
function getLastFilledRow(sheet, column) {
  const lastRow = sheet.getLastRow();
  const range = sheet.getRange(column + "1:" + column + lastRow);
  const values = range.getValues();
  
  for (let i = values.length - 1; i >= 0; i--) {
    if (values[i][0] !== "") {
      return i + 1;
    }
  }
  
  return 0;
}
