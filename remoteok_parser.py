BOT_TOKEN = "8915818050:AAFDUXJRYibcmIYBhyorTPBSdcT_dkJ86MI"
CHAT_ID = "5877409438"

from curl_cffi import requests
import time


def get_vacancies(keyword):
    url = f"https://remoteok.com/api?tag={keyword}"
    response = requests.get(url, impersonate="chrome110")
    response.raise_for_status()
    data = response.json()
    # First element is metadata, skip it
    return data[1:6] if len(data) > 1 else []


def format_salary(vacancy):
    salary_min = vacancy.get("salary_min")
    salary_max = vacancy.get("salary_max")
    if salary_min and salary_max:
        return f"{salary_min} - {salary_max}"
    elif salary_min:
        return f"from {salary_min}"
    elif salary_max:
        return f"up to {salary_max}"
    return "not specified"


def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}
    response = requests.post(url, json=payload)
    response.raise_for_status()


def main():
    keyword = input("Enter keyword to search jobs: ")

    vacancies = get_vacancies(keyword)

    if not vacancies:
        print("No jobs found.")
        return

    send_telegram_message(f"🔍 Jobs for: {keyword}")
    time.sleep(1)

    for vacancy in vacancies:
        position = vacancy.get("position", "Unknown")
        company = vacancy.get("company", "Unknown")
        salary = format_salary(vacancy)
        link = vacancy.get("url", "")

        message = (
            f"💼 {position}\n"
            f"🏢 {company}\n"
            f"💰 {salary}\n"
            f"🔗 {link}"
        )

        send_telegram_message(message)
        print(f"Sent: {position}")
        time.sleep(1)

    print("All jobs sent!")


if __name__ == "__main__":
    main()
