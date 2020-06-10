# -*- coding: utf-8 -*-
import time
import locale
import json
import os
import cv2
import filecmp
import logging
logging.basicConfig(filename='./logs/helpers.log',level=logging.DEBUG)

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

user_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "user")
prev_session_file_path = os.path.join(user_dir, "last_session.json")

# load user previous session settings
try:
    if not os.path.isdir(user_dir):
        os.makedirs(user_dir, exist_ok=True)
        SESSION_PREFS = {}
        with open(prev_session_file_path, "w") as session_f:
            session_f.write(json.dumps(SESSION_PREFS))
            session_f.close()
    else:
        with open(prev_session_file_path, "r") as session_f:
            SESSION_PREFS = json.load(session_f)
            session_f.close()
except IOError:
    SESSION_PREFS = {}
    print("[ERROR] i/o error")
except Exception as e:
    print(e)


def props(cls):
    return [i for i in cls.__dict__.keys() if i[:1] != '_']


def process_fps(video_frames):
    times = [float(i.to_dict()["timestamp"]) for i in video_frames]
    len_records = len(video_frames)

    if not len_records:
        return None, None, None

    info_1 = "[INFO] length of recorded frames {}\n\r".format(len_records)
    print(info_1)
    info_2 = ""
    diff_2 = max(times) - min(times)
    frame_rate_2 = None
    if diff_2:
        frame_rate_2 = len_records / diff_2
        info_2 = "[INFO] frame rate calculated by recorded frames times is {}\n\r".format(frame_rate_2)
        print(info_2)

    return info_1, info_2, frame_rate_2


def frame_processing(frame):
    """
        for a uniform frame processing while looping across frames
        so far doess nothing, TODO add some frame manipulation
    """
    return frame


def get_local_str_util(key):
    lang = "ru"
    #    local_def = locale.getdefaultlocale()
    #    if len(local_def) and local_def[0]:
    #        sys_locale = local_def[0].split("_")[0]
    #        if sys_locale in ["en", "ru"]:
    #            lang = sys_locale
    #
    if key in LOCALE.keys():
        if lang in LOCALE.get(key).keys():
            return LOCALE.get(key)[lang]

    return key


def get_default_from_prev_session(key, default=''):
    # loads a variable saved from the last session, directory, stimuli video for example
    if key in SESSION_PREFS.keys():
        return str(SESSION_PREFS.get(key))
    else:
        return str(default)


def set_default_from_prev_session(key, value):
    # set a variable key in this session. e.g the directory of stimuli video
    SESSION_PREFS[key] = value


def save_session_variables():
    with open(prev_session_file_path, "w") as session_f:
        session_f.write(json.dumps(SESSION_PREFS))
        session_f.close()


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


def check_talon_directory():
    talon_home = os.path.expanduser("~/.talon/user")
    filename = os.path.join(talon_home, "launcher.py")

    launcher_exists = os.path.exists(filename)
    launcher_isfile = os.path.isfile(filename)

    if not (launcher_exists and launcher_isfile):
        with open("./launcher.py", 'r') as src, open(filename, 'w') as dst:
            dst.write(src.read())
            dst.close()
            src.close()

    force_update = not filecmp.cmp("./launcher.py", filename, shallow=False)
    print("[INFO] forcing update? {}".format(force_update))
    # force_update = True

    if force_update:
        with open("./launcher.py", 'r') as src, open(filename, 'w') as dst:
            dst.write(src.read())
            dst.close()
            src.close()
