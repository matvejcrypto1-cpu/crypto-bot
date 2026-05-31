import requests
from bs4 import BeautifulSoup
import time
import json
import re
import random
from fake_useragent import UserAgent

BOT_TOKEN = "8915818050:AAFDUXJRYibcmIYBhyorTPBSdcT_dkJ86MI"
CHAT_ID = "5877409438"

ua = UserAgent()

def create_session():
    """Create a requests session with realistic browser headers."""
    session = requests.Session()
    session.headers.update({
        "User-Agent": ua.random,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "ru-RU,ru;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Referer": "https://kwork.ru/",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-User": "?1",
    })
    return session

def is_blocked(response_text):
    """Check if Kwork returned a block/captcha page."""
    return "заблокирован" in response_text or "captcha" in response_text.lower()

def safe_request(session, url, max_retries=3):
    """Make a request with retry logic on block detection."""
    for attempt in range(1, max_retries + 1):
        session.headers["User-Agent"] = ua.random
        try:
            response = session.get(url, timeout=15)
            if not is_blocked(response.text):
                print(f"  [OK] Запрос успешен (попытка {attempt})")
                return response
            else:
                wait = 30 * attempt + random.uniform(5, 15)
                print(f"  [!] Блокировка обнаружена (попытка {attempt}/{max_retries}), ждем {wait:.0f} сек...")
                if attempt < max_retries:
                    time.sleep(wait)
                    # Create a fresh session with new User-Agent and cookies
                    session.cookies.clear()
                    session.headers["User-Agent"] = ua.random
        except requests.exceptions.RequestException as e:
            print(f"  [X] Ошибка запроса (попытка {attempt}): {e}")
            if attempt < max_retries:
                time.sleep(10)
    return response  # Return last response even if blocked

def send_telegram(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"})

def extract_projects(soup_obj):
    """Extract project data from window.stateData JSON in the page."""
    state_data = None
    for script in soup_obj.find_all("script"):
        if "window.stateData" in script.text:
            match = re.search(r'window\.stateData\s*=\s*(\{.*?\});\s*(?:window|\Z)', script.text, re.DOTALL)
            if match:
                try:
                    state_data = json.loads(match.group(1))
                except:
                    pass
                break
    if state_data:
        wants = state_data.get("wantsListData", {}).get("wants", [])
        if not wants:
            wants = state_data.get("wants", [])
        return wants
    return []

def parse_kwork(keyword):
    session = create_session()

    # Visit the main page first to get cookies (like a real browser would)
    print(f"[*] Заходим на главную kwork.ru...")
    session.get("https://kwork.ru/", timeout=15)
    time.sleep(random.uniform(2, 5))

    # Try searching with category c=41 first
    url = f"https://kwork.ru/projects?c=41&keyword={keyword}"
    print(f"[*] Поиск в категории c=41: {keyword}")
    response = safe_request(session, url)

    # Save the HTML page for debugging as requested
    with open("C:/code/debug.html", "w", encoding="utf-8") as f:
        f.write(response.text)

    if is_blocked(response.text):
        print("[X] IP заблокирован. Попробуйте позже или используйте VPN.")
        send_telegram(f"❌ IP заблокирован Kwork. Попробуйте позже или смените IP.")
        return

    soup = BeautifulSoup(response.text, "html.parser")
    projects = extract_projects(soup)
    print(f"  Найдено в категории c=41: {len(projects)}")

    # If no projects found in category c=41, try searching without category
    if not projects:
        time.sleep(random.uniform(2, 5))

        url_fallback = f"https://kwork.ru/projects?keyword={keyword}"
        print(f"[*] Поиск без категории: {keyword}")
        response_fallback = safe_request(session, url_fallback)

        if not is_blocked(response_fallback.text):
            soup_fallback = BeautifulSoup(response_fallback.text, "html.parser")
            projects = extract_projects(soup_fallback)
            print(f"  Найдено без категории: {len(projects)}")

            # Save fallback HTML to debug if it was the one that returned results
            if projects:
                with open("C:/code/debug.html", "w", encoding="utf-8") as f:
                    f.write(response_fallback.text)

    if not projects:
        send_telegram(f"❌ По запросу <b>{keyword}</b> ничего не найдено")
        print("[X] Ничего не найдено")
        return

    send_telegram(f"🔍 Нашёл заказы по запросу: <b>{keyword}</b>")
    print(f"[OK] Отправляю {min(len(projects), 5)} заказов в Telegram...")

    for project in projects[:5]:
        try:
            title = project.get("name", "").strip()
            link = f"https://kwork.ru/projects/{project.get('id')}"

            # Format price nicely
            price_limit = project.get("priceLimit")
            if price_limit:
                try:
                    price = f"{float(price_limit):.0f} руб."
                except ValueError:
                    price = f"{price_limit} руб."
            else:
                price = "Бюджет не указан"

            msg = f"📌 <b>{title}</b>\n💰 {price}\n🔗 {link}"
            send_telegram(msg)
            print(f"  -> {title} | {price}")
            time.sleep(1)
        except Exception as e:
            continue

    print("[OK] Готово!")

keyword = input("Введи ключевое слово для поиска: ")
parse_kwork(keyword)