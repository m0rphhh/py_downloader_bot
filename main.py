import os
import random
import re
import string
import telebot
import yt_dlp
from yt_dlp import DownloadError
import vk_audio
import yandex_disk
import moviepy.editor as mp
from decouple import config
import sentry_sdk

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
                          'link is required, leave other settings empty if they are not required\n'
                          'add yandex token if you want files to be uploaded to yandex disk\n'
                          'tap this link https://oauth.yandex.ru/authorize?response_type=token&client_id'
                          f'={config("YANDEX_ID")}&redirect_uri=http://127.0.0.1:4996 and get your token '
                          'from query string "access_token=<token>"\n'
                          'leave yandex_path empty if token is not specified or if you want file to be uploaded to '
                          'root of your disk, else insert info like : '
                          '"/path"')
    msg = bot.reply_to(message, 'link:http...\n'
                                'filename:video...\n'
                                'cut:00:00:00 00:01:00\n'
                                'audio_only:yes\n'
                                'yandex_disk_token:\n'
                                'yandex_path:\n'
                                'vk_order:')
    bot.register_next_step_handler(msg, get_info)


def get_info(message):
    info = message.text
    info_split = info.split('\n')

    try:
        link = info_split[0].split("link:", 1)[1]
        filename = info_split[1].split("filename:", 1)[1]

        if filename == '':
            filename = 'default'

        cut = info_split[2].split("cut:", 1)[1]
        audio_only = info_split[3].split("audio_only:", 1)[1]
        yandex_disk_token = info_split[4].split("yandex_disk_token:", 1)[1]
        yandex_path = info_split[5].split("yandex_path:", 1)[1]
        vk_order = info_split[6].split("vk_order:", 1)[1]

        use_yandex = False
        if yandex_disk_token != '' and yandex_path != '':
            if not yandex_disk.check_disk(yandex_disk_token):
                bot.reply_to(message, 'yandex token is incorrect, try one more time')
                return

            use_yandex = True

        vk_audio_pattern = '^https*:\/\/vk.com\/audios'
        vk_order_pattern = '^\d*$'
        if re.match(vk_audio_pattern, link):
            vk_order = int(vk_order) if re.match(vk_order_pattern, vk_order) else 0
            query_pattern = '\?q=(.*)'
            query_regex = re.search(query_pattern, link)
            query = query_regex.group(1)
            send_audio(message, query.replace('%20', ' '), use_yandex, yandex_disk_token, yandex_path, filename,
                       vk_order)

            return
    except IndexError:
        bot.reply_to(message, 'template filled incorrectly, type in /start to start over (some of settings are empty)')
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
        if use_yandex:
            yandex_disk.upload_file_to_yandex_disk(yandex_disk_token, yandex_path, open(filename + '.mp3', 'rb'), filename + '.mp3')
        else:
            bot.send_audio(message.chat.id, open(filename + '.mp3', 'rb'))
        os.remove(filename + '.mp3')
        os.remove(filename + '.mp4')
        if is_cut:
            os.remove(edited_filename)
    else:
        try:
            if use_yandex:
                yandex_disk.upload_file_to_yandex_disk(yandex_disk_token, yandex_path, open(edited_filename, 'rb'),
                                                       filename + '.mp4')
            else:
                bot.send_document(message.chat.id, open(edited_filename, 'rb'))

            os.remove(edited_filename)
            os.remove(filename + '.mp4')

        except FileNotFoundError:
            if use_yandex:
                yandex_disk.upload_file_to_yandex_disk(yandex_disk_token, yandex_path, open(filename + '.mp4', 'rb'),
                                                       filename + '.mp4')
            else:
                bot.send_document(message.chat.id, open(filename + '.mp4', 'rb'))

            os.remove(filename + '.mp4')


def send_audio(message, query, use_yandex, token, path, filename, order):
    if not use_yandex:
        bot.send_audio(message.chat.id, vk_audio.main(query, order))
    else:
        yandex_disk.upload_file_to_yandex_disk(token, path, vk_audio.main(query, order), filename + '.mp3')


if __name__ == '__main__':
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
