import random
from bs4 import BeautifulSoup
import requests
import main
from pdf_generator import generatePdfFile

last_news = []

def trim_text_to_words(text, max_words):
    words = text.split()
    if len(words) <= max_words:
        return text

    trimmed_words = words[:max_words]
    trimmed_text = " ".join(trimmed_words)

    last_punctuation = max(
        trimmed_text.rfind("."),
        trimmed_text.rfind("!"),
        trimmed_text.rfind("?"),
    )

    if last_punctuation != -1:
        return trimmed_text[:last_punctuation + 1]
    return trimmed_text

def edit_file(current_news, user_id):
    new_title = current_news[0]['title']
    if '(видео)' in new_title:
        new_title = new_title.replace('(видео)', '')

    new_body = current_news[0]['text']
    new_body = trim_text_to_words(new_body, 150)

    new_url = last_news[0]['image_url']
    new_timestamp = current_news[0]['publication_timestamp']
    new_source = last_news[0]['source']

    generatePdfFile(
        title=new_title,
        body=new_body,
        image_url=new_url,
        timestamp=new_timestamp,
        source=new_source,
        user_id=user_id
    )

def parse_news(url, user_id):
    headers = {
        "User-Agent": random.choice(main.user_agents)
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        bs4 = BeautifulSoup(response.text, "lxml")
        last_news.clear()

        title_tag = bs4.find("h1", class_="blog-post-title uppercase")
        body_texts = bs4.find("div", class_="blog-post-item").find_all("p") if bs4.find("div",
                                                                                        class_="blog-post-item") else []
        image_tag = bs4.find("img", class_="img-responsive")
        publication_timestamp_tag = bs4.find("span", class_="font-lato localtime")
        source_tag = bs4.find("span", class_="pull-right text-right margin-top-6 font-lato font-style-italic")

        title = title_tag.text.strip() if title_tag else "Заголовок не найден"
        text = "\n".join([p.text.strip() for p in body_texts]) if body_texts else "Текст не найден"
        image_url = 'https://rosguard.gov.ru' + image_tag['src'] if image_tag and image_tag.get(
            'src') else "Изображение не найдено"
        publication_timestamp = publication_timestamp_tag.text.strip() if publication_timestamp_tag else "Дата не указана"
        source = source_tag.text.strip() if source_tag else "Источник не указан"

        new_news = {
            "title": title,
            "text": text,
            "image_url": image_url,
            "publication_timestamp": publication_timestamp,
            "source": source,
        }

        last_news.append(new_news)

        news_text = (
            f"📰 <b>{title}</b>\n\n"
            f"📝 <i>{text}</i>\n\n"
            f"🖼️ <a href='{image_url}'>Изображение</a>\n\n"
            f"📅 <b>Дата публикации:</b> {publication_timestamp}\n"
            f"🔗 <b>Источник:</b> {source}"
        )

        main.bot.send_message(user_id, news_text, parse_mode="HTML", disable_web_page_preview=False)

    except requests.RequestException as e:
        print(f"Ошибка при запросе к {url}: {e}")
        main.bot.send_message(user_id, "Произошла ошибка при получении новости. Попробуйте позже.")
    except Exception as e:
        print(f"Ошибка при парсинге: {e}")
        main.bot.send_message(user_id, "Произошла ошибка при обработке новости.")
    edit_file(last_news, user_id)