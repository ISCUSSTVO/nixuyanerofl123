import base64
import quopri
import sqlite3
import email
import imaplib
import asyncio
import keyboard
from aiogram import types, Bot
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from createbot import dp
from database import database



IMAP_SERVER = "imap.mail.ru"
SMTP_SERVER = "smtp.mail.ru"

# Определение состояний для машины состояний
class FSMloginsteam(StatesGroup):
    steamlogin = State()
    email = State()
    empass = State()

# Обработчик команды /start
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton(text="Да", callback_data="login"))
    keyboard.add(InlineKeyboardButton(text="Нет", callback_data="register"))
    
    await message.answer(text="Здравствуйте, вы зарегистрированы?", reply_markup=keyboard)

start_completed = False

# Обработчик нажатия кнопки "Да" при запуске бота
@dp.callback_query_handler(text_contains=['login'])
async def start(call: CallbackQuery):
    global start_completed
    start_completed = True
    await call.message.answer("Введите свой логин стим")

# Обработчик ввода логина стима
@dp.message_handler()
async def check_number(message: types.Message):
    global start_completed, mail, empass, user_data, mailchek, empasschek
    if not start_completed:
        return 
    conn = sqlite3.connect('base.db')
    c = conn.cursor()
    steamlogin = message.text.lower()
    c.execute("SELECT * FROM list WHERE LOWER(steamlogin)=?", (steamlogin,))
    result = c.fetchone()
    if result:
        mail = result[1]
        mailchek = mail 
        empass = result[2]
        empasschek = empass
        user_data = mail, empass
        await message.answer(f"Этот логин найден в базе данных. Почта: {mail}.\\nПароль: {empass}", reply_markup=keyboard.test.login)
    else:
        await message.answer(f"Номер {message.text} не найден в базе данных.")

# Обработчик нажатия кнопки "Нет" при запуске бота
@dp.callback_query_handler(text_contains=['register'], state=None)
async def register(call: CallbackQuery):
    await call.message.answer('Введите свой логин стим')
    await FSMloginsteam.steamlogin.set()

# Обработчики для машины состояний
@dp.message_handler(state=FSMloginsteam.steamlogin)
async def stlogin(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['steamlogin'] = message.text
    await message.reply('Теперь введите свою почту')
    await FSMloginsteam.email.set()

@dp.message_handler(state=FSMloginsteam.email)
async def steammail(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['email'] = message.text
    await message.reply('Теперь введите пароль от почты')
    await FSMloginsteam.empass.set()

@dp.message_handler(state=FSMloginsteam.empass)
async def steammailpass(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['empass'] = message.text
    await database.sql_add_command(state)
    await state.finish()

# Обработчик нажатия кнопки "chek"
@dp.callback_query_handler(text_contains=['chek'])
async def get_last_steam_email(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        try:
            loop = asyncio.get_event_loop()

            print(user_data, empasschek)
            if user_data is None:
                await message.answer("Не удалось получить данные из почтового ящика")
                return

            mail_connection = await loop.run_in_executor(None, imaplib.IMAP4_SSL, IMAP_SERVER)
            mail_connection.login(user_data[0], user_data[1])
            mail_connection.select('INBOX')

            status, data = mail_connection.search(None, 'FROM', '"Steam"')
            latest_email_id = data[0].split()[-1]
            status, data = mail_connection.fetch(latest_email_id, '(RFC822)')
            raw_email = data[0][1]
            
            if raw_email is None:
                await message.answer("Не удалось получить содержимое письма от Steam")
                return

            email_message = email.message_from_bytes(raw_email)
            
            if email_message is not None:
                decoded_payload = base64.b64decode(email_message.get_payload()).decode('utf-8')
                print(type(decoded_payload))

                if decoded_payload is not None:
                    await message.answer(f"Последнее письмо от Steam:\n\n{decoded_payload.decode()}")
                else:
                    await message.answer("Не удалось декодировать содержимое письма")
            else:
                await message.answer("Не удалось обработать письмо от Steam")

        except Exception as e:
            await message.answer(f"Произошла ошибка при чтении почты: {e}")


