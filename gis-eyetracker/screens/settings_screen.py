#!/usr/bin/python
from kivy.app import App
from kivy.uix.screenmanager import Screen
from kivy.core.window import Window
from kivy.config import Config
from kivy.lang.builder import Builder
from kivy.config import ConfigParser
import os
from helpers import get_local_str_util, create_log, get_video_fps, props, get_default_from_prev_session, set_default_from_prev_session, file_log, flex_get_locale
from threading import Thread

p = os.path.dirname(__file__)
p = os.path.dirname(p)
widget = Builder.load_file(os.path.join(p, "settings", "screens",  "settings_screen.kv"))
config = ConfigParser()


class SettingsScreen(Screen):
    def build(self):
        return widget

    def start_all(self):
        lang = flex_get_locale()
        self.ids["settings_panel"].add_json_panel(self.get_local_str('_replay_settings'), config, os.path.join(p, "settings", "replay_settings-{}.json".format(lang)))

        return True

    def close_settings_screen(self):
        print("[INFO] closing settings screen")
        app = App.get_running_app()
        app.root.screen_manager.current = 'replay_screen'

    @staticmethod
    def get_default_from_prev_session(key, default='', cut = False):
        # loads a variable saved from the last session, directory, stimuli video for example
        val = get_default_from_prev_session(key, default)
        if cut:
           return val[:25] + " ... " + val[-40:]
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
        file_log("closing... settings screen")

    