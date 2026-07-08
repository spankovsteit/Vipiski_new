function send_for_approval_FD() {
  
  try {
    const currentDate = Utilities.formatDate(new Date(), "GMT+1", "dd.MM.yyyy");
    
    // Отправка email
    sendApprovalEmail_fd(currentDate);

    notifyFinGroup(
      `Реестр платежей на ${currentDate} отправлен на согласование Финансовому директору.`
    );
    
    // Логирование успешной отправки
    console.log(`Реестр успешно отправлен на согласование ${currentDate}`);
  } catch (error) {
    handleError(error, 'send_for_approbal_FD');
  }
}

/**
 * Отправляет email с реестром платежей
 * @param {string} date - Форматированная дата
 */
function sendApprovalEmail_fd(date) {
  const emailTemplate = `
Добрый день!

Реестр платежей на ${date} для согласования готов.

https://docs.google.com/spreadsheets/d/115N5lK0LuHldMhjEhCDHcjegiMC_L1D-38GGv9LoUc8/edit?usp=sharing

С уважением,

Финансовый менеджер
Инвестиционно-управляющая компания STEIT
Телефон: +7(812)777-77-07 (221)
`;

  MailApp.sendEmail({
    to: CONFIG.EMAIL.RECIPIENTS_FIN,
    subject: `Реестр платежей на ${date}`,
    body: emailTemplate,
    name: "Отдел финансового контроля"
  });
}
