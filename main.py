#!/usr/bin/python
from kivy.app import App

from kivy.factory import Factory
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from floatInput import FloatInput
from kivy.uix.image import Image
from kivy.graphics.texture import Texture

from kivy.properties import ObjectProperty
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.clock import Clock, mainthread
import json
from threading import Thread
import time

from eye_utilities.helpers import get_local_str_util, create_log, get_video_fps
from process_result import gaze_stimuli, create_timeline

import os
from io import StringIO
import sys

from tracker_ctrl import TrackerCtrl
from video_feed_ctrl import VideoFeedCtrl
from kivy.core.window import Window

Window.size = (1200, 800)
Window.clearcolor = (1, 1, 1, 1)

APP_THREADS = {}

# load user previous session settings
try:
    user_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "user")
    prev_session_file_path = os.path.join(user_dir, "last_session.json")

    if not os.path.isdir(user_dir):
        os.makedirs(user_dir, exist_ok=True)
        SESSION_PREFS = {}
        with open(prev_session_file_path, "w") as session_f:
            session_f.write(json.dumps(SESSION_PREFS))
            session_f.close()
    else:
        with open(prev_session_file_path, "r") as session_f:
            SESSION_PREFS = json.load(session_f)
            session_f.close()
except IOError:
    SESSION_PREFS = {}
    print("[ERROR] i/o error")
except Exception as e:
    print(e)


class LoadDialog(FloatLayout):
    load = ObjectProperty(None)
    cancel = ObjectProperty(None)
    get_local_str = ObjectProperty(None)


