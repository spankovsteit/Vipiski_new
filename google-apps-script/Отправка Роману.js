// Конфигурационные константы
const CONFIG = {
  TELEGRAM: {
    TOKEN: '5617912411:AAFaAFs0NcEOZR5iJwsEOO7iVrRPFFKzFh8',
    CHATS: {
      BOT: '1824722729',     // Бот SteitVipiska
      FIN_GROUP: '-1003124598066' // Группа STEIT FIN
    }
  },
  BITRIX24: {
    DIALOG_ID: 'chat5294' // чат «Остатки»; URL — в Свойствах скрипта
  },
  EMAIL: {
    RECIPIENTS: "pankov@steit.ru, roman@steit.ru, v.solncev@steit.ru, v.chemodanova@steit.ru, yu.duhnenko@steit.ru",
    RECIPIENTS_FIN: "pankov@steit.ru, v.solncev@steit.ru, v.chemodanova@steit.ru",
    RECIPIENTS_BUH: "pankov@steit.ru, v.chemodanova@steit.ru, yu.duhnenko@steit.ru", // Получатели через запятую
    SENDER_NAME: "Отдел финансового контроля"
  },
  SPREADSHEET_URL: "https://docs.google.com/spreadsheets/d/115N5lK0LuHldMhjEhCDHcjegiMC_L1D-38GGv9LoUc8/edit?usp=sharing"
};

/**
 * Отправляет реестр платежей на согласование
 */
function sendRoman() {
  try {
    const currentDate = Utilities.formatDate(new Date(), "GMT+1", "dd.MM.yyyy");
    
    // Отправка email
    sendApprovalEmail_r(currentDate);
    
    notifyFinGroup(
      `Реестр на ${currentDate} отправлен на согласование Стогову Р.В.`
    );
    
    // Логирование успешной отправки
    console.log(`Реестр успешно отправлен на согласование ${currentDate}`);
  } catch (error) {
    handleError(error, 'sendRoman');
  }
}

/**
 * Отправляет email с реестром платежей
 * @param {string} date - Форматированная дата
 */
function sendApprovalEmail_r(date) {
  const emailTemplate = `
Добрый день, Роман Владимирович!

Реестр платежей на ${date} для согласования готов.

${CONFIG.SPREADSHEET_URL}

С уважением,

Финансовый менеджер
Инвестиционно-управляющая компания STEIT
Телефон: +7(812)777-77-07 (221)
`;

  MailApp.sendEmail({
    to: CONFIG.EMAIL.RECIPIENTS,
    subject: `Реестр платежей на ${date}`,
    body: emailTemplate,
    name: CONFIG.EMAIL.SENDER_NAME
  });
}

/**
 * Отправляет сообщение в Telegram
 * @param {string} chatId - ID чата
 * @param {string} text - Текст сообщения
 * @param {Object} [keyboard] - Клавиатура (опционально)
 */
function sendTelegramNotification(chatId, text, keyboard) {
  const payload = {
    chat_id: String(chatId),
    text: text,
    parse_mode: 'HTML'
  };

  if (keyboard) {
    payload.reply_markup = JSON.stringify(keyboard);
  }

  const options = {
    method: 'post',
    payload: payload,
    muteHttpExceptions: true
  };

  const response = UrlFetchApp.fetch(
    `https://api.telegram.org/bot${CONFIG.TELEGRAM.TOKEN}/sendMessage`, 
    options
  );

  const responseData = JSON.parse(response.getContentText());
  if (!responseData.ok) {
    throw new Error(`Telegram API error: ${responseData.description}`);
  }

  return responseData;
}

/**
 * Обрабатывает ошибки
 * @param {Error} error - Объект ошибки
 * @param {string} functionName - Название функции где произошла ошибка
 */
function handleError(error, functionName) {
  console.error(`Ошибка в функции ${functionName}:`, error);
  
  notifyBot(`⚠️ Ошибка при отправке реестра (${functionName}): ${error.message}`);
}

// Функция отправки сообщения в Telegram
function sendTelegramMessage(message) {
  const token = CONFIG.TELEGRAM.TOKEN;
  const chatId = CONFIG.TELEGRAM.CHATS.FIN_GROUP;
  
  const url = `https://api.telegram.org/bot${token}/sendMessage`;
  
  const payload = {
    method: 'post',
    contentType: 'application/json',
    payload: JSON.stringify({
      chat_id: chatId,
      text: message,
      parse_mode: 'HTML'
    })
  };
  
  try {
    const response = UrlFetchApp.fetch(url, payload);
    return JSON.parse(response.getContentText());
  } catch (error) {
    console.error('Ошибка при отправке сообщения в Telegram:', error);
    return null;
  }
}

// Функция очистки ячейки P1 на листе Account_balances
function clearCellP1() {
  try {
    const spreadsheet = SpreadsheetApp.getActiveSpreadsheet();
    const sheet = spreadsheet.getSheetByName('Account_balances');
    if (sheet) {
      sheet.getRange('P1').clearContent();
      console.log('Ячейка P1 очищена');
    } else {
      console.error('Лист "Account_balances" не найден');
    }
  } catch (error) {
    console.error('Ошибка при очистке ячейки P1:', error);
  }
}

// Функция для проверки ячейки P1 (вызывается по расписанию)
function checkAndSendMessage() {
  try {
    const spreadsheet = SpreadsheetApp.getActiveSpreadsheet();
    const sheet = spreadsheet.getSheetByName('Account_balances');
    
    if (!sheet) {
      console.error('Лист "Account_balances" не найден');
      return;
    }
    
    // Получаем значение ячейки P1
    const cellValue = sheet.getRange('P1').getValue();
    
    // Важно: проверяем, что cellValue - это строка, а не объект события
    if (cellValue && typeof cellValue === 'string' && cellValue.toString().trim() !== '') {
      const message = cellValue.toString().trim();
      
      // Проверяем, что это не JSON от триггера (не содержит timezone и т.д.)
      if (message.includes('timezone') || message.includes('triggerUid')) {
        console.log('Обнаружены метаданные триггера, пропускаем отправку');
        return;
      }
      
      console.log('Обнаружено сообщение для отправки:', message);
      
      const result = notifyOutboxMessage(message);

      if (result.ok) {
        clearCellP1();
        console.log('Сообщение отправлено (Telegram + Bitrix24), ячейка P1 очищена');
      } else {
        console.error('Не удалось отправить сообщение. Результат:', result);
      }
    } else {
      console.log('Ячейка P1 пуста или содержит нестроковое значение');
    }
  } catch (error) {
    console.error('Ошибка в checkAndSendMessage:', error);
  }
}

// Функция для ручного тестирования
function testCheckAndSend() {
  checkAndSendMessage();
  SpreadsheetApp.getActiveSpreadsheet().toast('Проверка выполнена', 'Готово', 3);
}