import os
import telebot
import yt_dlp
import vk_audio

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
    msg = bot.reply_to(message, 'Link to video')
    bot.register_next_step_handler(msg, get_link)


def get_link(message):
    user.link = message.text
    msg = bot.reply_to(message, 'Name of file')
    bot.register_next_step_handler(msg, get_name_of_file)


def get_name_of_file(message):
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


@bot.message_handler(commands=['vk'])
def vk(message):
    msg = bot.reply_to(message, 'Search query')
    bot.register_next_step_handler(msg, send_audio)


def send_audio(message):
    bot.send_audio(message.chat.id, vk_audio.main(message.text))


bot.infinity_polling()
