import os
import random
import re
import string
import telebot
from telebot import apihelper
import yt_dlp
from yt_dlp import DownloadError
from telebot.apihelper import ApiTelegramException
import vk_audio
import yandex_disk
import moviepy.editor as mp
import sentry_sdk

from db_init.user import User

from exceptions.IncorrectLinkError import IncorrectLinkError
from exceptions.TemplateError import TemplateError
from exceptions.YandexTokenError import YandexTokenError
from exceptions.CutFailedError import CutFailedError
from exceptions.EntityTooLargeError import EntityTooLargeError

sentry_sdk.init(
    os.getenv('SENTRY_TOKEN'),
    traces_sample_rate=1.0
)

apihelper.API_URL = "http://server:8081/bot{0}/{1}"
bot = telebot.TeleBot(os.getenv('BOT_TOKEN'))

# TEXT DATA

default_template = 'link:\nfilename:\ncut:\naudio_only:\nyandex_disk_token:\nyandex_path:\nvk_order:'

instruction = 'copy this template and insert your data\n' \
              'link:required, example(link:https://www.youtube.com/watch?v=AzqEnFVv0MM)\n' \
              'filename:not required, example(filename:best_video)\n' \
              'cut:not required, example(cut 00:00:00 00:01:00) <- in this format\n' \
              'audio_only:not required, insert yes or any other value\n' \
              'yandex_disk_token:not required, insert your yandex token if' \
              ' you want to upload file to your yandex disk. Tap this link to get your key https' \
              '://oauth.yandex.ru/authorize?response_type=token&client_id' \
              f'={os.getenv("YANDEX_ID")}&redirect_uri=https://oauth.yandex.ru/verification_code' \
              ' and take it from query_string' \
              ' (access_token=<token>)\n' \
              'yandex_path:not required, example(yandex_path:videos), ' \
              'file will create in this directory on your yandex disk\n' \
              'vk_order:not required. example(vk_order:3)' \

help_message = '/start for downloading files\n' \
               '/change_template - change your personal template for downloads\n' \
               '/set_default_template - set default template for downloads'


@bot.message_handler(commands=['start'])
def start(message):
    user = get_user(message)

    bot.reply_to(message, instruction)
    msg = bot.reply_to(message, user.template)
    bot.register_next_step_handler(msg, get_info)


def get_info(message):
    info = message.text
    info_split = info.split('\n')

    try:
        link = info_split[0].split("link:", 1)[1]
        yandex_filename = filename = info_split[1].split("filename:", 1)[1]
        cut = info_split[2].split("cut:", 1)[1]
        audio_only = info_split[3].split("audio_only:", 1)[1]
        yandex_disk_token = info_split[4].split("yandex_disk_token:", 1)[1]
        yandex_path = info_split[5].split("yandex_path:", 1)[1]
        vk_order = info_split[6].split("vk_order:", 1)[1]
    except IndexError:
        bot.reply_to(message, 'template filled incorrectly (some of filters are missing), type in /start to start over')
        raise TemplateError('template filled incorrectly, some of settings are missing')

    if filename == '':
        yandex_filename = filename = f"{''.join(random.choice(string.ascii_lowercase) for i in range(10))}"

    filename = 'files/' + str(message.chat.id) + '/' + filename

    use_yandex = False
    if yandex_disk_token != '' and yandex_path != '':
        if not yandex_disk.check_disk(yandex_disk_token):
            bot.reply_to(message, 'yandex token is incorrect, try one more time')
            raise YandexTokenError('yandex token is incorrect')

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
        clear_sub_directory_by_id(message)
        return

    edited_filename = \
        'files/' + str(
            message.chat.id) + '/' + f"{''.join(random.choice(string.ascii_lowercase) for i in range(10))}.mp4"

    download_video(filename, link, message)

    duration = get_duration(mp.VideoFileClip(filename + '.mp4').duration)
    is_cut = get_cut_file(cut, filename, edited_filename, duration, message)
    is_audio_only = get_audio_only(audio_only, is_cut, edited_filename, filename)

    if is_audio_only:
        if use_yandex:
            yandex_disk.upload_file_to_yandex_disk(yandex_disk_token, yandex_path, open(filename + '.mp3', 'rb'),
                                                   yandex_filename + '.mp3')
        else:
            try:
                bot.send_audio(message.chat.id, open(filename + '.mp3', 'rb'), timeout=100)
            except ApiTelegramException as e:
                bot.reply_to(message, 'file is too large, max size is 1500MB.')
                clear_sub_directory_by_id(message)
                raise EntityTooLargeError(e.description)

    else:
        if use_yandex:
            filename_to_send = filename + '.mp4' if not is_cut else edited_filename
            yandex_disk.upload_file_to_yandex_disk(yandex_disk_token, yandex_path, open(filename_to_send, 'rb'),
                                                   yandex_filename + '.mp4')
            clear_sub_directory_by_id(message)
        else:
            filename_to_send = filename + '.mp4' if not is_cut else edited_filename
            try:
                bot.send_video(message.chat.id, open(filename_to_send, 'rb'), timeout=200)
            except ApiTelegramException as e:
                bot.reply_to(message, 'file is too large, max size is 50MB.\n Try to upload file on yandex disk')
                clear_sub_directory_by_id(message)
                raise EntityTooLargeError(e.description)

    clear_sub_directory_by_id(message)


