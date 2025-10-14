import os
import requests
from bs4 import BeautifulSoup
import pdfplumber
import io
import re
import json
import csv
from datetime import datetime
from telegram import Bot

# === НАСТРОЙКИ ===
TELEGRAM_TOKEN = os.getenv(TELEGRAM_TOKEN)
CHAT_IDS = [int(x) for x in os.getenv(CHAT_IDS, ).split(,) if x.strip()]
TARGET_PLACES = [глазов, завьялово, молдаванка]

PAGE_URL = httpselsetudm.ruconsumersplanovye-otklyucheniya-elektroenergii
CHECKED_FILE = checked_files.json
HISTORY_FILE = history.csv

bot = Bot(token=TELEGRAM_TOKEN)


def load_checked()
    if not os.path.exists(CHECKED_FILE)
        return []
    try
        with open(CHECKED_FILE, r, encoding=utf-8) as f
            return json.load(f)
    except Exception
        return []


def save_checked(urls)
    with open(CHECKED_FILE, w, encoding=utf-8) as f
        json.dump(urls, f, ensure_ascii=False, indent=2)


def append_history(date, place, match_text, pdf_url)
    Добавляет запись в историю.
    file_exists = os.path.exists(HISTORY_FILE)
    with open(HISTORY_FILE, a, encoding=utf-8, newline=) as f
        writer = csv.writer(f, delimiter=;)
        if not file_exists
            writer.writerow([date, place, text, pdf_url])
        writer.writerow([date, place, match_text, pdf_url])


def get_all_pdf_urls()
    r = requests.get(PAGE_URL, timeout=20)
    soup = BeautifulSoup(r.text, html.parser)
    links = soup.find_all(a, href=re.compile(r.pdf$))
    pdf_urls = []
    for link in links
        href = link[href]
        if href.startswith(http)
            pdf_urls.append(href)
        else
            pdf_urls.append(httpselsetudm.ru + href)
    return list(set(pdf_urls))


def get_text_from_pdf(pdf_content)
    with pdfplumber.open(io.BytesIO(pdf_content)) as pdf
        text = n.join(page.extract_text() or  for page in pdf.pages)
    return text.lower()


def main()
    checked_urls = load_checked()
    pdf_urls = get_all_pdf_urls()
    new_files_found = False

    for pdf_url in pdf_urls
        if pdf_url in checked_urls
            print(fПропускаем уже обработанный файл {pdf_url})
            continue

        print(fПроверяем новый файл {pdf_url})
        response = requests.get(pdf_url)
        pdf_content = response.content
        text = get_text_from_pdf(pdf_content)
        lines = text.splitlines()
        found_places = []

        for place in TARGET_PLACES
            matches = [line.strip() for line in lines if place in line]
            if matches
                found_places.append((place, matches))

        if found_places
            new_files_found = True
            for place, matches in found_places
                message = (
                    f Найдено упоминание '{place.title()}' в новом файле отключений 
                    f({datetime.now()%d.%m.%Y})nn
                    + n.join(matches[10])
                    + fnn📄 {pdf_url}
                )

                for chat_id in CHAT_IDS
                    bot.send_message(chat_id=chat_id, text=message)
                    bot.send_document(chat_id=chat_id, document=io.BytesIO(pdf_content), filename=otklyucheniya.pdf)

                for match in matches
                    append_history(datetime.now().strftime(%Y-%m-%d %H%M), place, match, pdf_url)

                print(f✅ Сообщение и запись в историю по '{place}' добавлены.)
        else
            print(f'{pdf_url}' — нет совпадений.)

        checked_urls.append(pdf_url)

    save_checked(checked_urls)

    if not new_files_found
        print(Новых отключений для заданных населённых пунктов не найдено.)


if __name__ == __main__
    main()

