import os
import glob
import requests
import random
import hashlib
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import main
import smpt_client

user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/603.3.8 (KHTML, like Gecko) Version/10.1.2 Safari/603.3.8",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:54.0) Gecko/20100101 Firefox/54.0"
]

# Initialize fonts
pdfmetrics.registerFont(TTFont('Gidole-Regular', 'fonts/Gidole-Regular.ttf'))


def get_cached_filename(url):
    return hashlib.md5(url.encode()).hexdigest() + ".jpg"


def download_image(url, save_path):
    try:
        headers = {
            "User-Agent": random.choice(user_agents)
        }
        response = requests.get(url, headers=headers, stream=True)
        response.raise_for_status()
        with open(save_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        return True
    except Exception as e:
        print(f"Ошибка при загрузке изображения: {e}")
        return False


def cleanup_old_files(user_id, max_files=3):
    files = glob.glob(f"pdf_files/news_{user_id}_*.pdf")
    files.sort(key=os.path.getmtime, reverse=True)

    for old_file in files[max_files:]:
        try:
            os.remove(old_file)
            print(f"Удален старый файл: {old_file}")
        except Exception as e:
            print(f"Ошибка при удалении файла {old_file}: {e}")


def generatePdfFile(title, body, image_url, timestamp, source, user_id):
    os.makedirs("pdf_files", exist_ok=True)
    os.makedirs("image_cache", exist_ok=True)

    current_date = datetime.now().strftime("%d_%m_%Y")
    formatted_date = datetime.now().strftime("%d %B %Y года").replace("January", "января").replace("February",
                                                                                                   "февраля") \
        .replace("March", "марта").replace("April", "апреля").replace("May", "мая").replace("June", "июня") \
        .replace("July", "июля").replace("August", "августа").replace("September", "сентября") \
        .replace("October", "октября").replace("November", "ноября").replace("December", "декабря")

    pdf_filename = f"pdf_files/news_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

    doc = SimpleDocTemplate(pdf_filename, pagesize=A4, rightMargin=10 * mm, leftMargin=10 * mm, topMargin=5 * mm)

    styles = getSampleStyleSheet()

    if 'CustomTitle' not in styles:
        styles.add(ParagraphStyle(name='CustomTitle', alignment=TA_LEFT, fontSize=24, leading=30,
                                  fontName='Gidole-Regular', textColor=colors.black))
    if 'CustomSubtitle' not in styles:
        styles.add(ParagraphStyle(name='CustomSubtitle', alignment=TA_CENTER, fontSize=18, leading=22,
                                  fontName='Gidole-Regular', textColor=colors.white))
    if 'Justify' not in styles:
        styles.add(ParagraphStyle(name='Justify', alignment=TA_JUSTIFY, fontSize=12, leading=15,
                                  fontName='Gidole-Regular', textColor=colors.black))
    if 'Info' not in styles:
        styles.add(ParagraphStyle(name='Info', alignment=TA_JUSTIFY, fontSize=10, leading=12,
                                  fontName='Gidole-Regular', textColor=colors.grey))

    content = []

    logo_url = "https://rosguard.gov.ru/static/images/main/rosgvard_logo.png"
    logo_path = "image_cache/rosgvard_logo.png"

    if not os.path.exists(logo_path):
        print("Загрузка логотипа...")
        download_image(logo_url, logo_path)

    if os.path.exists(logo_path):
        logo = Image(logo_path, width=60, height=60)
    else:
        logo = None

    title_text = Paragraph("Новости РОСГВАРДИИ!", styles['CustomTitle'])
    table_data = [[title_text, logo]]
    table = Table(table_data, colWidths=[doc.width * 0.7, doc.width * 0.3])
    table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
    ]))
    content.append(table)

    subtitle = Paragraph(title, styles['CustomSubtitle'])
    subtitle_table = Table([[subtitle]], colWidths=[doc.width])
    subtitle_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.darkgrey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
    ]))
    content.append(subtitle_table)

    news_image_path = os.path.join("image_cache", get_cached_filename(image_url))
    if not os.path.exists(news_image_path):
        print("Загрузка изображения новости...")
        download_image(image_url, news_image_path)

    if os.path.exists(news_image_path):
        content.append(Spacer(1, 12))
        news_image = Image(news_image_path, width=400, height=200)
        news_image.hAlign = 'CENTER'
        content.append(news_image)

    content.append(Spacer(1, 12))
    content.append(Paragraph(body, styles['Justify']))

    content.append(Spacer(1, 12))
    content.append(Table([[""]], colWidths=[doc.width], style=[
        ('LINEABOVE', (0, 0), (-1, -1), 1, colors.Color(0, 0, 0, alpha=0.3)),
    ]))

    info_text = f"Источник: {source}"
    time_text = f"⏱︎ {timestamp}"
    content.append(Spacer(1, 12))
    content.append(Paragraph(info_text, styles['Info']))
    content.append(Paragraph(time_text, styles['Info']))

    doc.build(content)
    print(f"PDF-документ '{pdf_filename}' успешно создан!")

    cleanup_old_files(user_id, max_files=3)

    main.bot.send_message(user_id, "PDF успешно создан, сейчас вышлем, оцените:")
    main.bot.send_document(user_id, open(pdf_filename, "rb"))

    email_subject = f"Новости на {formatted_date}"

    smpt_client.send_file(user_id, pdf_filename, email_subject, title)