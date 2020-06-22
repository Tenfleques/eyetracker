from kivy.uix.floatlayout import FloatLayout
from kivy.properties import ObjectProperty
from kivy.lang.builder import Builder
from helpers import get_local_str_util, get_default_from_prev_session, set_default_from_prev_session
import os

p = os.path.dirname(__file__)
p = os.path.dirname(p)
widget = Builder.load_file(os.path.join(p, "settings", "screens",  "loaddialog.kv"))


class LoadDialog(FloatLayout):
    load = ObjectProperty(None)
    cancel = ObjectProperty(None)

    @staticmethod
    def get_default_from_prev_session(key, default=''):
        # loads a variable saved from the last session, directory, stimuli video for example
        return get_default_from_prev_session(key, default)

    @staticmethod
    def set_default_from_prev_session(key, value):
        # set a variable key in this session. e.g the directory of stimuli video
        return set_default_from_prev_session(key, value)
    
    @staticmethod
    def get_user_dir():
        return os.path.join(p,"user/data")

    @staticmethod
    def get_local_str(key):
        # gets the localized string for literal text on the UI
        return get_local_str_util(key)

    def on_path_validate(self,ctrl):
        if os.path.exists(ctrl.text):
            self.ids["filechooser"].path = ctrl.text

    def build(self):
        return widget
