import imaplib
import email
from email.header import decode_header
import pandas as pd
import getpass

# --- НАСТРОЙКИ ---
EMAIL_USER = "kirillvidov132@gmail.com"  # ВАШ ЛОГИН
EMAIL_PASS = "fdjv dhng hzkn eame"  # ВАШ ПАРОЛЬ ПРИЛОЖЕНИЯ
IMAP_SERVER = "imap.gmail.com"  # Для Gmail. (imap.yandex.ru / imap.mail.ru)
NUM_EMAILS = 200  # Сколько последних писем скачать


def clean_text(text):
    """Убирает лишние пробелы и переносы строк"""
    if text:
        return " ".join(text.split())
    return ""


def decode_str(header_value):
    """Декодирует тему письма (убирает кракозябры =?UTF-8?...)"""
    if not header_value:
        return ""
    decoded_list = decode_header(header_value)
    default_charset = 'utf-8'
    text_parts = []

    for decoded_bytes, charset in decoded_list:
        if isinstance(decoded_bytes, bytes):
            try:
                part = decoded_bytes.decode(charset or default_charset)
            except (LookupError, UnicodeDecodeError):
                part = decoded_bytes.decode(default_charset, errors='replace')
            text_parts.append(part)
        else:
            text_parts.append(str(decoded_bytes))

    return "".join(text_parts)


def get_body(msg):
    """Извлекает чистый текст из письма"""
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))

            # Ищем текстовую часть, игнорируем вложения
            if content_type == "text/plain" and "attachment" not in content_disposition:
                try:
                    return part.get_payload(decode=True).decode()
                except:
                    pass
    else:
        # Если письмо не составное, просто берем текст
        try:
            return msg.get_payload(decode=True).decode()
        except:
            pass
    return ""


def main():
    print("Подключаемся к серверу...")
    mail = imaplib.IMAP4_SSL(IMAP_SERVER)

    try:
        mail.login(EMAIL_USER, EMAIL_PASS)
        print("Успешный вход!")
    except Exception as e:
        print(f"Ошибка входа: {e}")
        print("Совет: Проверьте, включили ли вы 'Пароль приложения' в настройках почты.")
        return

    mail.select("inbox")

    # Поиск писем (ALL - все, UNSEEN - непрочитанные)
    status, messages = mail.search(None, "ALL")
    email_ids = messages[0].split()

    # Берем последние N писем (идем с конца)
    latest_email_ids = email_ids[-NUM_EMAILS:]

    data_list = []

    print(f"Начинаем скачивание {len(latest_email_ids)} писем...")

    for i, e_id in enumerate(reversed(latest_email_ids)):
        # Скачиваем письмо
        res, msg_data = mail.fetch(e_id, "(RFC822)")
        for response_part in msg_data:
            if isinstance(response_part, tuple):
                msg = email.message_from_bytes(response_part[1])

                # Получаем тему и отправителя
                subject = decode_str(msg["Subject"])
                sender = decode_str(msg["From"])

                # Получаем текст
                body = get_body(msg)

                # Очищаем текст (убираем HTML теги, если они просочились, можно доработать)
                # Для простоты пока просто берем text/plain

                if body:
                    data_list.append({
                        "Subject": subject,
                        "From": sender,
                        "Body": clean_text(body),
                        "Category": ""  # Пустая колонка для вашей разметки
                    })

        if i % 20 == 0:
            print(f"Обработано {i} писем...")

    # Сохраняем в CSV
    df = pd.DataFrame(data_list)
    filename = "my_emails.csv"
    df.to_csv(filename, index=False, encoding='utf-8-sig')  # utf-8-sig чтобы Excel открыл кириллицу

    print(f"\nГотово! Скачано {len(df)} писем.")
    print(f"Откройте файл {filename} и заполните колонку 'Category'.")


if __name__ == "__main__":
    main()