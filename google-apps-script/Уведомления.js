/**
 * Telegram + Bitrix24: общий слой уведомлений.
 * Секрет вебхука — в Свойствах скрипта (BITRIX24_WEBHOOK_URL, BITRIX24_DIALOG_ID).
 */

function getBitrix24Config() {
  const props = PropertiesService.getScriptProperties();
  const fallback = (CONFIG && CONFIG.BITRIX24) || {};
  return {
    WEBHOOK_URL: props.getProperty('BITRIX24_WEBHOOK_URL') || fallback.WEBHOOK_URL || '',
    DIALOG_ID: props.getProperty('BITRIX24_DIALOG_ID') || fallback.DIALOG_ID || ''
  };
}

function isBitrix24Configured() {
  const cfg = getBitrix24Config();
  return !!(cfg.WEBHOOK_URL && cfg.DIALOG_ID);
}

/**
 * @param {string} text
 * @param {string} [dialogId]
 * @return {Object|null}
 */
function sendBitrix24Message(text, dialogId) {
  const cfg = getBitrix24Config();
  const webhook = cfg.WEBHOOK_URL;
  const chat = dialogId || cfg.DIALOG_ID;

  if (!webhook || !chat) {
    console.log('Bitrix24 не настроен — пропуск');
    return { skipped: true };
  }

  const url = webhook.replace(/\/$/, '') + '/im.message.add.json';
  const maxLen = 4000;
  const chunks = [];
  for (let i = 0; i < text.length; i += maxLen) {
    chunks.push(text.substring(i, i + maxLen));
  }

  let last = null;
  chunks.forEach(function(chunk, idx) {
    const response = UrlFetchApp.fetch(url, {
      method: 'post',
      payload: {
        DIALOG_ID: String(chat),
        MESSAGE: chunk
      },
      muteHttpExceptions: true
    });
    const data = JSON.parse(response.getContentText());
    if (data.error) {
      throw new Error('Bitrix24: ' + (data.error_description || data.error));
    }
    console.log(
      'Bitrix24 часть ' + (idx + 1) + '/' + chunks.length + ', id=' + data.result
    );
    last = data;
  });
  return last;
}

/**
 * Telegram FIN-группа + Bitrix24 (один текст).
 * @param {string} text
 * @param {Object} [opts]
 */
function notifyFinGroup(text, opts) {
  opts = opts || {};
  const errors = [];

  try {
    sendTelegramNotification(
      CONFIG.TELEGRAM.CHATS.FIN_GROUP,
      text,
      opts.keyboard
    );
  } catch (e) {
    errors.push(e.message || String(e));
  }

  try {
    sendBitrix24Message(text, opts.bitrixDialogId);
  } catch (e) {
    errors.push(e.message || String(e));
  }

  if (errors.length) {
    throw new Error('Уведомления: ' + errors.join('; '));
  }
}

/** Telegram BOT + Bitrix24 (ошибки и служебные алерты). */
function notifyBot(text) {
  const errors = [];
  try {
    sendTelegramNotification(CONFIG.TELEGRAM.CHATS.BOT, text);
  } catch (e) {
    errors.push(e.message || String(e));
  }
  try {
    sendBitrix24Message(text);
  } catch (e) {
    errors.push(e.message || String(e));
  }
  if (errors.length) {
    console.error('notifyBot:', errors.join('; '));
  }
}

/** Outbox P1: остатки в Telegram и Bitrix24. */
function notifyOutboxMessage(text) {
  const tgResult = sendTelegramMessage(text);
  const tgOk = tgResult && tgResult.ok;

  return {
    // Остатки в Bitrix24 отправляет Vipiski (Python). Здесь оставляем только Telegram,
    // чтобы не было дублей из P1-триггера.
    ok: tgOk,
    telegram: tgResult,
    bitrixOk: null,
    bitrixSkipped: true
  };
}

function testBitrix24() {
  notifyFinGroup('Тест: реестр + Bitrix24');
  SpreadsheetApp.getActiveSpreadsheet().toast('Отправлено в Telegram и Bitrix24', 'Тест', 3);
}
