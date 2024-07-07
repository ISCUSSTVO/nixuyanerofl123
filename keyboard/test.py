from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
log = InlineKeyboardButton('Да', callback_data='chek')
login = InlineKeyboardMarkup(resize_keyboard = True)\
    .add(log)

