import os
import random
import re
import string
import telebot
import yt_dlp
import vk_audio

bot = telebot.TeleBot('TOKEN')


class User:
    link = None
    file_name = None
    cut = None
    audio_only = None

    def __init__(self):
        self.link = None
        self.file_name = None
        self.cut = None
        self.audio_only = None


user = User


@bot.message_handler(commands=['start'])
def start(message):
    msg = bot.reply_to(message, 'Link to video')
    bot.register_next_step_handler(msg, get_link)


def get_link(message):
    user.link = message.text
    msg = bot.reply_to(message, 'Name of file')
    bot.register_next_step_handler(msg, get_cut)


def get_cut(message):
    user.file_name = message.text
    msg = bot.reply_to(message,
                       'print wanted cut in format 00:00:00 00:00:00 \nprint any char for downloading without cut')
    bot.register_next_step_handler(msg, get_audio_only_info)


def get_audio_only_info(message):
    user.cut = message.text
    msg = bot.reply_to(message, 'do you want audio only? print "yes". else type any char or string')
    bot.register_next_step_handler(msg, get_name_of_file)


def get_name_of_file(message):
    user.audio_only = message.text
    edited_filename = f"{''.join(random.choice(string.ascii_lowercase) for i in range(10))}.mp4"
    ydl_opts = {
        'format': 'best',
        'ext': 'mp4',
        'outtmpl': str(os.getcwd() + '/' + user.file_name + '.mp4'),
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([str(user.link)])

    audio_only_pattern = '^yes$'
    time_pattern = '^\d{2}:\d{2}:\d{2} \d{2}:\d{2}:\d{2}$'

    is_cut = False
    if re.match(time_pattern, user.cut):
        is_cut = True
        from_to_string = user.cut.split()
        cut_script = f"""ffmpeg -i {user.file_name + '.mp4'} -ss {from_to_string[0]} -to {from_to_string[1]} -c copy {edited_filename} """
        os.system(cut_script)

    is_audio_only = False
    if re.match(audio_only_pattern, user.audio_only):
        is_audio_only = True
        if is_cut:
            file = edited_filename
        else:
            file = user.file_name + '.mp4'

        audio_only_script = f"""ffmpeg -i {file} {user.file_name + '.mp3'} """
        os.system(audio_only_script)
        print(user.file_name + '.mp3')

    if is_audio_only:
        bot.send_audio(message.chat.id, open(user.file_name + '.mp3', 'rb'))
        os.remove(user.file_name + '.mp3')
        os.remove(user.file_name + '.mp4')
        if is_cut:
            os.remove(edited_filename)
    else:
        try:
            bot.send_document(message.chat.id, open(edited_filename, 'rb'))
            os.remove(edited_filename)
            os.remove(user.file_name + '.mp4')
        except FileNotFoundError:
            bot.send_document(message.chat.id, open(user.file_name + '.mp4', 'rb'))
            os.remove(user.file_name + '.mp4')


@bot.message_handler(commands=['vk'])
def vk(message):
    msg = bot.reply_to(message, 'Search query')
    bot.register_next_step_handler(msg, send_audio)


def send_audio(message):
    bot.send_audio(message.chat.id, vk_audio.main(message.text))


bot.infinity_polling()
