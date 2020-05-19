#:kivy 1.1.0
from kivy.uix.anchorlayout import AnchorLayout
from kivy.lang.builder import Builder
import os

widget = Builder.load_file(os.path.join(os.path.dirname(__file__), "infobar.kv"))


class InfoBar(AnchorLayout):
    def build(self):
        return widget

    def log_text(self, log, log_label):
        self.ids[log_label].text = log
