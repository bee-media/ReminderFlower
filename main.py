import random
import logging
import os
import time  # Для работы с реальным временем
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
import asyncio

# Настраиваем логирование для записи в файл
log_file_path = os.path.join(os.path.dirname(__file__), 'bot.log')
logging.basicConfig(
    filename=log_file_path,  # Путь к файлу для записи логов
    filemode='a',  # Режим добавления (append) в файл
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO  # Устанавливаем уровень логирования на INFO
)

logger = logging.getLogger(__name__)

# Telegram ID администраторов (необходимо заменить на реальные ID)
ADMIN_1_ID = ID_TG
ADMIN_2_ID = ID_TG
TOKEN_Telega = "TOKEN"
Random_day_A = 1
Random_day_B = 1

# Инициализация глобальных переменных
watering_in_progress = False
last_watering_time = time.time()  # Устанавливаем текущее время как время последнего полива
days_until_next_reminder = random.randint(Random_day_A, Random_day_B)
reminder_sent_time = None  # Время отправки последнего напоминания

NIGHT_START_HOUR = 22  # Начало ночного времени (22:00)
NIGHT_END_HOUR = 6     # Конец ночного времени (06:00)

async def send_watering_reminder(application):
    global watering_in_progress, last_watering_time, days_until_next_reminder, reminder_sent_time

    while True:
        try:
            now = time.time()
            current_hour = time.localtime(now).tm_hour
            
            if watering_in_progress:
                # Проверяем, прошло ли 24 часа с момента отправки напоминания
                if now - reminder_sent_time >= 24 * 3600:  # 24 часа
                    watering_in_progress = False
                    logger.info("Никто не ответил на напоминание. Отправляем повторное напоминание.")
            else:
                # Проверяем, пора ли отправлять напоминание
                if now - last_watering_time >= days_until_next_reminder * 24 * 3600:
                    # Если время отправки попадает в ночное время, планируем на утро
                    if current_hour >= NIGHT_START_HOUR or current_hour < NIGHT_END_HOUR:
                        # Переносим на утро следующего дня
                        logger.info("Попытка отправки напоминания в ночное время. Запланируем на утро.")
                        # Запланируем уведомление на 6:00 следующего дня
                        next_notification_time = time.mktime(time.localtime(now)) + ((24 - current_hour + NIGHT_END_HOUR) % 24) * 3600
                        await asyncio.sleep(next_notification_time - now)
                    else:
                        # Отправляем напоминание администраторам
                        keyboard = [[InlineKeyboardButton("Я полью", callback_data='i_will_water')]]
                        reply_markup = InlineKeyboardMarkup(keyboard)
                        await application.bot.send_message(chat_id=ADMIN_1_ID, text="Пора полить цветы!", reply_markup=reply_markup)
                        await application.bot.send_message(chat_id=ADMIN_2_ID, text="Пора полить цветы!", reply_markup=reply_markup)

                        watering_in_progress = True
                        reminder_sent_time = now  # Запоминаем время отправки напоминания
                        logger.info("Напоминание отправлено администраторам.")
            await asyncio.sleep(3600)  # Проверяем каждую час
        except Exception as e:
            logger.error(f"Ошибка в процессе напоминания о поливе: {e}")

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global watering_in_progress, last_watering_time, days_until_next_reminder

    try:
        query = update.callback_query
        await query.answer()

        user_id = query.from_user.id
        other_admin_id = ADMIN_1_ID if user_id == ADMIN_2_ID else ADMIN_2_ID

        await context.bot.send_message(chat_id=other_admin_id, text=f"{query.from_user.first_name} взял на себя полив цветов.")

        watering_in_progress = False
        last_watering_time = time.time()  # Обновляем время последнего полива
        days_until_next_reminder = random.randint(Random_day_A, Random_day_B)
        logger.info(f"Полив выполнен. Следующее напоминание через {days_until_next_reminder} дней.")

        await query.edit_message_text(text="Спасибо за то, что полили цветы!")
    except Exception as e:
        logger.error(f"Ошибка при обработке нажатия кнопки: {e}")

async def shed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        keyboard = [[InlineKeyboardButton("Я полью", callback_data='i_will_water')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Пора полить цветы!", reply_markup=reply_markup)
    except Exception as e:
        logger.error(f"Ошибка в команде /shed: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.message.reply_text('Привет! Я бот для напоминания о поливе цветов.')
    except Exception as e:
        logger.error(f"Ошибка в команде /start: {e}")

async def check_days(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global last_watering_time, days_until_next_reminder

    try:
        now = time.time()
        elapsed_time = now - last_watering_time
        remaining_seconds = days_until_next_reminder * 24 * 3600 - elapsed_time

        if remaining_seconds > 0:
            remaining_days = int(remaining_seconds // (24 * 3600))
            remaining_hours = int((remaining_seconds % (24 * 3600)) // 3600)
            remaining_minutes = int((remaining_seconds % 3600) // 60)

            logger.info(
                f"Осталось {remaining_days} дней, {remaining_hours} часов и {remaining_minutes} минут до следующего напоминания.")

            await update.message.reply_text(
                f"До следующего напоминания осталось {remaining_days} дней, {remaining_hours} часов и {remaining_minutes} минут."
            )
        else:
            await update.message.reply_text("Напоминание о поливе должно прийти сегодня!")
    except Exception as e:
        logger.error(f"Ошибка в команде /check_days: {e}")

async def main():
    try:
        application = ApplicationBuilder().token(TOKEN_Telega).build()
        await application.initialize()

        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("shed", shed))
        application.add_handler(CommandHandler("check_days", check_days))
        application.add_handler(CallbackQueryHandler(button_click))

        # Запускаем отправку напоминаний о поливе в фоне
        asyncio.create_task(send_watering_reminder(application))

        await application.start()
        await application.updater.start_polling()

        try:
            while True:
                await asyncio.sleep(3600)
        except KeyboardInterrupt:
            await application.stop()
    except Exception as e:
        logger.critical(f"Критическая ошибка в основной функции: {e}")

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except Exception as e:
        logger.critical(f"Ошибка при запуске бота: {e}")
