import yadisk
from yadisk.exceptions import PathNotFoundError, ParentNotFoundError


def upload_file_to_yandex_disk(token, path, file, filename):
    disk = yadisk.YaDisk(token=token)
    try:
        list(disk.listdir(path))
    except (PathNotFoundError, ParentNotFoundError):
        disk.mkdir(path)

    disk.upload(file, path + '/' + filename)


def check_disk(token):
    disk = yadisk.YaDisk(token=token)
    return disk.check_token()
