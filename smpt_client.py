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
    password = os.getenv('PASSWORD')

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

    with open(pdf_filename, "rb") as f:
        attach = MIMEApplication(f.read(), _subtype="pdf")
    attach.add_header(
        'Content-Disposition',
        'attachment',
        filename=os.path.basename(pdf_filename)
    )
    msg.attach(attach)

    s = smtplib.SMTP('smtp.yandex.ru', 587, timeout=10)

    try:
        s.starttls()
        s.login(login, password)
        s.sendmail(msg['From'], recipients_emails, msg.as_string())
        print(f"Email успешно отправлен на {recipients_emails}")
        main.bot.send_message(user_id, f"Отправляем файл на почту, ожидайте ...")
        main.bot.send_message(user_id, f"Email успешно отправлен на {recipients_emails}")
    except Exception as ex:
        print(f"Ошибка при отправке email: {ex}")
        main.bot.send_message(user_id, f"Ошибка при отправке email: {ex}")
    finally:
        s.quit()
