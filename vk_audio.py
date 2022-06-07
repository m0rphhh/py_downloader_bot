import os
import vk_api
from vk_api.audio import VkAudio
import random
import string


def main(search, order):
    vk_session = vk_api.VkApi(os.getenv('VK_LOGIN'), os.getenv('VK_PASSWORD'))
    order = order - 1

    try:
        vk_session.auth()
    except vk_api.AuthError as error_msg:
        print(error_msg)
        return

    vkaudio = VkAudio(vk_session).search(q=search)
    i = 0

    for track in vkaudio:
        if i != order:
            i += 1
            continue

        ts_filename = f"{''.join(random.choice(string.ascii_lowercase) for i in range(10))}.ts"
        filename = f"{track.get('artist')} - {track.get('title')}.mp3"
        print('saving using streamlink')
        script_download = f"""streamlink --output {ts_filename} {track.get('url')} best"""
        os.system(script_download)
        script_convert = f"""ffmpeg -i {ts_filename} "{filename}" """
        os.system(script_convert)
        file = open(filename, 'rb')
        os.remove(ts_filename)
        os.remove(filename)
        return file