def send_audio(message, query, use_yandex, token, path, filename, order):
    if not use_yandex:
        try:
            bot.send_audio(message.chat.id, vk_audio.main(query, order), timeout=200)
        except ApiTelegramException as e:
            bot.reply_to(message, 'file is too large, max size is 50MB.\n Try to upload file on yandex disk')
            clear_sub_directory_by_id(message)
            raise EntityTooLargeError(e.description)
    else:
        yandex_disk.upload_file_to_yandex_disk(token, path, vk_audio.main(query, order), filename + '.mp3')
        clear_sub_directory_by_id(message)


def get_user(message):
    try:
        user = User.get(
            (User.telegram_id == message.chat.id)
        ).get()
    except User.DoesNotExist:
        user = User.create(
            telegram_id=message.chat.id,
            template=default_template
        ).get()

    return user


def get_duration(seconds):
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    return "%d:%02d:%02d" % (h, m, s)


@bot.message_handler(commands=['change_template'])
def change_template(message):
    user = get_user(message)

    msg = bot.reply_to(message, 'Your template:\n\n' + user.template + '\n\nprint new one to store it!')
    bot.register_next_step_handler(msg, save_new_template, user)


def save_new_template(message, user):
    user.template = message.text
    user.save()
    bot.reply_to(message, 'template changed successfully')


@bot.message_handler(commands=['help'])
def help(message):
    bot.reply_to(message, help_message)


@bot.message_handler(commands=['set_default_template'])
def change_template(message):
    user = get_user(message)
    user.template = default_template
    user.save()

    bot.reply_to(message, 'template changed successfully')


@bot.message_handler(regexp='^https*://')
def get_video_without_settings(message):
    with yt_dlp.YoutubeDL() as ydl:
        try:
            info_dict = ydl.extract_info(message.text, download=False)
            filename = 'files' + str(message.chat.id) + '/' + info_dict.get('title', None)
        except DownloadError:
            filename = 'files' + str(message.chat.id) + '/' + \
                f"{''.join(random.choice(string.ascii_lowercase) for i in range(10))}"

    download_video(filename, message.text, message)
    bot.send_video(message.chat.id, open(filename + '.mp4', 'rb'))


def get_audio_only(audio_only, is_cut, edited_filename, filename):
    audio_only_pattern = '^yes$'
    if re.match(audio_only_pattern, audio_only):
        if is_cut:
            file = edited_filename
        else:
            file = filename + '.mp4'

        audio_only_script = f"""ffmpeg -i {file} {filename + '.mp3'} """
        os.system(audio_only_script)
        return True

    return False


def get_cut_file(cut, filename, edited_filename, duration, message):
    if cut == '':
        return False

    time_pattern = '^\d{2}:\d{2}:\d{2} \d{2}:\d{2}:\d{2}$'
    from_to_string = cut.split()

    if not re.match(time_pattern, cut):
        bot.reply_to(message, 'cut time should be in the format "cut:00:00:00 00:00:00", leave empty "cut:" if you dont'
                              'want to cut file')
        raise CutFailedError('the given cut string is in the wrong format')

    if not from_to_string[0] < from_to_string[1]:
        bot.reply_to(message, 'first time period should be less than second')
        raise CutFailedError('first time period more than second')

    if not from_to_string[1] <= duration:
        bot.reply_to(message, 'second time segment is not included in the video')
        raise CutFailedError('second time period is not included in the video')

    if not from_to_string[0] < duration:
        bot.reply_to(message, 'first time segment is not included in the video')
        raise CutFailedError('first time period is not included in the video')

    cut_script = f"""ffmpeg -i {filename + '.mp4'} -ss {from_to_string[0]} -to {from_to_string[1]} -c copy {edited_filename} """
    os.system(cut_script)
    return True


def download_video(filename, link, message):
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
            raise IncorrectLinkError(f'link is incorrect: {link}')


def clear_sub_directory_by_id(message):
    directory = os.getcwd() + '/files/' + str(message.chat.id)
    for file in os.listdir(directory):
        os.remove(os.path.join(directory, file))


def get_settings(message):
    info_split = message.text.split('\n')
    settings = {}
    for setting in info_split:
        settings[setting.split(':', 1)[0]] = setting.split(':', 1)[1]

    return settings


if __name__ == '__main__':
    bot.infinity_polling(timeout=100, long_polling_timeout=100)
