#!/usr/bin/python
from kivy.app import App

from kivy.factory import Factory
from kivy.uix.relativelayout import RelativeLayout

from kivy.uix.popup import Popup
import json

from eye_utilities.helpers import get_local_str_util, create_log, get_video_fps, props
import os
from components.loaddialog import LoadDialog
from result_playback_ctrl import ResultVideoCanvas
from components.table import Table
from components.floatInput import FloatInput
from components.integerInput import IntegerInput
from components.infobar import InfoBar
from components.framedetails import FrameDetails

from kivy.core.window import Window

from collections import deque

from kivy.config import Config


Config.set('graphics', 'kivy_clock', 'free_all')
Config.set('graphics', 'maxfps', 0)

Window.size = (1400, 800)
Window.clearcolor = (1, 1, 1, 1)

Window.set_title(get_local_str_util('_appname'))

# Window.set_icon('./assets/icon.png')
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


class Root(RelativeLayout):
    video_feed_ctrl = None
    session_timeline = None
    processes = []
    video_frame_shape = []

    video_frames = deque()
    video_frame_index = 0
    video_interval = None

    session_name = None

    def stop_all(self):
        print("[INFO] closing processes and devices")
        self.stop()
        for p in self.processes:
            # join all other running processes
            p.join()
        print("[INFO] closed all processes and devices ")

    @staticmethod
    def get_default_from_prev_session(key, default=''):
        # loads a variable saved from the last session, directory, stimuli video for example
        if key in SESSION_PREFS.keys():
            return str(SESSION_PREFS.get(key))
        else:
            return default

    @staticmethod
    def set_default_from_prev_session(key, value):
        # set a variable key in this session. e.g the directory of stimuli video
        SESSION_PREFS[key] = value

    @staticmethod
    def get_local_str(key):
        # gets the localized string for litera text on the UI
        return get_local_str_util(key)

    def show_frame_info(self):
        print("[INFO] get the frame info: detailed ")

    def set_playback_fps(self, ctrl):
        if not ctrl.text:
            return
        fps = float(ctrl.text)

        if not fps:
            return

        if self.video_feed_ctrl is None:
            return

        self.video_feed_ctrl.set_fps(fps)

    def start_all(self):
        print("[INFO] init listeners")
        self.ids["txt_box_replay_video_rate"].bind(on_text_validate=self.set_playback_fps)
        self.ids["video_progress"].bind(on_touch_up=self.step_to_frame)

    def input_dir_ready(self):
        lbl_input_dir = self.ids['lbl_input_dir']
        # check the directory in the computer's filesystem
        ready = os.path.isdir(lbl_input_dir.text)
        # directory doesn't exist, scream for attention
        if not ready:
            lbl_input_dir.color = (1, 0, 0, 1)  # red scream
            self.__tracker_app_log(self.get_local_str("_directory_not_selected"))
        else:
            lbl_input_dir.color = (0, 0, 0, 1)

        return ready

    def stimuli_video_ready(self):
        ready = False
        # checks if video path is a file, if it's even a video file
        if get_video_fps(self.ids['lbl_src_video'].text):
            return True

        self.__tracker_app_log(self.get_local_str("_load_stimuli_video"))

        return ready

    def __tracker_app_log(self, text, log_label='app_log'):
        # give feedback to the user of what is happening behind the scenes
        log = create_log(text)
        if log_label in self.ids["info_bar"].ids:
            self.ids["info_bar"].log_text(log, log_label)
            return

        if log_label in self.ids:
            self.ids[log_label].text = log

    def btn_stop_click(self):
        if self.video_feed_ctrl is None:
            return
        self.stop()

    def step_to_frame(self, ctrl, touch):
        if self.video_feed_ctrl is None:
            return
        self.video_feed_ctrl.step_to_frame(ctrl.value)

    def btn_step_backward_click(self):
        if self.video_feed_ctrl is None:
            return

        if not self.ids["txt_box_step_size"].text:
            return

        step_size = int(self.ids["txt_box_step_size"].text)
        self.video_feed_ctrl.step_backward(step_size)

    def btn_step_forward_click(self):
        if self.video_feed_ctrl is None:
            return
        if not self.ids["txt_box_step_size"].text:
            return

        step_size = int(self.ids["txt_box_step_size"].text)
        self.video_feed_ctrl.step_forward(step_size)

    def btn_play_click(self):
        """
        connects to the camera, video, tracker adapters
        runs till stop or end of stimuli video.
        :return:
        """
        if not self.input_dir_ready():
            return

        if self.video_feed_ctrl is None:
            self.video_feed_ctrl = self.ids["replay_video_canvas"]

        # if playing pause
        if self.video_feed_ctrl.is_playing():
            self.video_feed_ctrl.pause_play()
            self.set_button_play_start()
            return

        # can't run session if video stimuli not ready can we?
        if not self.stimuli_video_ready():
            return

        # list the files inside the input dir
        files = os.listdir(self.ids['lbl_input_dir'].text)
        filename = "tracker-timeline.json"
        if filename not in files:
            print("[ERROR] the tracker timeline file caould not be found ")

        viewpoint_size = None
        session_timeline_path = os.path.join(self.ids['lbl_input_dir'].text, filename)
        cam_video_path = os.path.join(self.ids['lbl_input_dir'].text, "out-video.avi")
        end_cb=lambda t: self.set_button_play_start(True)

        # toggle play button to stop
        self.set_button_play_start()
        # get path to video
        video_src = self.ids['lbl_src_video'].text

        # set fps
        self.set_playback_fps(self.ids["txt_box_replay_video_rate"])

        started = self.video_feed_ctrl.start(video_src, session_timeline_path,
                                             viewpoint_size, cam_video_path, self.progress_cb,
                                             end_cb)

        print("[INFO] started video player {} ".format(started))
        fps = self.video_feed_ctrl.get_fps()
        self.ids["txt_box_replay_video_rate"].text = "{:.5}".format(fps)

    def progress_cb(self, current, total=None, frame_details=None):
        video_progress = self.ids["video_progress"]
        if total is None:
            total = video_progress.max

        if total != video_progress.max:
            video_progress.max = total

        video_log = "{}/{}".format(current, total)
        self.__tracker_app_log(video_log, "stimuli_video_log")
        video_progress.value = current

        if frame_details is not None:
            self.ids["frame_details"].update(frame_details)

    def set_button_play_start(self, force_stop=False):
        if force_stop:
            self.ids["btn_play"].text = self.get_local_str("_start")
            return

        if self.get_local_str("_start") == self.ids["btn_play"].text:
            self.ids["btn_play"].text = self.get_local_str("_pause")
            return

        self.ids["btn_play"].text = self.get_local_str("_start")

    def stop(self):
        # stop video capture feed and callback toggle play button ready for next experiment
        if self.video_feed_ctrl is not None:
            self.video_feed_ctrl.stop()

        self.progress_cb(0)
        self.set_button_play_start(True)

    # loading directory dialog
    def dismiss_popup(self):
        self._popup.dismiss()

    def show_load(self):
        content = LoadDialog(load=self.load, cancel=self.dismiss_popup,
                             get_local_str=self.get_local_str,
                             get_default_from_prev_session=self.get_default_from_prev_session)
        self._popup = Popup(title=self.get_local_str("_select_directory"), content=content, size_hint=(0.9, 0.9))
        self._popup.open()

    # loading video file dialog
    def show_load_video(self):
        content = LoadDialog(load=self.load_video, cancel=self.dismiss_popup,
                             get_local_str=self.get_local_str,
                             get_default_from_prev_session=self.get_default_from_prev_session)
        self._popup = Popup(title=self.get_local_str("_select_src_video"), content=content, size_hint=(0.9, 0.9))
        self._popup.open()

    def load_video(self, path, filenames):
        lbl_src_video = self.ids['lbl_src_video']
        self.set_default_from_prev_session('filechooser', path)

        if len(filenames):
            if not filenames[0] == path:
                video_path = os.path.join(path, filenames[0])
                lbl_src_video.text = video_path
                self.set_default_from_prev_session("lbl_src_video", video_path)

        self.dismiss_popup()

    def load(self, path, filename):
        lbl_input_dir = self.ids['lbl_input_dir']
        lbl_input_dir.text = path
        self.set_default_from_prev_session('lbl_input_dir', path)
        self.set_default_from_prev_session('filechooser', path)
        self.dismiss_popup()

        self.input_dir_ready()


class Replay(App):
    def build(self):
        Factory.register('Root', cls=Root)
        Factory.register('LoadDialog', cls=LoadDialog)

    def on_start(self):
        app = App.get_running_app()
        app.root.start_all()

    def on_stop(self):
        app = App.get_running_app()
        app.root.stop_all()
        with open(prev_session_file_path, "w") as session_f:
            session_f.write(json.dumps(SESSION_PREFS))
            session_f.close()
        print("closing...")


if __name__ == '__main__':
    tracker = Replay()
    tracker.run()