class Root(FloatLayout):
    session_recording = False
    video_ctrl = None
    tracker_ctrl = None
    session_timeline = None
    session_meta = {
        "camera": {},
        "video": {},
        "tracker": {
            "output_file": "",
            "dict": {}
        }
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def init_listeners(self):
        pass

    @staticmethod
    def get_default_from_prev_session(key, default=''):
        if key in SESSION_PREFS.keys():
            return SESSION_PREFS.get(key)
        else:
            return default

    @staticmethod
    def set_default_from_prev_session(key, value):
        SESSION_PREFS[key] = value

    @staticmethod
    def get_local_str(key):
        return get_local_str_util(key)

    @staticmethod
    def get_video_fps(path):
        return str(get_video_fps(path))

    def save_dir_ready(self):
        lbl_output_dir = self.ids['lbl_output_dir']

        ready = os.path.isdir(lbl_output_dir.text)

        if not ready:
            lbl_output_dir.color = (1, 0, 0, 1)
            self.__tracker_app_log(self.get_local_str("_directory_not_selected"))
        else:
            lbl_output_dir.color = (0, 0, 0, 1)

        return ready

    def stimuli_video_ready(self):
        ready = False
        if get_video_fps(self.ids['lbl_src_video'].text):
            return True

        self.__tracker_app_log(self.get_local_str("_load_stimuli_video"))
        return ready

    def __tracker_app_log(self, text, log_label='app_log'):
        log = create_log(text)
        print(log)
        self.ids[log_label].text = log

    def btn_play_click(self):
        """
        connects to the camera, video, tracker adapters
        runs till stop or end of stimuli video.
        :return:
        """
        if not self.save_dir_ready():
            return

        if not self.stimuli_video_ready():
            return

        old_stdout = sys.stdout
        sys.stdout = str_stdout = StringIO()
        self.__run_session()
        self.ids['gaze_log'].text = "\n".join(str_stdout.getvalue().split("   "))

        sys.stdout = old_stdout

    def __run_session(self):
        if self.session_recording:
            # stop the services
            self.session_recording = False
            self.ids['btn_capture'].text = self.get_local_str("_start")
            # self.ids['btn_capture'].text
            if self.video_ctrl is not None:
                self.video_ctrl.stop()
            if self.tracker_ctrl is not None:
                self.tracker_ctrl.stop()

        else:
            # start the services
            self.session_recording = True
            self.ids['btn_capture'].text = self.get_local_str("_stop")
            # get stdout

            if self.tracker_ctrl is None:
                self.tracker_ctrl = TrackerCtrl()
                self.tracker_ctrl.start()
            else:
                self.tracker_ctrl.start()

            if self.video_ctrl is None:
                self.video_ctrl = VideoFeedCtrl()
                finished = self.video_ctrl.start(self.ids['lbl_src_video'].text,
                                                 self.ids['lbl_output_dir'].text,
                                                 video_fps=float(self.ids['txt_box_video_rate'].text),
                                                 camera_fps=float(self.ids['txt_box_camera_rate'].text),
                                                 preprocess=self.ids['chkbx_preprocess_video'].active,
                                                 save_images=False)
            else:
                self.video_ctrl.stop()
                finished = self.video_ctrl.start(self.ids['lbl_src_video'].text,
                                                 self.ids['lbl_output_dir'].text,
                                                 video_fps=float(self.ids['txt_box_video_rate'].text),
                                                 camera_fps=float(self.ids['txt_box_camera_rate'].text),
                                                 preprocess=self.ids['chkbx_preprocess_video'].active,
                                                 save_images=False)
            if finished:
                self.video_ctrl.stop()
                try:
                    self.tracker_ctrl.stop()
                    tracker_json_path = os.path.join(self.ids['lbl_output_dir'].text, "tracker.json")
                    video_json_path = os.path.join(self.ids['lbl_output_dir'].text, "video_camera.json")

                    self.tracker_ctrl.save_json(tracker_json_path)
                    self.video_ctrl.save_json(video_json_path)
                    APP_THREADS["timeline_thread"] = Thread(target=self.load_session_timeline,
                                                            args=(tracker_json_path, video_json_path))
                    APP_THREADS["timeline_thread"].start()
                    self.session_meta["tracker"]["output_file"] = tracker_json_path
                except Exception as e:
                    print("[ERROR] a possible segmentation error from stopping the tracker {}{}    "
                          .format(e, time.strftime("%H:%M:%S")))
                    del self.tracker_ctrl
                    self.tracker_ctrl = None

                self.ids['btn_capture'].text = self.get_local_str("_start")

                lcl_string_fps = self.get_local_str("_requested_fps") + ": {} ".format(
                    self.video_ctrl.get_video_meta("requested_fps"))
                lcl_string_fps += self.get_local_str("_factual_fps") + ": {} ".format(
                    self.video_ctrl.get_video_meta("factual_fps"))

                self.__tracker_app_log(lcl_string_fps, "stimuli_video_log")

                lcl_string_fps = self.get_local_str("_requested_fps") + ": {} ".format(
                    self.video_ctrl.get_camera_meta("requested_fps"))
                lcl_string_fps += self.get_local_str("_factual_fps") + ": {} ".format(
                    self.video_ctrl.get_camera_meta("factual_fps"))

                self.__tracker_app_log(lcl_string_fps, "camera_log")

                lcl_string = self.get_local_str("_demonstration_preparing")
                self.__tracker_app_log(lcl_string)

    def load_session_timeline(self, tracker_json_path, video_json_path):
        print("[INFO] started to process the timeline {}    ".format(time.strftime("%H:%M:%S")))
        lcl_string = self.get_local_str("_preparing_session_timeline")
        self.__tracker_app_log(lcl_string)
        self.session_timeline = gaze_stimuli(tracker_json_path,
                                             video_json_path,
                                             self.ids['lbl_src_video'].text,
                                             selfie_video_path=os.path.join(self.ids['lbl_output_dir'].text,
                                                                            "out-video.avi"),
                                             video_fps=float(self.ids['txt_box_video_rate'].text))

        lcl_string = self.get_local_str("_session_timeline_ready")
        self.__tracker_app_log(lcl_string)

    def load_session_results(self):
        k = 0

        if self.session_timeline is None:
            timeline_path = None
            for fl in os.listdir(self.ids['lbl_output_dir'].text):
                if "-timeline.json" in fl:
                    timeline_path = fl
                    break
            if timeline_path is not None:
                timeline_path = os.path.join(self.ids['lbl_output_dir'].text, timeline_path)
                with open(timeline_path, "r") as fp:
                    self.session_timeline = json.load(fp)
            else:
                return

        if self.session_timeline is None:
            return

        self.ids["view_stage"].bind(minimum_height=self.ids["view_stage"].setter('height'))

        bg_color = ((), ())
        for key, record in self.session_timeline.items():
            gaze = "-"
            cam = "-"
            vid = "-"
            if record["gaze"] is not None:
                gaze = "({:.4}, {:.4}) ".format(record["gaze"].get("x", "-"), record["gaze"].get("y", "-"))
            if record["camera"] is not None:
                cam = record["camera"].get("frame_id", "-")
            if record["video"] is not None:
                vid = record["video"].get("frame_id", "-")

            row = GridLayout(size_hint_y=None, height=50, cols=4)
            l_ts = Label(text="{}".format(key), font_size='12sp', color=(0, 0, 0, 1))
            row.add_widget(l_ts)

            l_gz = Label(text=gaze, font_size='12sp', color=(0, 0, 0, 1))
            row.add_widget(l_gz)

            l_cam = Label(text=str(cam), font_size='12sp', color=(0, 0, 0, 1))
            row.add_widget(l_cam)

            l_v = Label(text=str(vid), font_size='12sp', color=(0, 0, 0, 1))
            row.add_widget(l_v)

            self.ids["view_stage"].add_widget(row)
            k += 1

    def result_video_ready(self, path=None):
        if path is None:
            lcl_string = self.get_local_str("_session_video_not_ready")
            self.__tracker_app_log(lcl_string)
            return False

        if not os.path.isfile(path):
            lcl_string = self.get_local_str("_session_video_not_ready")
            self.__tracker_app_log(lcl_string)
            return False

        return True

    def btn_replay_click(self):
        """
        replays the recent recorded session
        :return:
        """
        video_path = os.path.join(self.ids['lbl_output_dir'].text, 'out-video-demonstration.avi')

        if not self.result_video_ready(video_path):
            return

        APP_THREADS["session_timeline_thread"] = Thread(target=self.load_session_results)
        APP_THREADS["session_timeline_thread"].start()

        if self.video_ctrl is None:
            self.video_ctrl = VideoFeedCtrl()

        self.video_ctrl.play_video(video_path, video_fps=1000)
        APP_THREADS["session_timeline_thread"].join()

    def btn_preprocess_video_click(self):
        # load frames to memory for faster fps
        if not self.stimuli_video_ready():
            return

        old_stdout = sys.stdout
        sys.stdout = str_stdout = StringIO()
        if self.video_ctrl is None:
            self.video_ctrl = VideoFeedCtrl()
            lcl_string = self.get_local_str("_preprocessing_video")
            self.__tracker_app_log(lcl_string)

            APP_THREADS["prep_thread"] = Thread(target=self.preprocessing_src_video)
            APP_THREADS["prep_thread"].start()
        else:
            lcl_string = self.get_local_str("_preprocessed_already")
            self.__tracker_app_log(lcl_string)

        self.ids['gaze_log'].text = "\n".join(str_stdout.getvalue().split("   "))
        sys.stdout = old_stdout

    def preprocessing_src_video(self):
        lcl_string = self.get_local_str("_video_preprocessing_started")
        self.__tracker_app_log(lcl_string)
        self.video_ctrl.preprocess_video(self.ids['lbl_src_video'].text)
        lcl_string = self.get_local_str("_video_preprocessing_finished")
        self.__tracker_app_log(lcl_string)

    def dismiss_popup(self):
        self._popup.dismiss()

    def show_load(self):
        content = LoadDialog(load=self.load, cancel=self.dismiss_popup, get_local_str=self.get_local_str)
        self._popup = Popup(title=self.get_local_str("_select_directory"), content=content, size_hint=(0.9, 0.9))
        self._popup.open()

    def show_load_video(self):
        content = LoadDialog(load=self.load_video, cancel=self.dismiss_popup, get_local_str=self.get_local_str)
        self._popup = Popup(title=self.get_local_str("_select_src_video"), content=content, size_hint=(0.9, 0.9))
        self._popup.open()

    def get_video_src(self):
        return self.ids['lbl_src_video'].text

    def load_video(self, path, filenames):
        lbl_src_video = self.ids['lbl_src_video']

        if len(filenames):
            if not filenames[0] == path:
                video_path = os.path.join(path, filenames[0])
                this_fps = self.get_video_fps(video_path)
                self.ids["txt_box_video_rate"].text = this_fps
                self.set_default_from_prev_session("txt_box_video_rate", this_fps)
                lbl_src_video.text = video_path
                self.set_default_from_prev_session("lbl_src_video", video_path)

        self.dismiss_popup()

    def load(self, path, filename):
        lbl_output_dir = self.ids['lbl_output_dir']
        lbl_output_dir.text = path
        self.set_default_from_prev_session('lbl_output_dir', path)
        self.dismiss_popup()

        self.save_dir_ready()


class Tracker(App):
    def build(self):
        Factory.register('Root', cls=Root)
        Factory.register('LoadDialog', cls=LoadDialog)

    def on_stop(self):
        for k, app_thread in APP_THREADS.items():
            app_thread.join()

        with open(prev_session_file_path, "w") as session_f:
            session_f.write(json.dumps(SESSION_PREFS))
            session_f.close()
        print("closing...")


if __name__ == '__main__':
    tracker = Tracker()
    tracker.run()
