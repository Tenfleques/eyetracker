#:kivy 1.1.0
from kivy.uix.anchorlayout import AnchorLayout
from kivy.lang.builder import Builder
import os
from kivy.core.window import Window

p = os.path.dirname(__file__)
p = os.path.dirname(p)
widget = Builder.load_file(os.path.join(p, "settings", "screens",  "infobar.kv"))


class InfoBar(AnchorLayout):
    def build(self):
        return widget

    def log_text(self, log, log_label):
        self.ids[log_label].text = log
