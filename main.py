#!/usr/bin/python
from kivy.app import App

from kivy.factory import Factory

from kivy.core.window import Window
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition, SlideTransition

from kivy.config import Config
from helpers import get_local_str_util, create_log, get_video_fps, props
import os
from kivy.clock import Clock

Config.set('graphics', 'kivy_clock', 'free_all')
Config.set('graphics', 'maxfps', 0)

Window.size = (1200, 800)
Window.clearcolor = (1, 1, 1, 1)

Window.set_title(get_local_str_util('_appname'))

# Window.set_icon('./assets/icon.png')

from components.loaddialog import LoadDialog
from replay_screen import ReplayScreen
from tracker_screen import TrackerScreen

class TestApp(App):
    
    def on_start(self):
        print("[INFO] starting ")
        app = App.get_running_app()
        app.root.ids["replay_screen"].start_all()
        app.root.ids["screen_manager"].transition = FadeTransition()

    def on_stop(self):
        app = App.get_running_app()
        app.root.ids["tracker_screen"].stop_all()
        app.root.ids["replay_screen"].stop_all()

        # app.root.stop_all()

        # with open(prev_session_file_path, "w") as session_f:
        #     session_f.write(json.dumps(SESSION_PREFS))
        #     session_f.close()
        # print("closing...")

if __name__ == '__main__':
    TestApp().run()
