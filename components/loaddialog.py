from kivy.uix.floatlayout import FloatLayout
from kivy.properties import ObjectProperty
from kivy.lang.builder import Builder
import os

widget = Builder.load_file(os.path.join(os.path.dirname(__file__), "loaddialog.kv"))


class LoadDialog(FloatLayout):
    load = ObjectProperty(None)
    cancel = ObjectProperty(None)
    get_default_from_prev_session = ObjectProperty(None)
    get_local_str = ObjectProperty(None)

    def build(self):
        return widget
