#!/usr/bin/python
from kivy.config import Config
from kivy.core.window import Window
from helpers import get_local_str_util, create_log, get_video_fps, props, save_session_variables
from kivy.app import App
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition, SlideTransition
from kivy.clock import Clock

Config.set('graphics', 'kivy_clock', 'free_all')
Config.set('graphics', 'maxfps', 0)

Window.size = (1600, 800)

from screens.replay_screen import ReplayScreen
from screens.tracker_screen import TrackerScreen
from screens.generator_screen import GeneratorScreen

Window.set_icon('./assets/icon.png')


class GisApp(App):

    @staticmethod
    def get_local_str(key):
        # gets the localized string for literal text on the UI
        return get_local_str_util(key)

    def tracker_app_log(self, text, log_label='app_log'):
        log = create_log(text)
        if log_label in self.root.ids["info_bar"].ids:
            self.root.ids["info_bar"].log_text(log, log_label)
            return

        if log_label in self.root.ids:
            self.root.ids[log_label].text = log

    def on_start(self):
        print("[INFO] starting ")
        app = App.get_running_app()
        Clock.schedule_once(lambda dt: app.root.ids["replay_screen"].start_all())
        Clock.schedule_once(lambda dt: app.root.ids["generator_screen"].build())
        app.root.ids["screen_manager"].transition = FadeTransition()
        # app.root.screen_manager.current = 'replay_screen'
        Window.set_title(get_local_str_util('_appname'))

    def on_stop(self):
        app = App.get_running_app()
        app.root.ids["tracker_screen"].stop_all()
        app.root.ids["replay_screen"].stop_all()

        save_session_variables()


if __name__ == '__main__':
    GisApp().run()
