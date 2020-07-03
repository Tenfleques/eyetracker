from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import Screen
import json
import os
from helpers import get_local_str_util, get_default_from_prev_session, set_default_from_prev_session, get_app_dir

APP_DIR = get_app_dir()

out_put_path = os.path.join(APP_DIR, "user", "configs", "camera")
os.makedirs(out_put_path, exist_ok=True)

widget = Builder.load_file(os.path.join(APP_DIR, "settings", "subscreens", "cam_config.kv"))

class CamConfig(Screen):
    def build(self):
        return widget

    @staticmethod
    def get_local_str(key):
        # gets the localized string for literal text on the UI
        return get_local_str_util(key)

    @staticmethod
    def get_default_from_prev_session(key, default=''):
        config_path = os.path.join(APP_DIR, "user", "configs", "camera", "cam_config.json")
        return get_default_from_prev_session(key, default, config_path=config_path)

    @staticmethod
    def get_scheme_image():
        return os.path.join(APP_DIR, "assets", "ui", "scheme.jpg")

    @staticmethod
    def __tracker_app_log(text, log_label='camera_log'):
        # give feedback to the user of what is happening behind the scenes
        app = App.get_running_app()
        try:
            app.tracker_app_log(text, log_label)
        except Exception as er:
            file_log("[ERROR] {}".format(er))

    def gen(self):
        d = {}
        vallist = ['width', 'height', 'x_offset', 'y_offset']
        for v in vallist:
            d[v] = int(self.ids[v].text)
        
        config_path = os.path.join(APP_DIR, "user", "configs", "camera", "cam_config.json")

        try:
            with open(config_path, 'w') as json_file:
                json.dump(d, json_file)
                json_file.close()

            success_str = self.get_local_str("_camera_configuration_written_successful")
            self.__tracker_app_log(success_str)
        except Exception as err:
            success_str = self.get_local_str("_camera_configuration_writing_unsuccessful")
            self.__tracker_app_log(success_str)