import re
import sqlite3
import email
import imaplib
import asyncio
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
import keyboard


from createbot import dp
from database import database


IMAP_SERVER = "imap.mail.ru"
SMTP_SERVER = "smtp.mail.ru"


class FSMloginsteam(StatesGroup):
    steamlogin = State()
    email = State()
    empass = State()


@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton(text="Да", callback_data="login"))
    keyboard.add(InlineKeyboardButton(text="Нет", callback_data="register"))

    await message.answer(
        text="Здравствуйте, вы зарегистрированы?", reply_markup=keyboard
    )


start_completed = False


@dp.callback_query_handler(text="login")
async def start1(call: CallbackQuery):
    global start_completed
    start_completed = True
    await call.message.answer("Введите свой логин стим")


@dp.message_handler()
async def check_number(message: types.Message):
    global start_completed, mail, empass, user_data, mailchek, empasschek

    steamlogin = message.text.lower()
    if not start_completed:
        return 
    conn = sqlite3.connect("base.db")
    c = conn.cursor()
    c.execute("SELECT * FROM list WHERE LOWER(steamlogin)=?", (steamlogin,))
    result = c.fetchone()
    if result:
        mail = result[1]
        mailchek = mail
        empass = result[2]
        empasschek = empass
        user_data = (mail, empass)
        await message.answer(
            f"Этот логин найден в базе данных. Почта: {mail}.Пароль: {empass}\n Проверить почту?", reply_markup=keyboard.test.login
        )
    else:
        await message.answer(f"Логин {message.text} не найден в базе данных.")
    conn.close()


@dp.callback_query_handler(text="register", state=None)
async def register(call: CallbackQuery):
    await call.message.answer("Введите свой логин стим")
    await FSMloginsteam.steamlogin.set()


@dp.message_handler(state=FSMloginsteam.steamlogin)
async def stlogin(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data["steamlogin"] = message.text
    await message.reply("Теперь введите свою почту")
    await FSMloginsteam.email.set()


@dp.message_handler(state=FSMloginsteam.email)
async def steammail(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data["email"] = message.text
    await message.reply("Теперь введите пароль от почты")
    await FSMloginsteam.empass.set()


@dp.message_handler(state=FSMloginsteam.empass)
async def steammailpass(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data["empass"] = message.text
    await database.sql_add_command(state)
    await state.finish()
    await message.reply("Регистрация завершена!")


dp.callback_query_handler(text="chek")
async def get_last_steam_email(call: CallbackQuery):
    # Обработчик нажатия кнопки "chek" в телеграм-боте

    try:
        loop = asyncio.get_event_loop()
        # Создание цикла событий asyncio

        if user_data is None:
            await call.message.answer("Не удалось получить данные из почтового ящика")
            return
        # Проверка наличия данных пользователя из почтового ящика

        mail_connection = await loop.run_in_executor(
            None, lambda: imaplib.IMAP4_SSL(IMAP_SERVER)
        )
        # Установка защищенного соединения с почтовым сервером

        mail_connection.login(user_data[0], user_data[1])
        mail_connection.select("INBOX")
        # Вход в почтовый ящик и выбор папки "INBOX"

        status, data = mail_connection.search(None, "FROM", '"Steam"')
        # Поиск писем от Steam

        latest_email_id = data[0].split()[-1]
        status, data = mail_connection.fetch(latest_email_id, "(RFC822)")
        # Извлечение последнего письма от Steam

        raw_email = data[0][1]
        email_message = email.message_from_bytes(raw_email)
        # Извлечение содержимого письма

        decoded_payload = None
        if email_message.is_multipart():
            for part in email_message.walk():
                if part.get_content_type() == "text/plain":
                    decoded_payload = part.get_payload(decode=True).decode("utf-8")
                    break
        else:
            decoded_payload = email_message.get_payload(decode=True).decode("utf-8")
        # Декодирование содержимого письма

        if decoded_payload:
            match = re.search(r'Код доступа(.*?)Если это были не вы', decoded_payload, re.DOTALL)
            if match:
                extracted_phrase = match.group(1).strip()
                await call.message.answer(f"{extracted_phrase}")
            else:
                await call.message.answer("Не удалось найти заданные фразы в письме")
        else:
            await call.message.answer("Не удалось декодировать содержимое письма")
        # Извлечение кода доступа из письма и отправка его пользователю

    except Exception as e:
        await call.message.answer(f"Произошла ошибка при чтении почты: {e}")
    finally:
        if "mail_connection" in locals():
            mail_connection.logout()
    # Обработка ошибок и выход из почтового ящика