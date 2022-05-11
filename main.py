import os
import telebot
from pytube import YouTube
import youtube_dl
import yt_dlp

bot = telebot.TeleBot('TOKEN')


class User:
    link = None
    file_name = None

    def __init__(self):
        self.link = None
        self.file_name = None


user = User

@bot.message_handler(commands=['start'])
def start(message):
    markup = telebot.types.ReplyKeyboardMarkup(row_width=1)
    vk = telebot.types.KeyboardButton('/vkvideo')
    youtube = telebot.types.KeyboardButton('/youtube')
    ok = telebot.types.KeyboardButton('/okvideo')
    tiktok = telebot.types.KeyboardButton('/tiktok')
    markup.add(vk, youtube, ok, tiktok)
    bot.send_message(message.chat.id, "Choose social network:", reply_markup=markup)


@bot.message_handler(commands=['youtube'])
def get_user_text(message):
    msg = bot.reply_to(message, 'Link to video on youtube')
    bot.register_next_step_handler(msg, get_link_for_youtube)


def get_link_for_youtube(message):
    user.link = message.text
    msg = bot.reply_to(message, 'Name of file')
    bot.register_next_step_handler(msg, get_name_of_file_for_youtube)


def get_name_of_file_for_youtube(message):
    user.file_name = message.text
    file_name = user.file_name + '.mp4'
    YouTube(user.link).streams.get_highest_resolution().download(None, file_name)
    bot.send_document(message.chat.id, open(file_name, 'rb'))
    os.remove(file_name)


@bot.message_handler(commands=['vkvideo'])
def get_user_text(message):
    msg = bot.reply_to(message, 'Link to video on vk')
    bot.register_next_step_handler(msg, get_link_for_vk)


def get_link_for_vk(message):
    user.link = message.text
    msg = bot.reply_to(message, 'Name of file')
    bot.register_next_step_handler(msg, get_name_of_file_for_vk)


def get_name_of_file_for_vk(message):
    user.file_name = message.text + '.mp4'
    ydl_opts = {
        'format': 'best',
        'ext': 'mp4',
        'outtmpl': str(os.getcwd() + '/' + user.file_name)
    }

    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.download([str(user.link)])

    bot.send_document(message.chat.id, open(user.file_name, 'rb'))
    os.remove(user.file_name)


@bot.message_handler(commands=['okvideo'])
def get_user_text(message):
    msg = bot.reply_to(message, 'Link to video on odnoklassniki')
    bot.register_next_step_handler(msg, get_link_for_ok)


def get_link_for_ok(message):
    user.link = message.text
    msg = bot.reply_to(message, 'Name of file')
    bot.register_next_step_handler(msg, get_name_of_file_for_ok)


def get_name_of_file_for_ok(message):
    user.file_name = message.text + '.mp4'
    ydl_opts = {
        'format': 'best',
        'ext': 'mp4',
        'outtmpl': str(os.getcwd() + '/' + user.file_name)
    }

    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.download([str(user.link)])

    bot.send_document(message.chat.id, open(user.file_name, 'rb'))
    os.remove(user.file_name)


@bot.message_handler(commands=['tiktok'])
def get_user_text(message):
    msg = bot.reply_to(message, 'Link to video on tiktok')
    bot.register_next_step_handler(msg, get_link_for_tiktok)


def get_link_for_tiktok(message):
    user.link = message.text
    msg = bot.reply_to(message, 'Name of file')
    bot.register_next_step_handler(msg, get_name_of_file_for_tiktok)


def get_name_of_file_for_tiktok(message):
    user.file_name = message.text + '.mp4'
    ydl_opts = {
        'format': 'best',
        'ext': 'mp4',
        'outtmpl': str(os.getcwd() + '/' + user.file_name)
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([str(user.link)])

    bot.send_document(message.chat.id, open(user.file_name, 'rb'))
    os.remove(user.file_name)


bot.infinity_polling()