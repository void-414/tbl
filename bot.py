import asyncio
import requests
import re
from bs4 import BeautifulSoup
from telegram import Bot
from telegram.error import TelegramError

# === CONFIGURATION ===
BOT_TOKEN = '8048142660:AAHVgCaI7VOrGQW3pmr9Xc9d_mi44Ode5pk'  # <-- Replace with your bot token
GROUP_CHAT_ID = '-1002724747749'  # e.g. @TamilGroup or -1001234567890
BASE_URL = "https://www.1tamilblasters.fi/"
HEADERS = {"User-Agent": "Mozilla/5.0"}
SEEN_TOPICS_FILE = "seen_topics.txt"

# === REGEX PATTERNS ===
TOPIC_LINK_PATTERN = re.compile(r"https://www\.1tamilblasters\.fi/index\.php\?/forums/topic/\d+")
MAGNET_PATTERN = re.compile(r"magnet:\?xt=urn:btih:[a-zA-Z0-9]+")

# === BOT SETUP ===
bot = Bot(token=BOT_TOKEN)

# === HELPER FUNCTIONS ===
def get_soup(url):
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return BeautifulSoup(response.text, "html.parser")

def extract_links(soup, pattern):
    return [a['href'] for a in soup.find_all('a', href=True) if pattern.match(a['href'])]

def load_seen_topics():
    try:
        with open(SEEN_TOPICS_FILE, "r", encoding="utf-8") as f:
            return set(line.strip() for line in f)
    except FileNotFoundError:
        return set()

def save_seen_topic(topic_url):
    with open(SEEN_TOPICS_FILE, "a", encoding="utf-8") as f:
        f.write(topic_url + "\n")

# === MAIN SCRAPER ===
async def scrape_and_send():
    seen_topics = load_seen_topics()

    try:
        soup = get_soup(BASE_URL)
        topic_links = extract_links(soup, TOPIC_LINK_PATTERN)
    except Exception as e:
        print("❌ Failed to load homepage:", e)
        return

    print(f"✅ Found {len(topic_links)} topics on homepage.")

    for topic_url in topic_links:
        if topic_url in seen_topics:
            continue  # Skip already processed topics

        print(f"🔍 New topic found: {topic_url}")

        try:
            topic_soup = get_soup(topic_url)
            magnets = [a['href'] for a in topic_soup.find_all('a', href=True) if MAGNET_PATTERN.match(a['href'])]

            if not magnets:
                print(f"⚠️ No magnets found in topic: {topic_url}")
                save_seen_topic(topic_url)
                continue

            for magnet in magnets:
                msg = f"/ql {magnet}"
                await bot.send_message(chat_id=GROUP_CHAT_ID, text=msg)
                print(f"✅ Sent: {magnet}")
                await asyncio.sleep(1)

            save_seen_topic(topic_url)

        except TelegramError as te:
            print("⚠️ Telegram error:", te)
        except Exception as e:
            print("⚠️ Error processing topic:", e)

# === ENTRY POINT ===
if __name__ == "__main__":
    asyncio.run(scrape_and_send())
