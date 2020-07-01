#!/usr/bin/python
from kivy.app import App
from kivy.uix.screenmanager import Screen
from kivy.core.window import Window
from kivy.config import Config
from kivy.lang.builder import Builder
from kivy.config import ConfigParser
from kivy.graphics.texture import Texture
import os
import cv2
from helpers import get_local_str_util, create_log, get_video_fps, props, get_default_from_prev_session, set_default_from_prev_session, file_log, flex_get_locale, flex_get_user_locales
from kivy.uix.popup import Popup
from ctrls.loaddialog import LoadDialog
from ctrls.select_box import SelectBox

APP_DIR = os.path.dirname(__file__)
APP_DIR = os.path.dirname(APP_DIR)

out_put_path = os.path.join(APP_DIR, "user", "data", "output")
stimuli_path = os.path.join(APP_DIR, "user", "data", "output")

os.makedirs(out_put_path, exist_ok=True)
os.makedirs(stimuli_path, exist_ok=True)

widget = Builder.load_file(os.path.join(APP_DIR, "settings", "screens",  "settings_screen.kv"))

LOG_LEVELS = ['trace', 'debug', 'info', 'warning', 'error', 'critical']

class SettingsScreen(Screen):
    def build(self):
        return widget

    def start_all(self):
        language_options = [(i, self.select_box_on_select_lang) for i in flex_get_user_locales()]
        self.ids["select_language_ctrl"].set_options(language_options)

        log_levels_options = [(i, self.select_box_on_select_logs) for i in LOG_LEVELS]
        self.ids["select_log_level_ctrl"].set_options(log_levels_options)
        # frame = cv2.imread(os.path.join(APP_DIR, "assets", "icon-bg.png"))
        # buf = frame.tostring()
        # texture = Texture.create(size=(frame.shape[1], frame.shape[0]), colorfmt='bgr')

        # texture.blit_buffer(buf, colorfmt='bgr', bufferfmt='ubyte')

        # self.ids["bg_canvas"].texture = texture

        return True

    def select_box_on_select_lang(self):
        lang_chosen = self.ids["select_language_ctrl"].text
        if lang_chosen in flex_get_user_locales():
            self.set_default_from_prev_session("select_language_ctrl", lang_chosen)

    def select_box_on_select_logs(self):
        level_chosen = self.ids["select_log_level_ctrl"].text

        if level_chosen in LOG_LEVELS:
            self.set_default_from_prev_session("select_log_level_ctrl", level_chosen)

    def close_settings_screen(self):
        print("[INFO] closing settings screen")
        app = App.get_running_app()
        app.root.screen_manager.current = 'replay_screen'

    @staticmethod
    def get_user_dir(in_dirs=[]):
        st = os.path.join(APP_DIR, "user")

        for d in in_dirs:
            st = os.path.join(st, d)
    
        return st

    @staticmethod
    def get_app_dir(in_dirs=[]):
        st = APP_DIR
        for d in in_dirs:
            st = os.path.join(st, d)
    
        return st

    @staticmethod
    def get_default_from_prev_session(key, default='', cut = False):
        # loads a variable saved from the last session, directory, stimuli video for example
        val = get_default_from_prev_session(key, default)
        return val
    
    @staticmethod
    def set_default_from_prev_session(key, value):
        # set a variable key in this session. e.g the directory of stimuli video
        return set_default_from_prev_session(key, value)

    @staticmethod
    def get_local_str(key):
        # gets the localized string for literal text on the UI
        return get_local_str_util(key)

    @staticmethod
    def __tracker_app_log(text, log_label='app_log'):
        # give feedback to the user of what is happening behind the scenes
        app = App.get_running_app()
        try:
            app.tracker_app_log(text, log_label)
        except Exception as er:
            file_log("[ERROR] {}".format(er))

    def on_stop(self):
        pass
    
    # loading directory dialog
    def dismiss_popup(self):
        if self._popup is not None:
            self._popup.dismiss()

    def show_load_select_src_sessions_directory(self):
        start_dir = get_default_from_prev_session('lbl_src_sessions_directory',self.get_user_dir(["data","sessions"]))
        if not os.path.isdir(start_dir):
            start_dir = None

        content = LoadDialog(load=self.load_select_src_sessions_directory, cancel=self.dismiss_popup, start_dir=start_dir)

        self._popup = Popup(title=self.get_local_str("_select_src_sessions_directory"), content=content, size_hint=(0.9, 0.9))
        self._popup.open()

    def show_load_select_src_stimuli_directory(self):
        start_dir = get_default_from_prev_session('lbl_src_stimuli_directory',self.get_user_dir(["data","output"]))
        if not os.path.isdir(start_dir):
            start_dir = None

        content = LoadDialog(load=self.load_select_src_stimuli_directory, cancel=self.dismiss_popup, start_dir=start_dir)

        self._popup = Popup(title=self.get_local_str("_select_src_stimuli_directory"), content=content, size_hint=(0.9, 0.9))
        self._popup.open()

    def show_load_select_bin_directory(self):
        start_dir = get_default_from_prev_session('lbl_bin_directory',self.get_app_dir(["bin"]))
        if not os.path.isdir(start_dir):
            start_dir = None

        content = LoadDialog(load=self.load_select_bin_directory, cancel=self.dismiss_popup, start_dir=start_dir)

        self._popup = Popup(title=self.get_local_str("_select_bin_directory"), content=content, size_hint=(0.9, 0.9))
        self._popup.open()

    def show_load_select_logs_directory(self):
        start_dir = get_default_from_prev_session('lbl_logs_directory',self.get_user_dir(["logs"]))
        
        if not os.path.isdir(start_dir):
            start_dir = None
        content = LoadDialog(load=self.load_select_logs_directory, cancel=self.dismiss_popup, start_dir=start_dir)

        self._popup = Popup(title=self.get_local_str("_select_logs_directory"), content=content, size_hint=(0.9, 0.9))
        self._popup.open()

    def load_select_logs_directory(self, path, filename):
        if os.path.exists(path):
            if not os.path.isdir(path):
                path = os.path.dirname(path)

        self.ids['lbl_logs_directory'].text = path
        
        self.set_default_from_prev_session('lbl_logs_directory', path)
        self.set_default_from_prev_session('filechooser', path)
        
        self.dismiss_popup()

    def load_select_bin_directory(self, path, filename):
        if os.path.exists(path):
            if not os.path.isdir(path):
                path = os.path.dirname(path)

        self.ids['lbl_bin_directory'].text = path
        
        self.set_default_from_prev_session('lbl_bin_directory', path)
        self.set_default_from_prev_session('filechooser', path)
        
        self.dismiss_popup()

    def load_select_src_stimuli_directory(self, path, filename):
        if os.path.exists(path):
            if not os.path.isdir(path):
                path = os.path.dirname(path)

        self.ids['lbl_src_stimuli_directory'].text = path
        
        self.set_default_from_prev_session('lbl_src_stimuli_directory', path)
        self.set_default_from_prev_session('filechooser', path)
        
        self.dismiss_popup()
    
    def load_select_src_sessions_directory(self, path, filename):
        if os.path.exists(path):
            if not os.path.isdir(path):
                path = os.path.dirname(path)

        self.ids['lbl_src_sessions_directory'].text = path
        
        self.set_default_from_prev_session('lbl_src_sessions_directory', path)
        self.set_default_from_prev_session('filechooser', path)
        
        self.dismiss_popup()