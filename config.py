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

# Используем директорию для временных файлов GitHub Actions
WORKSPACE = os.getenv('GITHUB_WORKSPACE', '.')
DATA_DIR = os.path.join(WORKSPACE, 'data')
os.makedirs(DATA_DIR, exist_ok=True)

# Файлы в специальной директории
HISTORY_FILE = os.path.join(DATA_DIR, "processed_pdfs.txt")
LOG_FILE = os.path.join(DATA_DIR, "bot_launches.log")