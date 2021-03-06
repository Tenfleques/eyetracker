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
import json

from helpers import get_local_str_util, create_log, get_video_fps, props, get_default_from_prev_session, set_default_from_prev_session, file_log, flex_get_locale, flex_get_user_locales
from kivy.uix.popup import Popup
from ctrls.loaddialog import LoadDialog
from ctrls.select_box import SelectBox
from ctrls.update_ctrl import UpdateCtrl
from ctrls.dataset_ctrl import make_datasets_from_data_dir
from threading import Thread

APP_DIR = os.path.dirname(__file__)
APP_DIR = os.path.dirname(APP_DIR)

out_put_path = os.path.join(APP_DIR, "user", "data", "output")
stimuli_path = os.path.join(APP_DIR, "user", "data", "output")

os.makedirs(out_put_path, exist_ok=True)
os.makedirs(stimuli_path, exist_ok=True)

widget = Builder.load_file(os.path.join(APP_DIR, "settings", "screens",  "settings_screen.kv"))

LOG_LEVELS = ['trace', 'debug', 'info', 'warning', 'error', 'critical']

class SettingsScreen(Screen):
    update_ctrl = UpdateCtrl()
    processes = []

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

        # check for updates
        
        start_dir = get_default_from_prev_session('lbl_logs_directory',self.get_user_dir(["logs"]))
        self.set_default_from_prev_session('lbl_logs_directory', start_dir)
        start_dir = get_default_from_prev_session('lbl_bin_directory',self.get_app_dir(["bin"]))
        self.set_default_from_prev_session('lbl_bin_directory', start_dir)
        start_dir = get_default_from_prev_session('lbl_src_stimuli_directory',self.get_user_dir(["data","output"]))
        self.set_default_from_prev_session('lbl_src_stimuli_directory', start_dir)
        start_dir = get_default_from_prev_session('lbl_src_sessions_directory',self.get_user_dir(["data","sessions"]))
        self.set_default_from_prev_session('lbl_src_sessions_directory', start_dir)

        
        self.check_updates()
        return True

    def end_update_cb(self):
        self.__tracker_app_log(self.get_local_str("_update_finished"))
        self.ids["btn_update_ctrl"].disabled = False
        self.check_updates()

    def check_updates(self, component="main"):
        try:
            target=self.check_update_process
            if self.ids["btn_update_ctrl"].text == self.get_local_str("_update_now"):
                target=self.update_app
                component=self.end_update_cb

                self.ids["btn_update_ctrl"].disabled = True
                self.ids["btn_update_ctrl"].text = self.get_local_str("_updating")
                self.__tracker_app_log(self.get_local_str("_updating"))
            
            proc = Thread(target=target, args=(component,))
            proc.start()
            self.processes.append(proc)

        except Exception as err:
            print("[ERROR] error looking up updates")
            file_log("[ERROR] {}".format(err))

    def check_update_process(self, target="main"):
        res = self.update_ctrl.check_updates(target)
        if res == 0:
            # success we have an update
            details = self.update_ctrl.get_update_details()
            self.ids["btn_update_ctrl"].text = self.get_local_str("_update_now")
            self.ids["lbl_update_available"].text = "{} {}.{}".format(self.get_local_str("_update_available"), details.get("name", ""), details.get("version", ""))
            self.__tracker_app_log(self.ids["lbl_update_available"].text)
            return 0
        if res == 1:
            # already latest update
            self.__tracker_app_log(self.get_local_str("_latest_version"))
            self.ids["lbl_update_available"].text = ""
            self.ids["btn_update_ctrl"].text = self.get_local_str("_check_updates")
            return 0
        if res == -1:
            self.__tracker_app_log(self.get_local_str("_error_checking_update"))
            return -1

    def update_app(self, cb):
        try:
            self.update_ctrl.update_app(cb)
        except Exception as d_err:
            print("[ERROR] failed to download new update")
            file_log("[ERROR] {}".format(d_err))

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

    def export_sessions_directory_to_dataset(self):
        sessions_dir = get_default_from_prev_session('lbl_src_sessions_directory',self.get_user_dir(["data","sessions"]))

        proc = Thread(target=make_datasets_from_data_dir, args=(sessions_dir, self.sessions_export_cb))
        proc.start()
        self.processes.append(proc)

    def sessions_export_cb(self, **kwargs):
        session_exporting = kwargs.get("name", "")
        log_text = "{}: {}".format(self.get_local_str("_exporting_session_to_dataset"), session_exporting)

        current = kwargs.get("current", "")
        total = kwargs.get("total", "")
        progress = ""
        if current and total:
            progress = "{}/{}".format(current, total)
            self.ids["dataset_export_progress"].max = total
            self.ids["dataset_export_progress"].value = current

        self.ids["lbl_src_sessions_exporting"].text = "{} {}".format(log_text, progress)
        

        self.__tracker_app_log("{} {}".format(log_text, progress))

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
        file_log("[INFO] closing settings processes")
        for proc in self.processes:
            # join all other running processes
            proc.join()
        file_log("[INFO] closed all settings processes ")
    
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