# -*- coding: utf-8 -*-
import time
import locale
import json
import os
import cv2
import filecmp
from PIL import Image
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas

ERROR = -1
WARNING = 2
INFO = 0
LOCALE = {}
with open("_locale.json", "r", encoding="utf8") as f:
    LOCALE = json.load(f)

# LOCALE["__empty"] = {
#     "ru": "",
#     "en": ""
# }

# timestamp = lambda x: time.mktime(time.strptime(x[0], "%H:%M:%S")) + float("0." + x[1])

p = os.path.dirname(__file__)
p = os.path.dirname(p)

user_dir = os.path.join(p, "user")

prev_session_file_path = os.path.join(user_dir, "last_session.json")
log_dir = os.path.join(user_dir, "logs")
os.makedirs(log_dir, exist_ok=True)

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

def recurse_directory_files(src, depth=0, max_depth=2):
    all_files = os.listdir(src)
    files = []
    folders = []
    for i in all_files:
        full_path = os.path.join(os.path.abspath(src), i)

        if os.path.isfile(full_path):
            files.append(full_path)
        else:
            if depth < max_depth:
                files += recurse_directory_files(full_path, depth+1, max_depth)

    return files 


def file_log(log_string):
    timestr = time.strftime("%H:%M:%S")
    logfilename = time.strftime("%Y-%m-%d")
    
    log_string = "{} {} {}".format(timestr, log_string, os.linesep)

    log_file = os.path.join(log_dir, "{}.log".format(logfilename))
    with open(log_file, "a") as logfp:
        logfp.write(log_string)
        logfp.close()
    return


def fig2img ( fig ):
    """
    @brief Convert a Matplotlib figure to a PIL Image in RGBA format and return it
    @param fig a matplotlib figure
    @return a Python Imaging Library ( PIL ) image
    """
    # put the figure pixmap into a numpy array
    buf = fig2data ( fig )
    w, h, d = buf.shape
    return Image.fromstring( "RGBA", ( w ,h ), buf.tostring( ) )


def fig2data ( fig ):
    """
    @brief Convert a Matplotlib figure to a 4D numpy array with RGBA channels and return it
    @param fig a matplotlib figure
    @return a numpy 3D array of RGBA values
    """
    # draw the renderer
    canvas = FigureCanvas(fig)
    canvas.draw()
 
    # Get the RGBA buffer from the figure
    w,h = canvas.get_width_height()
    buf = numpy.frombuffer ( fig.canvas.tostring_argb(), dtype=numpy.uint8 )
    buf.shape = ( w, h, 4 )
 
    # canvas.tostring_argb give pixmap in ARGB mode. Roll the ALPHA channel to have it in RGBA mode
    buf = numpy.roll ( buf, 3, axis = 2 )
    return buf


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

def flex_get_user_locales():
    local_key = list(LOCALE.keys())[0]
    return LOCALE[local_key].keys()

def flex_get_locale():
    lang = "ru"
    available_langs = flex_get_user_locales()
    user_preffered_lang = get_default_from_prev_session('select_language_ctrl', default='ru')

    if user_preffered_lang in available_langs:
        return user_preffered_lang

    local_def = locale.getdefaultlocale()
    if len(local_def) and local_def[0]:
        sys_locale = local_def[0].split("_")[0]
        if sys_locale in available_langs:
            lang = sys_locale
    
    return lang

def get_local_str_util(key):
    lang = flex_get_locale()

    if key in LOCALE.keys():
        if lang in LOCALE.get(key).keys():
            return LOCALE.get(key)[lang]

    return key


def get_default_from_prev_session(key, default='', config_path=None):
    # loads a variable saved from the last session
    data_obj = SESSION_PREFS
    if config_path is not None:
        if os.path.isfile(config_path):
            with open(config_path, "r") as session_f:
                data_obj = json.load(session_f)
                session_f.close()

    if key in data_obj.keys():
        return str(data_obj.get(key))
    else:
        return str(default)


def set_default_from_prev_session(key, value):
    # set a variable key in this session. e.g the directory of stimuli video
    SESSION_PREFS[key] = value
    save_session_variables()


def save_session_variables():
    with open(prev_session_file_path, "w") as session_f:
        session_f.write(json.dumps(SESSION_PREFS))
        session_f.close()


def create_log(text, log_type=INFO, log_t=True):
    str_log_type = {
        INFO: "INFO",
        ERROR: "ERROR",
        WARNING: "WARNING"
    }
    # timestr = time.strftime("%Y/%m/%d %H:%M:%S")
    log = ""
    if text:
        if log_t:
            log = "{}: {}".format(str_log_type.get(log_type, INFO), text)
        else:
            log = "{}".format(text)
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

file_log("="*80 + "{}".format(time.strftime("%H:%M:%S")))