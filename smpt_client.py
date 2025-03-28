import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.header import Header
from dotenv import load_dotenv
import smtplib
import main

load_dotenv()


def send_file(user_id, pdf_filename, email_subject, title, recipients_emails="ds_6898_tso@rosgvard.ru"):
    login = 'asalbekov.as@yandex.ru'

    try:
        pdf_filename = str(pdf_filename)
        email_subject = str(email_subject)
        title = str(title)
        recipients_emails = str(recipients_emails) if isinstance(recipients_emails, str) else recipients_emails
    except Exception as e:
        error = f"Ошибка преобразования данных: {e}"
        print(error)
        main.bot.send_message(user_id, error)
        return

    if not all([pdf_filename, email_subject, title]):
        error = "Ошибка: pdf_filename, email_subject или title = None!"
        print(error)
        main.bot.send_message(user_id, error)
        return

    pdf_path = os.path.abspath(pdf_filename)
    if not os.path.exists(pdf_path):
        error = f"PDF не найден: {pdf_path}"
        print(error)
        main.bot.send_message(user_id, error)
        return

    password = os.getenv('PASSWORD')
    if not password:
        error = "PASSWORD не загружен из .env!"
        print(error)
        main.bot.send_message(user_id, error)
        return

    try:
        msg = MIMEMultipart()
        msg['Subject'] = Header(email_subject, 'utf-8')
        msg['From'] = login

        if isinstance(recipients_emails, list):
            msg['To'] = ', '.join(recipients_emails)
        else:
            msg['To'] = recipients_emails

        email_body = f"""
        <html>
          <body>
            <h2>{title}</h2>
          </body>
        </html>
        """

        msg.attach(MIMEText(email_body, 'html', 'utf-8'))

        with open(pdf_path, "rb") as f:
            attach = MIMEApplication(f.read(), _subtype="pdf")
        attach.add_header(
            'Content-Disposition',
            'attachment',
            filename=os.path.basename(pdf_path)
        )
        msg.attach(attach)

        with smtplib.SMTP('smtp.yandex.ru', 587, timeout=10) as s:
            s.starttls()
            s.login(login, password)
            s.sendmail(msg['From'], recipients_emails, msg.as_string())
            print(f"Email успешно отправлен на {recipients_emails}")
            main.bot.send_message(user_id, "Отправляем файл на почту, ожидайте ...")
            main.bot.send_message(user_id, f"Email успешно отправлен на {recipients_emails}")

    except Exception as ex:
        error = f"Ошибка при отправке email: {ex}"
        print(error)
        main.bot.send_message(user_id, error)