BOT_TOKEN = "8915818050:AAFDUXJRYibcmIYBhyorTPBSdcT_dkJ86MI"
CHAT_ID = "5877409438"

from curl_cffi import requests
import time


def get_vacancies(keyword):
    url = "https://api.hh.ru/vacancies"
    params = {"text": keyword, "per_page": 5}
    response = requests.get(url, params=params, impersonate="chrome110")
    response.raise_for_status()
    return response.json().get("items", [])


def format_salary(salary):
    if salary is None:
        return "не указана"
    parts = []
    if salary.get("from"):
        parts.append(f"от {salary['from']}")
    if salary.get("to"):
        parts.append(f"до {salary['to']}")
    currency = salary.get("currency", "")
    if parts:
        return " ".join(parts) + (f" {currency}" if currency else "")
    return "не указана"


def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}
    response = requests.post(url, json=payload)
    response.raise_for_status()


def main():
    keyword = input("Введите ключевое слово для поиска вакансий: ")

    vacancies = get_vacancies(keyword)

    if not vacancies:
        print("Вакансии не найдены.")
        return

    send_telegram_message(f"🔍 Вакансии по запросу: {keyword}")
    time.sleep(1)

    for vacancy in vacancies:
        name = vacancy.get("name", "Без названия")
        company = vacancy.get("employer", {}).get("name", "Не указана")
        salary = format_salary(vacancy.get("salary"))
        link = vacancy.get("alternate_url", "")

        message = (
            f"💼 {name}\n"
            f"🏢 {company}\n"
            f"💰 {salary}\n"
            f"🔗 {link}"
        )

        send_telegram_message(message)
        print(f"Отправлено: {name}")
        time.sleep(1)

    print("Все вакансии отправлены!")


if __name__ == "__main__":
    main()
