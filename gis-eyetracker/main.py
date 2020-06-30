#!/usr/bin/python
from kivy.config import Config
from kivy.core.window import Window
from helpers import get_local_str_util, create_log, get_video_fps, props, save_session_variables, file_log, get_default_from_prev_session, get_app_dir
from kivy.app import App
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition, SlideTransition
from kivy.clock import Clock, mainthread
from kivy.config import ConfigParser
import time 
from PIL import ImageGrab
import os
from threading import Thread


from screens.replay_screen import ReplayScreen
from screens.tracker_screen import TrackerScreen
from screens.generator_screen import GeneratorScreen
from screens.settings_screen import SettingsScreen
from screens.splash_screen import SplashScreen
from screens.cam_config_screen import CamConfigScreen
from ctrls.open_face_ctrl import OpenFaceController

Window.set_icon('./assets/icon.png')
Window.size = (600, 400)

APP_PATH = get_app_dir()

Config.set('graphics', 'kivy_clock', 'free_all')
Config.set('graphics', 'maxfps', 0)
Config.set('graphics', 'borderless', 1)

Config.set('kivy', 'desktop', 1)
Config.set('kivy', 'log_enable', 1)
Config.set('kivy', 'log_dir', get_default_from_prev_session('lbl_logs_directory', os.path.join(APP_PATH, 'user', 'logs')))
Config.set('kivy', 'log_level', get_default_from_prev_session('select_log_level_ctrl', 'debug'))
Config.set('kivy', 'window_icon', 'assets/icon.ico')



class GisApp(App):
    screen_buttons = [
        "btn_generator_screen",
        "btn_tracker_screen",
        "btn_replay_screen",
        "btn_settings_screen",
        "btn_cam_config_screen"
    ]
    processes = []

    @staticmethod
    def get_local_str(key):
        # gets the localized string for literal text on the UI
        return get_local_str_util(key)

    def update_active_screen(self):
        for btn in self.screen_buttons:
            self.root.ids[btn].background_color = (.9, .9, .9, 1)
        
        self.root.ids["btn_{}".format(self.root.screen_manager.current)].background_color = (.85, .85, .85, 1)

    def tracker_app_log(self, text, log_label='app_log', log_t=True):
        log = create_log(text,log_t=log_t)
        if log_label in self.root.ids["info_bar"].ids:
            self.root.ids["info_bar"].log_text(log, log_label)
            return

        if log_label in self.root.ids:
            self.root.ids[log_label].text = log

    @mainthread
    def start_main(self):
        app = App.get_running_app()
        Window.hide()
        app.root.screen_manager.current = 'generator_screen'
        Window.set_title(get_local_str_util('_appname'))
        Window.size = (1600, 800)
        Window.left = 100
        Window.top = 100
        app.root.ids["screen_nav"].height = 35
        Window.borderless = False
        Config.set('graphics', 'borderless', 'False')
        self.tracker_app_log("", log_t=False)
        Window.show()
        app.root.ids["screen_manager"].transition = FadeTransition()

    def init_all_screens(self):
        app = App.get_running_app()
        keys = [
            'generator_screen',
            'tracker_screen',
            'replay_screen',
            'settings_screen'
        ]
        for k in keys:
            app.root.ids[k].start_all()
        
        self.start_main()

    def on_start(self):
        app = App.get_running_app()
        self.tracker_app_log("[b]{} 2020 - {} [/b]".format(chr(0x00A9), time.strftime("%Y")), log_t=False)
        Clock.schedule_once(lambda dt: self.init_all_screens(), 5)
        
    def bg_open_face_process(self, cam_video, w, h):
        APP = get_default_from_prev_session('lbl_bin_directory', os.path.join(APP_PATH, "bin"))
        openface = OpenFaceController(APP, w, h)
        open_face_update = openface.proceed(cam_video)
        
        dir_literal = cam_video.split(os.sep)[-2]

        if open_face_update == 0:
            lcl_string = self.get_local_str("_open_face_process_finished")
            self.tracker_app_log("{} [{}]".format(lcl_string, dir_literal), "tracker_log")
        else:
            lcl_string = self.get_local_str("_open_face_process_error")
            self.tracker_app_log("{} [{}]".format(lcl_string, dir_literal), "tracker_log")
            file_log("[ERROR] an error from open face application occured {}".format(open_face_update))

    def process_open_face_video(self, output_dir):
        screen_grab = ImageGrab.grab()
        w, h = screen_grab.size
        cam_video = os.path.join(output_dir, "out-video.avi")
        dir_literal = output_dir.split(os.sep)[-1]
        
        lcl_string = self.get_local_str("_open_face_process_started")
        self.tracker_app_log("{} [{}]".format(lcl_string, dir_literal), "tracker_log")
        
        thr = Thread(target=self.bg_open_face_process, args=(cam_video, w, h))
        thr.start()
        self.processes.append(thr)

    def process_open_face_video_finished(self, output_dir):
        file_tmp = os.path.join(output_dir, "proc.log")
        status = -1

        if os.path.isfile(file_tmp):
            status = 0
        else:
            return status

        with open(file_tmp, 'r') as fp:
            text = fp.read()
            fp.close()

        if "finished" in text:
            status = 1
        
        return status
        
        
    def on_stop(self):
        app = App.get_running_app()
        app.root.ids["tracker_screen"].stop_all()
        app.root.ids["replay_screen"].stop_all()

        save_session_variables()
        for p in self.processes:
            p.join()


if __name__ == '__main__':
    GisApp().run()
