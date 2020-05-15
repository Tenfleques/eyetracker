#!/usr/bin/python
from kivy.app import App

from kivy.factory import Factory
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from floatInput import FloatInput
from kivy.uix.image import Image
from kivy.graphics.texture import Texture

from kivy.properties import ObjectProperty
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.clock import Clock
import json
import time
from multiprocessing import Process
from threading import Thread
import math

from eye_utilities.helpers import get_local_str_util, create_log, get_video_fps, frame_processing, process_fps, props
from process_result import gaze_stimuli

import os
from io import StringIO
import sys

from camera_feed_ctrl import Frame, CameraFeedCtrl
from tracker_ctrl import TrackerCtrl
from kivy.core.window import Window

import platform
import cv2
import numpy as np
from collections import deque

from kivy.config import Config

Config.set('graphics', 'kivy_clock', 'free_all')
Config.set('graphics', 'maxfps', 0)

Window.size = (1200, 800)
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

class LoadDialog(FloatLayout):
    load = ObjectProperty(None)
    cancel = ObjectProperty(None)
    get_default_from_prev_session = ObjectProperty(None)
    get_local_str = ObjectProperty(None)


class Root(FloatLayout):
    tracker_ctrl = None
    camera_feed_ctrl = CameraFeedCtrl()
    session_timeline = None
    processes = []
    video_frame_shape = []

    video_frames = deque()
    video_frame_index = 0
    video_interval = None

    

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if platform.system() == 'Darwin':
            print("[INFO] Running on Mac OS")
        

    def stop_all(self):
        print("[INFO] closing processes and devices")
        if self.tracker_ctrl is not None:
            self.tracker_ctrl.kill()
        for p in self.processes:
            p.join()
        print("[INFO] closed all processes and devices ")

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

        print(props(self.ids['lbl_src_video']))

        # cap = cv2.VideoCapture(self.ids['lbl_src_video'].text)
        # self.update_video_canvas(dt, cap)
        # cap.release()

        return ready

    def __tracker_app_log(self, text, log_label='app_log'):
        log = create_log(text)
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

        if self.video_interval is not None:
            self.stop()
            return
        
        output_dir = self.ids['lbl_output_dir'].text
        self.ids["tabbed_main_view"].switch_to(self.ids["tabbed_video_item"], do_scroll=True)

        camera_up = self.camera_feed_ctrl.start(output_path=output_dir,
              camera_index=0, save_images=False)
        
        if not camera_up:
            self.__tracker_app_log(self.get_local_str("_problem_waiting_camera"))
            return

        self.ids["btn_play"].text = self.get_local_str("_stop")
        video_src=self.ids['lbl_src_video'].text
        fps=float(self.ids['txt_box_video_rate'].text)

        self.old_stdout = sys.stdout
        sys.stdout = str_stdout = StringIO()
        # self.session_name =
        self.start(video_src, fps)
        self.ids['gaze_log'].text = "\n".join(str_stdout.getvalue().split("   "))

    def frames_cb(self, frame):
        frame = frame_processing(frame)
        self.video_frames.append(Frame(self.video_frame_index))
        self.video_frame_index += 1
        return frame

    def start(self, video_src, fps, is_recording=True):        
        video_canvas = self.ids["video_canvas"]
        self.video_frame_shape = []
        cb = lambda f: f
        if is_recording:
            self.video_frames.clear()
            self.video_frame_index = 0
            cb = self.frames_cb
        
        self.video_capture = cv2.VideoCapture(video_src)
        ret, frame = self.video_capture.read()

        # print(frame.shape)
        # sys.stdout.flush()

        em_fps = self.video_capture.get(cv2.CAP_PROP_FPS)
        if fps == 0:
            fps = em_fps
        
        if fps == 0:
            return 

        # start camera thread
        output_path = self.ids['lbl_output_dir'].text
        self.poll_count = 0
        save_images=False


        if self.tracker_ctrl is None:
            self.tracker_ctrl = TrackerCtrl()
        self.tracker_ctrl.start()
        
        self.video_interval = Clock.schedule_interval(lambda dt: self.update_video_canvas(dt, self.video_capture, cb), 1.0/fps)

    def stop(self):
        self.camera_feed_ctrl.stop()
        self.tracker_ctrl.stop()
        self.video_capture.release()

        if self.video_interval is not None:
            self.video_interval.cancel()
            self.video_interval = None
            info_1, info_2, self.actual_video_stimuli_fps = process_fps(self.video_frames)
            # log infor
            self.ids["btn_play"].text = self.get_local_str("_start")
            self.__after_recording()

            log_1, log_2, video_frame_rate = process_fps(self.video_frames)

            lcl_string_fps = self.get_local_str("_actual_video_fps") + ": {:.4} ".format(video_frame_rate)

            self.__tracker_app_log(lcl_string_fps, "stimuli_video_log")

            log_1, log_2, camera_frame_rate = process_fps(self.camera_feed_ctrl.get_frames())

            lcl_string_fps = self.get_local_str("_factual_camera_fps") + ": {:.4} ".format(camera_frame_rate)

            self.__tracker_app_log(lcl_string_fps, "camera_log")
        
        sys.stdout = self.old_stdout
        self.ids["tabbed_main_view"].switch_to(self.ids["tabbed_timeline_item"], do_scroll=True)

    def update_video_canvas(self, dt, cap, cb):
        video_canvas = self.ids["video_canvas"]
        ret, frame = cap.read()
        if not ret:
            self.stop()
            return 
        
        frame = cb(frame)

        buf_raw = cv2.flip(frame, 0)
        buf = buf_raw.tostring()
        texture = Texture.create(size=(frame.shape[1], frame.shape[0]), colorfmt='bgr') 
     
        texture.blit_buffer(buf, colorfmt='bgr', bufferfmt='ubyte')

        video_canvas.texture = texture

    
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
    
    def get_json(self):
        obj = {
                "camera": [i.to_dict() for i in self.camera_feed_ctrl.get_frames()],
                "video": [i.to_dict() for i in self.video_frames]
        }
        return obj

    def save_json(self, path=b"./results.json"):
        with open(path, "w") as f:
            f.write(json.dumps(self.get_json()))
            f.close()

    # session timeline view
    def load_session_timeline(self, tracker_json_path, video_json_path, timeline_exist=False, process_video=True):
        print("[INFO] started to process the timeline {}    ".format(time.strftime("%H:%M:%S")))
        lcl_string = self.get_local_str("_preparing_session_timeline")
        self.__tracker_app_log(lcl_string)
        selfie_video_path = os.path.join(self.ids['lbl_output_dir'].text,
                                         "out-video.avi")
        lcl_video_finished_str = self.get_local_str("_demonstration_video_ready")

        self.session_timeline = gaze_stimuli(tracker_json_path,
                                             video_json_path,
                                             self.ids['lbl_src_video'].text,
                                             selfie_video_path=selfie_video_path,
                                             timeline_exist=timeline_exist, process_video=process_video,
                                             session_timeline_cb=self.load_session_results,
                                             video_cb=lambda: self.__tracker_app_log(lcl_video_finished_str))

    def __set_session_timeline(self, st):
        print("[INFO] set session timeline length: {}    ".format(len(st.keys())))
        self.session_timeline = st

    def load_session_results(self, st=None):
        if st is not None:
            self.__set_session_timeline(st)

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

        range_of_values = 10
        self.__create_pagination_panel(range_of_values, self.session_timeline)
        self.__load_main_view_rows(self.session_timeline, 0, range_of_values)

    def __create_pagination_panel(self, range_of_values, st):
        pagination_buttons_count = math.ceil(len(st.keys()) /
                                             (range_of_values * 1.0))
        print("[INFO] pagination count {} ".format(pagination_buttons_count))

        self.ids["pagination_zone"].clear_widgets()

        for i in range(pagination_buttons_count):
            button = Button(text=str(i),
                            size_hint=(None, None), width='40dp', height='25dp',
                            padding=(5, 5),
                            halign='center', font_size=13)

            if i == 0:
                button.state = 'down'

            button_callback = lambda btn: self.__load_main_view_rows(st,
                                                                 start_index=i * range_of_values,
                                                                 max_elements=range_of_values, btn=btn)

            button.bind(on_release=button_callback)
            self.ids["pagination_zone"].add_widget(button)

    def __load_main_view_rows(self, st, start_index=0, max_elements=10, btn=None):
        k = -1
        self.ids["view_stage"].bind(minimum_height=self.ids["view_stage"].setter('height'))
        if btn is not None:
            btn.state = 'down'
            # find the current active button and deactivate it
            # self.ids["pagination_zone"].children
            # self.active_page
            start_index = int(btn.text) * max_elements
        rows = GridLayout(cols=1)
        self.ids["view_stage"].clear_widgets()

        for key, record in st.items():
            k += 1
            if k < start_index:
                continue

            if k > max_elements + start_index:
                break

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

            rows.add_widget(row)


        self.ids["view_stage"].add_widget(rows)
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
        self.set_default_from_prev_session('filechooser', path)
        self.dismiss_popup()

        self.save_dir_ready()

    
    def __after_recording(self):
        try:
            self.tracker_ctrl.stop()
            tracker_json_path = os.path.join(self.ids['lbl_output_dir'].text, "tracker.json")
            video_json_path = os.path.join(self.ids['lbl_output_dir'].text, "video_camera.json")

            self.tracker_ctrl.save_json(tracker_json_path)
            self.save_json(video_json_path)

            p = Thread(target=self.load_session_timeline, args=(tracker_json_path,
                                                                video_json_path, False, True,))
            p.start()

            self.processes.append(p)
        except Exception as ex:
            print("[ERROR] an error occurred {}{}    "
                    .format(ex, time.strftime("%H:%M:%S")))
            del self.tracker_ctrl
            self.tracker_ctrl = None

        self.ids['btn_play'].text = self.get_local_str("_start")

        lcl_string = self.get_local_str("_demonstration_preparing")
        self.__tracker_app_log(lcl_string)


class Tracker(App):
    def build(self):
        Factory.register('Root', cls=Root)
        Factory.register('LoadDialog', cls=LoadDialog)

    def on_stop(self):
        app = App.get_running_app()
        app.root.stop_all()

        with open(prev_session_file_path, "w") as session_f:
            session_f.write(json.dumps(SESSION_PREFS))
            session_f.close()
        print("closing...")


if __name__ == '__main__':
    tracker = Tracker()
    tracker.run()
