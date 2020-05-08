import time
import locale
import json
import os
import cv2

ERROR = -1
WARNING = 2
INFO = 0
LOCALE = {}
with open("_locale.json", "r", encoding="utf8") as f:
    LOCALE = json.load(f)

LOCALE["__empty"] = {
    "ru": "",
    "en": ""
}

timestamp = lambda x: time.mktime(time.strptime(x[0], "%H:%M:%S")) + float("0." + x[1])


def props(cls):
    return [i for i in cls.__dict__.keys() if i[:1] != '_']


def get_local_str_util(key):
    lang = "ru"
    local_def = locale.getdefaultlocale()
    if len(local_def) and local_def[0]:
        sys_locale = local_def[0].split("_")[0]
        if sys_locale in ["en", "ru"]:
            lang = sys_locale

    if key in LOCALE.keys():
        if lang in LOCALE.get(key).keys():
            return LOCALE.get(key)[lang]

    return key


def create_log(text, log_type=INFO):
    str_log_type = {
        INFO: "INFO",
        ERROR: "ERROR",
        WARNING: "WARNING"
    }
    # timestr = time.strftime("%Y/%m/%d %H:%M:%S")
    log = ""
    if text:
        log = "{}: {}".format(str_log_type.get(log_type, INFO), text)
    return log


def get_video_fps(path):
    if isinstance(path, int):
        video = cv2.VideoCapture(path)
    else:
        if not os.path.isfile(path):
            return 0
        else:
            video = cv2.VideoCapture(path)

    fps = video.get(cv2.CAP_PROP_FPS)
    video.release()
    return fps
