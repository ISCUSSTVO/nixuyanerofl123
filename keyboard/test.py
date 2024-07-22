from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
log = InlineKeyboardButton('Да', callback_data='chek')
login = InlineKeyboardMarkup(resize_keyboard = True)\
    .add(log)
##########################asdqwe################
mod_butt = InlineKeyboardButton('Добавить аккаунт', callback_data='addacc')
mod_butt1 = InlineKeyboardButton('Удалить аккаунт',callback_data='dellacc') 
moderator_action = InlineKeyboardMarkup(resize_keyboard = True)\
    .add(mod_butt,mod_butt1)

