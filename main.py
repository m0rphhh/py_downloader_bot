import os
import random
import re
import string
import telebot
import yt_dlp
from yt_dlp import DownloadError
import vk_audio
import moviepy.editor as mp
from decouple import config
import sentry_sdk
import requests

sentry_sdk.init(
    config('SENTRY_TOKEN'),
    traces_sample_rate=1.0
)

bot = telebot.TeleBot(config('BOT_TOKEN'))


def get_duration(seconds):
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    return "%d:%02d:%02d" % (h, m, s)


@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, 'copy this template and insert your data\n'
                          'if you need vk audio, insert only vk link with query like this:\n'
                          'link:https://vk.com/audios244838604?q=nothing%20but%20thieves%20amsterdam\n'
                          'link is required, leave other settings empty if they are not required')
    msg = bot.reply_to(message, 'link:http...\n'
                                'filename:video...\n'
                                'cut:00:00:00 00:01:00\n'
                                'audio_only:yes\n')
    bot.register_next_step_handler(msg, get_info)


def get_info(message):
    info = message.text
    info_split = info.split('\n')

    try:
        link = info_split[0].split("link:", 1)[1]
        vk_audio_pattern = '^https*:\/\/vk.com\/audios'
        if re.match(vk_audio_pattern, link):
            query_pattern = '\?q=(.*)'
            query_regex = re.search(query_pattern, link)
            query = query_regex.group(1)
            send_audio(message, query.replace('%20', ' '))
            return
        filename = info_split[1].split("filename:", 1)[1]
        if filename == '':
            filename = 'video'
        cut = info_split[2].split("cut:", 1)[1]
        audio_only = info_split[3].split("audio_only:", 1)[1]
    except IndexError as e:
        bot.reply_to(message, 'template filled incorrectly, type in /start to start over (some of settings are empty)')
        # sentry_sdk.capture_exception(error=e)
        return

    edited_filename = f"{''.join(random.choice(string.ascii_lowercase) for i in range(10))}.mp4"

    ydl_opts = {
        'format': 'best',
        'ext': 'mp4',
        'outtmpl': str(os.getcwd() + '/' + filename + '.mp4'),
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            ydl.download([str(link)])
        except DownloadError:
            bot.reply_to(message, 'template filled incorrectly, type in /start to start over (incorrect link)')

    duration = get_duration(mp.VideoFileClip(filename + '.mp4').duration)
    from_to_string = cut.split()

    audio_only_pattern = '^yes$'
    time_pattern = '^\d{2}:\d{2}:\d{2} \d{2}:\d{2}:\d{2}$'

    is_cut = False
    if re.match(time_pattern, cut) and from_to_string[0] < from_to_string[1] and from_to_string[1] > \
            from_to_string[0] and from_to_string[1] <= duration and from_to_string[0] < duration:
        is_cut = True
        cut_script = f"""ffmpeg -i {filename + '.mp4'} -ss {from_to_string[0]} -to {from_to_string[1]} -c copy {edited_filename} """
        os.system(cut_script)

    is_audio_only = False
    if re.match(audio_only_pattern, audio_only):
        is_audio_only = True
        if is_cut:
            file = edited_filename
        else:
            file = filename + '.mp4'

        audio_only_script = f"""ffmpeg -i {file} {filename + '.mp3'} """
        os.system(audio_only_script)

    if is_audio_only:
        bot.send_audio(message.chat.id, open(filename + '.mp3', 'rb'))
        os.remove(filename + '.mp3')
        os.remove(filename + '.mp4')
        if is_cut:
            os.remove(edited_filename)
    else:
        try:
            bot.send_document(message.chat.id, open(edited_filename, 'rb'))
            os.remove(edited_filename)
            os.remove(filename + '.mp4')
        except FileNotFoundError:
            bot.send_document(message.chat.id, open(filename + '.mp4', 'rb'))
            os.remove(filename + '.mp4')


def send_audio(message, query):
    bot.send_audio(message.chat.id, vk_audio.main(query))


if __name__ == '__main__':
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
