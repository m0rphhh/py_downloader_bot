import telebot
from decouple import config

#file for logout bot from https://telegram.org
bot = telebot.TeleBot(config('BOT_TOKEN'))
bot.log_out()
