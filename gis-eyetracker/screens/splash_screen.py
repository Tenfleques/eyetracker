#!/usr/bin/python
from kivy.app import App
from kivy.uix.screenmanager import Screen
from kivy.core.window import Window
from kivy.config import Config
from kivy.lang.builder import Builder
import os
import json
import time 

from helpers import get_local_str_util, create_log, get_video_fps, props, save_session_variables

p = os.path.dirname(__file__)
p = os.path.dirname(p)
widget = Builder.load_file(os.path.join(p, "settings", "screens", "splash_screen.kv"))


class SplashScreen(Screen):
    def build(self):
        return widget
    
    def get_appname(self):
        return get_local_str_util("_appname")

    def get_authors(self):
        authors = []
        with open(os.path.join(p, "assets/authors.json"), "r" ) as fp:
            authors = json.load(fp)
            fp.close()

        authors_str = ""
        for i in authors:
            authors_str += '''[b]{}[/b] \n [i]{} [i] \n\n'''.format(i.get("name", ""), i.get("company", ""))

        return authors_str

    @staticmethod 
    def get_local_str(key):
        return get_local_str_util(key)
