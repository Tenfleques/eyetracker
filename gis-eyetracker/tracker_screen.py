#!/usr/bin/python
from kivy.app import App
from kivy.uix.screenmanager import Screen

from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button

from kivy.uix.popup import Popup
import json
import time
from threading import Thread
from helpers import get_local_str_util, create_log, get_video_fps, get_default_from_prev_session, set_default_from_prev_session, process_fps

from process_result import gaze_stimuli

from kivy.lang.builder import Builder
import os

from camera_feed_ctrl import CameraFeedCtrl
from tracker_ctrl import TrackerCtrl
from loaddialog import LoadDialog
from video_feed_ctrl import VideoCanvas
from table import Table
from floatInput import FloatInput
from infobar import InfoBar
from kivy.core.window import Window
from kivy.clock import Clock


import logging
logging.basicConfig(filename='~/logs/tracker_screen.log',level=logging.DEBUG)

import platform
from collections import deque
from PIL import ImageGrab
from kivy.config import Config

Config.set('graphics', 'kivy_clock', 'free_all')
Config.set('graphics', 'maxfps', 0)

widget = Builder.load_file(os.path.join(os.path.dirname(__file__), "tracker_screen.kv"))


class TrackerScreen(Screen):
    tracker_ctrl = None
    camera_feed_ctrl = CameraFeedCtrl()
    video_feed_ctrl = None
    session_timeline = None
    processes = []
    video_frame_shape = []

    video_frames = deque()
    video_frame_index = 0
    video_interval = None

    session_name = None
    _popup = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if platform.system() == 'Darwin':
            print("[INFO] Running on Mac OS")

        Clock.schedule_once(lambda dt: self.ids["video_canvas"].on_start())

    def stop_all(self):
        print("[INFO] closing processes and devices")
        # emergency close
        self.stop(True)

        if self.tracker_ctrl is not None:
            # the tracker connection
            self.tracker_ctrl.kill()
        for p in self.processes:
            # join all other running processes
            p.join()
        print("[INFO] closed all processes and devices ")

    @staticmethod
    def get_default_from_prev_session(key, default=''):
        # loads a variable saved from the last session, directory, stimuli video for example
        return get_default_from_prev_session(key, default)

    @staticmethod
    def set_default_from_prev_session(key, value):
        # set a variable key in this session. e.g the directory of stimuli video
        return set_default_from_prev_session(key, value)

    @staticmethod
    def get_local_str(key):
        # gets the localized string for literal text on the UI
        return get_local_str_util(key)

    def save_dir_ready(self):
        lbl_output_dir = self.ids['lbl_output_dir']

        # check the directory in the computer's filesystem
        ready = os.path.isdir(lbl_output_dir.text)
        # directory doesn't exist, scream for attention
        if not ready:
            lbl_output_dir.color = (1, 0, 0, 1) # red scream
            self.__tracker_app_log(self.get_local_str("_directory_not_selected"))
        else:
            lbl_output_dir.color = (0, 0, 0, 1)

        return ready

    def __get_session_directory(self):
        # check if directory even exists
        if not self.save_dir_ready():
            return None
        # creates path from session name and chosen catalog
        return os.path.join(self.ids['lbl_output_dir'].text, self.session_name)

    def stimuli_video_ready(self):
        ready = False
        # checks if video path is a file, if it's even a video file
        if get_video_fps(self.ids['lbl_src_video'].text):
            return True

        self.__tracker_app_log(self.get_local_str("_load_stimuli_video"))

        return ready

    @staticmethod
    def __tracker_app_log(text, log_label='app_log'):
        # give feedback to the user of what is happening behind the scenes
        app = App.get_running_app()
        try:
            app.tracker_app_log(text, log_label)
        except Exception as er:
            print("[ERROR] {}".format(er))

    def btn_play_click(self):
        """
        connects to the camera, video, tracker adapters
        runs till stop or end of stimuli video.
        :return:
        """

        if self.video_feed_ctrl is None:
            self.video_feed_ctrl = self.ids["video_canvas"]
        # if playing stop
        if self.video_feed_ctrl.is_playing():
            # emergency close
            self.stop(True)
            return

        # can't run session if video stimuli not ready can we?
        if not self.stimuli_video_ready():
            return

        # create new session
        self.session_name = "exp-{}".format(time.strftime("%Y-%m-%d_%H-%M-%S"))

        # get new session dir
        output_dir = self.__get_session_directory()
        if output_dir is None:
            return
        # create the new session dir
        os.makedirs(output_dir, exist_ok=True)

        # update window to have name of session
        Window.set_title("{} [{}]".format(get_local_str_util('_appname'), self.session_name))
        # fires up camera
        camera_up = self.camera_feed_ctrl.start(output_path=output_dir,
              camera_index=0, save_images=False)

        # cancel everything if camera failed to start
        if not camera_up:
            self.__tracker_app_log(self.get_local_str("_problem_waiting_camera"))
            return

        # toggle play button to stop
        self.ids["btn_play"].text = self.get_local_str("_stop")
        # get path to video
        video_src = self.ids['lbl_src_video'].text
        # get the desired FPS
        fps = float(self.ids['txt_box_video_rate'].text)
        started = self.video_feed_ctrl.start(video_src, fps, end_cb=self.stop)

        print("[INFO] started video player {} ".format(started))
        if self.tracker_ctrl is None:
            self.tracker_ctrl = TrackerCtrl()
        self.tracker_ctrl.start()

    def set_button_play_start(self):
        self.ids["btn_play"].text = self.get_local_str("_start")

    def stop(self, emergency=None):
        process_data = True
        # stop camera feed
        if self.camera_feed_ctrl is not None:
            process_data = process_data and self.camera_feed_ctrl.get_camera_is_up()
            self.camera_feed_ctrl.stop()
        # stop tracker feed
        if self.tracker_ctrl is not None:
            process_data = process_data and self.tracker_ctrl.get_is_up()
            self.tracker_ctrl.stop()
        # stop video capture feed and callback toggle play button ready for next experiment
        if self.video_feed_ctrl is not None and emergency:
            process_data = process_data and self.video_feed_ctrl.is_playing()
            self.video_feed_ctrl.stop()

        if process_data:
            self.__after_recording()

        self.set_button_play_start()

        # switch view to the results while video is processed
        # self.ids["tabbed_main_view"].switch_to(self.ids["tabbed_timeline_item"], do_scroll=True)

    def __after_recording(self):
        try:
            self.tracker_ctrl.stop()
            output_dir = self.__get_session_directory()
            tracker_json_path = os.path.join(output_dir, "tracker.json")
            video_json_path = os.path.join(output_dir, "video_camera.json")

            tracker_meta_path = os.path.join(output_dir, "tracker-meta.json")
            tracker_meta = self.tracker_ctrl.get_meta_json()

            # save the session meta data
            with open(tracker_meta_path, "w") as f:
                f.write(tracker_meta)
                f.close()
            # save the screen dimension and bg
            screen_grab = ImageGrab.grab()
            screen_grab_path = os.path.join(output_dir, "screen.png")
            screen_grab.save(screen_grab_path, "PNG")
            # tracker_json = self.tracker_ctrl.get_json()
            # video_json = self.video_feed_ctrl.get_json()
            # camera_json = self.camera_feed_ctrl.get_json()

            # get actual FPS details for stimuli video
            info_1, info_2, self.actual_video_stimuli_fps = process_fps(self.video_feed_ctrl.get_frames())

            # log the actual video FPS
            if self.actual_video_stimuli_fps:
                lcl_string_fps = self.get_local_str("_actual_video_fps") + ": {:.4} ".format(self.actual_video_stimuli_fps)

                self.__tracker_app_log(lcl_string_fps, "stimuli_video_log")
            # get actual FPS details for camera
            log_1, log_2, camera_frame_rate = process_fps(self.camera_feed_ctrl.get_frames())
            # log actual camera FPS
            if camera_frame_rate:
                lcl_string_fps = self.get_local_str("_factual_camera_fps") + ": {:.4} ".format(camera_frame_rate)

                self.__tracker_app_log(lcl_string_fps, "camera_log")

            # save the tracker recording file
            self.tracker_ctrl.save_json(tracker_json_path)

            # save the video-camera recording file
            self.save_json(video_json_path)

            p = Thread(target=self.load_session_timeline, args=(tracker_json_path,
                                                                video_json_path, False, False))
            p.start()

            self.processes.append(p)
        except Exception as ex:
            print("[ERROR] an error occurred {}{}    ".format(ex, time.strftime("%H:%M:%S")))

    def load_session_timeline(self, tracker_json_path, video_json_path, timeline_exist=False, process_video=False):
        print("[INFO] started to process the timeline {}    ".format(time.strftime("%H:%M:%S")))

        lcl_string = self.get_local_str("_preparing_session_timeline")
        self.__tracker_app_log(lcl_string)
        selfie_video_path = os.path.join(self.ids['lbl_output_dir'].text,
                                         "out-video.avi")
        lcl_session_prep_finished_str = self.get_local_str("_session_timeline_ready")

        self.session_timeline = gaze_stimuli(tracker_json_path,
                                             video_json_path,
                                             self.ids['lbl_src_video'].text,
                                             selfie_video_path=selfie_video_path,
                                             timeline_exist=timeline_exist, process_video=process_video,
                                             session_timeline_cb=lambda sess_data:
                                             self.__tracker_app_log(lcl_session_prep_finished_str))

    def get_json(self):
        obj = {
                "camera": [i.to_dict() for i in self.camera_feed_ctrl.get_frames()],
                "video": [i.to_dict() for i in self.video_feed_ctrl.get_frames()]
        }
        return obj

    def save_json(self, path="./results.json"):
        with open(path, "w") as f:
            f.write(json.dumps(self.get_json()))
            f.close()

    # loading directory dialog
    def dismiss_popup(self):
        self._popup.dismiss()

    def show_load(self):
        try:
            content = LoadDialog(load=self.load, cancel=self.dismiss_popup)
            self._popup = Popup(title=self.get_local_str("_select_directory"), content=content, size_hint=(0.9, 0.9))
            self._popup.open()
        except Exception as err:
            print(err)

    # loading video file dialog
    def show_load_video(self):
        try:
            content = LoadDialog(load=self.load_video, cancel=self.dismiss_popup)
            self._popup = Popup(title=self.get_local_str("_select_src_video"), content=content, size_hint=(0.9, 0.9))
            self._popup.open()
        except Exception as err:
            print(err)

    def load_video(self, path, filenames):
        self.set_default_from_prev_session('filechooser', path)
        if len(filenames):
            if not filenames[0] == path:
                video_path = os.path.join(path, filenames[0])
                this_fps = get_video_fps(video_path)
                self.ids["txt_box_video_rate"].text = str(this_fps)
                self.set_default_from_prev_session("txt_box_video_rate", this_fps)
                self.ids['lbl_src_video'].text = video_path
                self.set_default_from_prev_session("lbl_src_video", video_path)

        self.dismiss_popup()

    def load(self, path, filename):
        lbl_output_dir = self.ids['lbl_output_dir']
        lbl_output_dir.text = path
        self.set_default_from_prev_session('lbl_output_dir', path)
        self.set_default_from_prev_session('filechooser', path)
        self.dismiss_popup()

        self.save_dir_ready()

