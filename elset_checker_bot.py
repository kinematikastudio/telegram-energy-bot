import requests
import pdfplumber
import io
import re
import os
import datetime
from urllib.parse import urljoin
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, TARGET_CITIES, MESSAGE_SETTINGS, DEBUG, HISTORY_FILE


LOG_FILE = "bot_launches.log"

def log_launch():
    """Запись лога запуска в файл"""
    try:
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{current_time}] Бот запущен\n"
        
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(log_message)
        
        print(f"Лог запуска записан: {current_time}")
    except Exception as e:
        print(f"Ошибка записи лога: {e}")

def send_telegram_message(message):
    """Отправка сообщения в Telegram"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message,
        'parse_mode': 'HTML'
    }
    try:
        response = requests.post(url, data=payload)
        return response.json()
    except Exception as e:
        print(f"Ошибка отправки в Telegram: {e}")

def is_pdf_processed(pdf_url):
    """Проверяем, обрабатывался ли уже этот PDF файл"""
    if not os.path.exists(HISTORY_FILE):
        return False
    
    try:
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            processed_files = f.read().splitlines()
        return pdf_url in processed_files
    except Exception as e:
        print(f"Ошибка чтения файла истории: {e}")
        return False

def mark_pdf_processed(pdf_url):
    """Добавляем PDF файл в список обработанных"""
    try:
        with open(HISTORY_FILE, 'a', encoding='utf-8') as f:
            f.write(pdf_url + '\n')
        print(f"Файл {pdf_url} добавлен в историю")
    except Exception as e:
        print(f"Ошибка записи в файл истории: {e}")

def format_outage_message(entry):
    """Форматирование одной записи об отключении"""
    city = entry.get('city', 'Не указан')
    date_off = entry.get('date_off', 'Не указана')
    time_off = entry.get('time_off', 'Не указано')
    time_on = entry.get('time_on', 'Не указано')
    streets = entry.get('streets', 'Улицы не указаны')
    
    if MESSAGE_SETTINGS['use_emoji']:
        message = (
            f"{city}\n"
            f"<b>📅 Дата:</b> {date_off}\n"
            f"<b>⏰ Время:</b> {time_off}-{time_on}\n"
            f"\n"
            f"🏙️ {streets}"
        )
    else:
        message = (
            f"{city}\n"
            f"<b>Дата:</b> {date_off}\n"
            f"<b>Время:</b> {time_off}-{time_on}\n"
            f"\n"
            f"{streets}"
        )
    
    return message

def create_telegram_message(results, pdf_url, is_debug=False, is_duplicate=False):
    """Создание форматированного сообщения для Telegram"""
    if not results:
        return []

    separator = MESSAGE_SETTINGS['separator']
    
    if MESSAGE_SETTINGS['use_emoji']:
        header = f"⚡ <b>График отключений электроэнергии</b> ⚡\n"
        header += f"🏘️ <b>Искомые населенные пункты:</b> {', '.join(TARGET_CITIES)}\n"
        header += f"📊 <b>Найдено записей:</b> {len(results)}\n"
        header += f"🔗 <a href='{pdf_url}'>Ссылка на файл</a>\n"
        if is_duplicate:
            header += f"🔄 <b>Повторная обработка</b> (файл уже был обработан)\n"
        if is_debug:
            header += f"🔧 <b>ОТЛАДОЧНЫЙ РЕЖИМ</b>\n"
        header += f"\n{separator}\n\n"
    else:
        header = f"<b>График отключений электроэнергии</b>\n"
        header += f"<b>Искомые населенные пункты:</b> {', '.join(TARGET_CITIES)}\n"
        header += f"<b>Найдено записей:</b> {len(results)}\n"
        header += f"<a href='{pdf_url}'>Ссылка на файл</a>\n"
        if is_duplicate:
            header += f"<b>Повторная обработка</b> (файл уже был обработан)\n"
        if is_debug:
            header += f"<b>ОТЛАДОЧНЫЙ РЕЖИМ</b>\n"
        header += f"\n{separator}\n\n"
    
    messages = []
    current_message = header
    
    for i, entry in enumerate(results, 1):
        entry_text = format_outage_message(entry)
        
        # Если добавляем разделитель (кроме последней записи)
        if i < len(results):
            entry_text += f"\n{separator}\n\n"
        
        # Проверяем, не превысит ли сообщение лимит Telegram (4096 символов)
        if len(current_message + entry_text) > 4000:
            messages.append(current_message)
            current_message = entry_text
        else:
            current_message += entry_text
    
    if current_message:
        messages.append(current_message)
    
    return messages

def parse_pdf_content(pdf_content):
    """Парсинг содержимого PDF и поиск нужных строк"""
    results = []
    
    with pdfplumber.open(io.BytesIO(pdf_content)) as pdf:
        for page in pdf.pages:
            # Пытаемся извлечь таблицу
            tables = page.extract_tables()
            
            for table in tables:
                if table:
                    for row in table:
                        # Пропускаем пустые строки и заголовки
                        if not row or not row[0] or not str(row[0]).strip().isdigit():
                            continue
                            
                        # Проверяем наличие нужных городов во втором столбце
                        if len(row) > 1 and row[1]:
                            city_name = str(row[1]).strip()
                            # Проверяем, содержится ли любой из искомых городов в названии
                            for target_city in TARGET_CITIES:
                                if target_city in city_name:
                                    # Извлекаем данные из столбцов
                                    try:
                                        city = str(row[1]).strip() if row[1] else city_name
                                        streets = str(row[2]).strip() if row[2] and len(row) > 2 else "улицы не указаны"
                                        date_off = str(row[3]).strip() if row[3] and len(row) > 3 else "дата не указана"
                                        time_off = str(row[4]).strip() if row[4] and len(row) > 4 else "время не указано"
                                        time_on = str(row[6]).strip() if row[6] and len(row) > 6 else "время не указано"
                                        
                                        # Форматируем результат в виде словаря
                                        result = {
                                            'city': city,
                                            'date_off': date_off,
                                            'time_off': time_off,
                                            'time_on': time_on,
                                            'streets': streets
                                        }
                                        results.append(result)
                                        print(f"Найдена запись: {city}, {date_off}, {time_off}-{time_on}, {streets}")
                                        break  # Прерываем после первого совпадения
                                        
                                    except Exception as e:
                                        print(f"Ошибка обработки строки: {e}")
                                        continue
    
    return results

def process_pdf_file(pdf_url):
    """Обработка одного PDF файла"""
    try:
        print(f"Обрабатываем PDF: {pdf_url}")
        
        # Проверяем, обрабатывался ли уже этот файл
        is_duplicate = is_pdf_processed(pdf_url)
        
        # Если файл уже обрабатывался и не в режиме отладки - пропускаем
        if is_duplicate and not DEBUG:
            print(f"Файл {pdf_url} уже был обработан ранее. Пропускаем.")
            return True
        
        # Загрузка PDF
        pdf_response = requests.get(pdf_url, timeout=30)
        pdf_response.raise_for_status()

        # Парсинг PDF
        results = parse_pdf_content(pdf_response.content)

        # Отправка результатов в Telegram только если есть записи
        if results:
            # Создаем форматированные сообщения
            messages = create_telegram_message(results, pdf_url, is_debug=DEBUG, is_duplicate=is_duplicate)
            
            for message in messages:
                send_telegram_message(message)
            print(f"Отправлено {len(messages)} сообщений в Telegram для файла {pdf_url}")
            
            # Помечаем файл как обработанный (только если не дубликат в режиме отладки)
            if not is_duplicate:
                mark_pdf_processed(pdf_url)
        else:
            # Если записей не найдено, выводим только в консоль
            print(f"Для населенных пунктов {TARGET_CITIES} отключений не найдено в файле {pdf_url}")
            
            # Помечаем файл как обработанный (только если не дубликат в режиме отладки)
            if not is_duplicate:
                mark_pdf_processed(pdf_url)
                
        return True
        
    except requests.RequestException as e:
        error_msg = f"❌ Ошибка сети при обработке {pdf_url}: {str(e)}"
        print(error_msg)
        if DEBUG:
            send_telegram_message(error_msg + "\n🔧 <b>ОТЛАДОЧНЫЙ РЕЖИМ</b>")
        return False
    except Exception as e:
        error_msg = f"❌ Ошибка при обработке {pdf_url}: {str(e)}"
        print(error_msg)
        if DEBUG:
            send_telegram_message(error_msg + "\n🔧 <b>ОТЛАДОЧНЫЙ РЕЖИМ</b>")
        return False

def main():
    # Логируем запуск
    log_launch()
    try:
        print("Начинаем обработку...")
        print(f"Ищем отключения для населенных пунктов: {', '.join(TARGET_CITIES)}")
        
        # Загрузка страницы
        url = "https://elsetudm.ru/consumers/planovye-otklyucheniya-elektroenergii/"
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        # Поиск всех PDF ссылок в HTML
        pdf_links = re.findall(r'href="([^"]*\.pdf[^"]*)"', response.text, re.IGNORECASE)
        if not pdf_links:
            print("PDF файлы не найдены на странице")
            return

        print(f"Найдено {len(pdf_links)} PDF файлов на странице")
        
        # Обрабатываем каждый PDF файл
        processed_count = 0
        for pdf_link in pdf_links:
            # Формируем полный URL
            if not pdf_link.startswith('http'):
                pdf_url = urljoin(url, pdf_link)
            else:
                pdf_url = pdf_link
                
            # Обрабатываем файл
            if process_pdf_file(pdf_url):
                processed_count += 1
        
        print(f"Обработка завершена. Успешно обработано {processed_count} из {len(pdf_links)} файлов")
        
        # Если в отладочном режиме все файлы уже были обработаны, выводим только в консоль
        if DEBUG and processed_count == 0 and len(pdf_links) > 0:
            print("Все файлы уже были обработаны ранее (отладочный режим)")

    except requests.RequestException as e:
        error_msg = f"❌ Ошибка сети при загрузке страницы: {str(e)}"
        print(error_msg)
    except Exception as e:
        error_msg = f"❌ Произошла ошибка: {str(e)}"
        print(error_msg)

if __name__ == "__main__":
    main()