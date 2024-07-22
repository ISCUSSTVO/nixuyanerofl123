from aiogram import executor
from createbot import dp
from handlers import client
async def on_startup(_):
    print("Бот вышел в онлайн")




executor.start_polling(dp, skip_updates=True, on_startup=on_startup)