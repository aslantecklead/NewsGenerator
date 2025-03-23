import re
import os
import telebot
from telebot import types
from bs4 import BeautifulSoup
import random
import requests
from fastapi import FastAPI
import threading
import asyncio
import news_parser

from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
app = FastAPI()

bot = telebot.TeleBot('7910784059:AAHT9D9fz1FwEQoZTYoMVHCRBnpiTjv6YkI')

user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/603.3.8 (KHTML, like Gecko) Version/10.1.2 Safari/603.3.8",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:54.0) Gecko/20100101 Firefox/54.0"
]

filtered_news = []


async def fetch_news():
    url = "https://rosguard.gov.ru/news?onHome=true&placement=OnHome"
    headers = {
        "User-Agent": random.choice(user_agents)
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        bs4 = BeautifulSoup(response.text, "lxml")

        news_items = bs4.find_all('div', class_='blog-post-item clearfix')

        filtered_news.clear()
        for item in news_items:
            title_tag = item.find('h4').find('a')
            if title_tag:
                title = title_tag.text.strip()
                link = title_tag['href']
                date_tag = item.find('span', class_='localtime')
                date = date_tag.text.strip() if date_tag else "Дата не указана"
                image_url = item.find('a')['href']

                filtered_news.append({
                    'title': title,
                    'link': 'https://rosguard.gov.ru' + link,
                    'date': date,
                    'image': 'https://rosguard.gov.ru' + image_url
                })

    except requests.RequestException as e:
        print(f"Error during requests to {url}: {e}")

@app.get("/")
async def connect():
    await fetch_news()
    return filtered_news

@bot.message_handler(commands=['Новости', 'новости', 'hui'])
def send_welcome(message) -> None:
    asyncio.run(fetch_news())
    if not filtered_news:
        bot.reply_to(message, "Нет доступных новостей.")
        return

    news_message = "\n".join(
        [f"{i + 1} - {news['title']} | \n       Дата: {news['date']}" for i, news in
         enumerate(filtered_news)])

    keyboard = []
    for i, news in enumerate(filtered_news):
        keyboard.append([InlineKeyboardButton(f"{i + 1} - {news['title'] }", callback_data=f'news_{i}')])

    reply_markup = InlineKeyboardMarkup(keyboard)

    print("Отправлены новости")
    bot.send_message(message.chat.id, news_message, reply_markup=reply_markup)

user_selected_news = {}
@bot.callback_query_handler(func=lambda call: True)
def choose_news(call):
    if call.data.startswith('news_'):
        news_index = int(call.data.split('_')[1])
        if news_index < len(filtered_news):
            if filtered_news is not None:
                news = filtered_news[news_index]
                user_selected_news[call.message.chat.id] = news
                news_detail = f"{news['title']} |\n{news['date']} |\n{news['link']}\n\nВыбрать данную новость?"

                btn1 = types.KeyboardButton("Да, норм")
                btn2 = types.KeyboardButton("Не, другое")
                btn3 = types.KeyboardButton("Выход")
                markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
                markup.add(btn1, btn2, btn3)

                bot.send_message(call.message.chat.id, news_detail, reply_markup=markup)

def generate_document(user_id):
    selected_news = user_selected_news.get(user_id)
    if selected_news:
        bot.send_message(user_id, f"Генерация документа для новости: {selected_news['title']}")
        url = selected_news['link']
        news_parser.parse_news(url, user_id)
    else:
        bot.send_message(user_id, "Новость не найдена. Попробуйте ещё раз.")

@bot.message_handler(content_types=['text'])
def choose_option(message):
    user_id = message.chat.id

    if message.text == 'Да, норм':
        bot.send_message(user_id, "Отлично, делаю новости ... Ожидайте", reply_markup=ReplyKeyboardRemove())
        generate_document(user_id)
    elif message.text == 'Не, другое':
        bot.send_message(user_id, "Выберите другую новость: ", reply_markup=ReplyKeyboardRemove())
        send_welcome(message)
    elif message.text == 'Выход':
        bot.send_message(user_id, "Бот завершил работу. Чтобы начать заново, напишите /hui.", reply_markup=ReplyKeyboardRemove())
        bot.stop_polling()
    else:
        bot.send_message(user_id, "Неизвестная команда, попробуйте ещё раз", reply_markup=ReplyKeyboardRemove())

def run_bot():
    bot.polling(none_stop=True)


if __name__ == '__main__':
    import uvicorn

    bot_thread = threading.Thread(target=run_bot)
    bot_thread.start()

    uvicorn.run(app, host="127.0.0.1", port=8000)