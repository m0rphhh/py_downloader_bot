import os
import vk_api
from vk_api.audio import VkAudio
import random
import string
from decouple import config


def main(search):
    vk_session = vk_api.VkApi(config('VK_LOGIN'), config('VK_PASSWORD'))

    try:
        vk_session.auth()
    except vk_api.AuthError as error_msg:
        print(error_msg)
        return

    vkaudio = VkAudio(vk_session).search(q=search)

    for track in vkaudio:
        ts_filename = f"{''.join(random.choice(string.ascii_lowercase) for i in range(10))}.ts"
        filename = f"{track.get('artist')} - {track.get('title')}.mp3"
        print('saving using streamlink')
        script_download = f"""streamlink --output {ts_filename} {track.get('url')} best"""
        os.system(script_download)
        script_convert = f"""ffmpeg -i {ts_filename} "{filename}" """
        os.system(script_convert)
        return open(filename, 'rb')
