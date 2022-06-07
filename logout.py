import telebot
import os
#file for logout bot from https://telegram.org
bot = telebot.TeleBot(os.getenv('BOT_TOKEN'))
bot.log_out()
