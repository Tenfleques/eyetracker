from kivy.uix.gridlayout import GridLayout
from kivy.lang.builder import Builder
import os

widget = Builder.load_file(os.path.join(os.path.dirname(__file__), "table.kv"))


class Table(GridLayout):

    def build(self):
        return widget
