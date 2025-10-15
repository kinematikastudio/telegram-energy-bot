# config.py
# Настройки бота
import os

# Токен бота от @BotFather
TELEGRAM_BOT_TOKEN = "8071837552:AAFE3OIukWMIj0CGZLtBftR2XwEVJp6Fm2I"

# ID чата/канала (можно получить через @userinfobot)
TELEGRAM_CHAT_ID = "-4927608858"

# Населенный пункт для поиска (например: "с. Заречное", "д. Лесная")
#TARGET_CITY = "Кез, Балезино"
TARGET_CITIES = ["Июльское", "Вавож", "Люга"] 

# Отладочный режим (True/False)
DEBUG = False  # В режиме True сообщения отправляются всегда


# Настройки форматирования
MESSAGE_SETTINGS = {
    'use_emoji': True,  # Использовать эмодзи
    'separator': '─' * 40,  # Разделитель между записями
}

# В GitHub Actions не используем файлы для хранения состояния
USE_FILE_STORAGE = os.getenv('GITHUB_ACTIONS') is None

# Файлы только для локального использования
if USE_FILE_STORAGE:
    HISTORY_FILE = "processed_pdfs.txt"
    LOG_FILE = "bot_launches.log"
else:
    HISTORY_FILE = None
    LOG_FILE = None