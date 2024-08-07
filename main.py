import requests
from bs4 import BeautifulSoup
import telegram
from telegram.constants import ParseMode
import asyncio
from deep_translator import GoogleTranslator, exceptions
import time
import os

# Function to fetch all article URLs from the given page
def fetch_article_urls(base_url):
    article_urls = []
    response = requests.get(base_url)
    soup = BeautifulSoup(response.content, 'html.parser')

    # Find all article URLs on the page
    for h1_tag in soup.find_all('h1', id='list'):
        a_tag = h1_tag.find('a')
        if a_tag and a_tag.get('href'):
            article_urls.append(a_tag['href'])
    
    return article_urls

# Function to translate text to Gujarati with retry mechanism
def translate_to_gujarati(text):
    max_retries = 3
    for attempt in range(max_retries):
        try:
            translator = GoogleTranslator(source='auto', target='gu')
            return translator.translate(text)
        except exceptions.TranslationNotFoundException as e:
            print(f"Translation not found: {e}")
            return text
        except Exception as e:
            print(f"Error in translation (attempt {attempt + 1}): {e}")
            time.sleep(2)  # Wait before retrying
    return text

# Function to split message into chunks
def split_message(message, max_length=4096):
    return [message[i:i+max_length] for i in range(0, len(message), max_length)]

# Function to split content into two parts
def split_content_in_two(content):
    mid_index = len(content) // 2
    for i in range(mid_index, len(content)):
        if content[i] in ['\n', '.', '!', '?']:
            return content[:i + 1], content[i + 1:]
    return content, ""

# Function to scrape the content and send it to the Telegram channel
async def scrape_and_send_to_telegram(url, bot_token, channel_id):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    # Find the main content div
    main_content = soup.find('div', class_='inside_post column content_width')
    if not main_content:
        raise Exception("Main content div not found")
    
    # Find the heading
    heading = main_content.find('h1', id='list')
    if not heading:
        raise Exception("Heading not found")

    # Prepare the content to be sent
    heading_text = heading.get_text()
    translated_heading = translate_to_gujarati(heading_text)

    message = (
        f"🌟 {translated_heading}\n\n"
        f"🌟 {heading_text}\n\n"
    )

    # Iterate through the sub-tags of the main content
    content = ""
    for tag in main_content.find_all(recursive=False):
        if tag.get('class') == ['sharethis-inline-share-buttons', 'st-center', 'st-has-labels', 'st-inline-share-buttons', 'st-animated']:
            continue

        if tag.get('class') == ['prenext']:
            break

        text = tag.get_text()
        translated_text = translate_to_gujarati(text)

        if tag.name == 'p':
            content += f"🔸 {translated_text}\n\n"
            content += f"🔸 {text}\n\n"
        elif tag.name == 'h2':
            content += f"🔹 {translated_text}\n\n"
            content += f"🔹 {text}\n\n"
        elif tag.name == 'h4':
            content += f"⚡ {translated_text}\n\n"
            content += f"⚡ {text}\n\n"
        elif tag.name == 'ul':
            for li in tag.find_all('li'):
                li_text = li.get_text()
                translated_li_text = translate_to_gujarati(li_text)
                content += f"• {translated_li_text}\n"
                content += f"• {li_text}\n"
            content += "\n"

    part1, part2 = split_content_in_two(content)

    # Add attractive channel promotion for both parts
    promotion = (
        "\n━━━━━━━━━━━━━━━━━━━━\n"
        "🔥 **Stay Updated with the Latest News!** 🔥\n"
        "Join our Telegram channel for:\n"
        "📈 Latest Current Updates\n"
        "📰 Breaking News\n"
        "📚 In-Depth Articles\n"
        "💡 GK \n"
        "\n"
        "👉 [**Join Our Telegram Channel**](https://telegram.me/currentadda) 👈\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
    )

    part1_message = message + part1 + promotion
    part2_message = message + part2 + promotion if part2 else None

    # Split message if it's too long
    chunks_part1 = split_message(part1_message)
    chunks_part2 = split_message(part2_message) if part2_message else []

    # Initialize the bot
    bot = telegram.Bot(token=bot_token)

    # Send each chunk separately for part 1
    for chunk in chunks_part1:
        await bot.send_message(chat_id=channel_id, text=chunk, parse_mode=ParseMode.MARKDOWN)

    # Send each chunk separately for part 2, if it exists
    for chunk in chunks_part2:
        await bot.send_message(chat_id=channel_id, text=chunk, parse_mode=ParseMode.MARKDOWN)

# Async function to handle main logic
async def main():
    base_url = "https://www.gktoday.in/current-affairs/"
    pages = 1

    # Fetch all article URLs
    article_urls = fetch_article_urls(base_url)
    
    # Scrape all URLs and send them to the Telegram channel
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN", "1637529837:AAFraGS_WwfTV8rj9XOhBy7PoxnbnVXBVEM")
    channel_id = os.environ.get("TELEGRAM_CHANNEL_ID", "@currentadda")

    for url in article_urls:
        print(f"Scraping and sending: {url}")
        await scrape_and_send_to_telegram(url, bot_token, channel_id)

if __name__ == "__main__":
    asyncio.run(main())
