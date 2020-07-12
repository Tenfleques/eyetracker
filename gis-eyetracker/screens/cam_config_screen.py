from kivy.app import App
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.uix.screenmanager import Screen
import json
import os
from helpers import get_local_str_util, get_default_from_prev_session, set_default_from_prev_session, file_log

from ctrls.cam_config import CamConfig
from ctrls.multiple_cameras import MultipleCameras

APP_DIR = os.path.dirname(__file__)
APP_DIR = os.path.dirname(APP_DIR)

widget = Builder.load_file(os.path.join(APP_DIR, "settings", "screens",  "cam_config_screen.kv"))

class CamConfigScreen(Screen):
    def build(self):
        Clock.schedule_once(lambda dt: self.ids["multi_cams_config"].start_all(),2)
        return widget

    @staticmethod
    def get_local_str(key):
        # gets the localized string for literal text on the UI
        return get_local_str_util(key)
    
    @staticmethod
    def __tracker_app_log(text, log_label='camera_log'):
        # give feedback to the user of what is happening behind the scenes
        app = App.get_running_app()
        try:
            app.tracker_app_log(text, log_label)
        except Exception as er:
            file_log("[ERROR] {}".format(er))

    