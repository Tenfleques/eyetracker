#!/usr/bin/python
from kivy.app import App
from kivy.uix.screenmanager import Screen
from kivy.uix.popup import Popup
from kivy.core.window import Window
from collections import deque
from kivy.config import Config
from kivy.lang.builder import Builder
from kivy.graphics.texture import Texture
import os

from helpers import get_local_str_util, create_log, get_video_fps, props, get_default_from_prev_session, set_default_from_prev_session, file_log, fig2data

from ctrls.result_playback_ctrl import ResultVideoCanvas
from ctrls.table import Table
from ctrls.floatInput import FloatInput
from ctrls.integerInput import IntegerInput
from ctrls.infobar import InfoBar
from ctrls.framedetails import FrameDetails
from ctrls.select_box import SelectBox
from ctrls.loaddialog import LoadDialog
import cv2
import numpy as np


from threading import Thread

Config.set('graphics', 'kivy_clock', 'free_all')
Config.set('graphics', 'maxfps', 0)

APP_DIR = os.path.dirname(__file__)
APP_DIR = os.path.dirname(APP_DIR)
widget = Builder.load_file(os.path.join(APP_DIR, "settings", "screens",  "replay_screen.kv"))


class ReplayScreen(Screen):
    video_feed_ctrl = None
    session_timeline = None
    processes = []
    video_frame_shape = []

    video_frames = deque()
    video_frame_index = 0
    video_interval = None

    session_name = None
    vid_ctrl_set = False

    _popup = None 
    session_directory = None 
    processing_open_face = []

    @staticmethod
    def get_user_dir(in_dirs= ["data", "sessions"]):
        st = os.path.join(APP_DIR, "user")
        for d in in_dirs:
            st = os.path.join(st, d)
    
        return st

        os.makedirs(path_required, exist_ok=True)
        return path_required

    @staticmethod
    def get_default_from_prev_session(key, default=''):
        # loads a variable saved from the last session, directory, stimuli video for example
        val = get_default_from_prev_session(key, default)
        return val
    
    @staticmethod
    def set_default_from_prev_session(key, value):
        # set a variable key in this session. e.g the directory of stimuli video
        return set_default_from_prev_session(key, value)

    @staticmethod
    def get_local_str(key):
        # gets the localized string for literal text on the UI
        return get_local_str_util(key)

    @staticmethod
    def show_frame_info():
        file_log("[INFO] get the frame info: detailed ")

    @staticmethod
    def __tracker_app_log(text, log_label='app_log'):
        # give feedback to the user of what is happening behind the scenes
        app = App.get_running_app()
        try:
            app.tracker_app_log(text, log_label)
        except Exception as er:
            file_log("[ERROR] {}".format(er))

    def build(self):
        return widget

    def on_stop(self):
        self.stop_all()
        file_log("closing... replay screen")

    def stop_all(self):
        file_log("[INFO] closing processes in replay screen")
        self.stop()

        if self.video_feed_ctrl is not None:
            self.video_feed_ctrl.kill()

        for proc_instance in self.processes:
            # join all other running processes
            proc_instance.join()
        file_log("[INFO] closed all processes in replay screen ")

    def load_on_neighbor(self):
        d = self.ids["select_box_neighboring_sessions"].text
        par_path = os.path.dirname(self.session_directory)
        path = os.path.join(par_path, d)

        self.load(path, "")

    def populate_neighbor_sessions(self):
        other_sessions = []

        if not os.path.isdir(self.session_directory):
            parent_path = self.get_default_from_prev_session('lbl_src_sessions_directory', self.get_user_dir())
        else:
            parent_path = os.path.dirname(self.session_directory)
        
        os.makedirs(parent_path, exist_ok=True)
        other_sessions = [(d,self.load_on_neighbor) for d in os.listdir(parent_path) if 'exp' in d and os.path.isdir(os.path.join(parent_path, d))]
        return other_sessions

    def update_neighbors(self):
        self.ids["select_box_neighboring_sessions"].set_options(self.populate_neighbor_sessions())
        
    def start_all(self):
        self.ids["txt_box_replay_video_speed"].bind(on_text_validate=self.set_playback_fps)
        speeds = [("{}x".format(i), self.set_playback_fps) for i in [.1, .25, .5, 1, 1.5, 2, 2.5, 3]]

        self.ids["select_box_replay_speed"].set_options(speeds)
        self.ids["video_progress"].bind(on_touch_up=self.step_to_frame)

        self.ids["chkbx_bg_is_grab"].bind(state=self.toggle_bg_is_screen)
        self.ids["chkbx_maintain_track"].bind(state=self.toggle_maintain_track)
        self.ids["chkbx_tracker_track"].bind(state=self.toggle_tracker_track)
        self.ids["chkbx_camera_track"].bind(state=self.toggle_camera_track)
        self.ids["chkbx_video_track"].bind(state=self.toggle_video_track)
        self.ids["chkbx_open_face_track"].bind(state=self.toggle_open_face_track)
        # self.ids["chkbx_use_optimal_step"].bind(state=self.set_use_optimal_step)
        self.init_video_player()
        
        self.update_side_vid_stream_handle(cam_frame=None, ctrl=self.ids["camera_feed_image"], toggle_ctrl=self.ids["chkbx_camera_track"])
        self.update_side_vid_stream_handle(cam_frame=None, ctrl=self.ids["open_face_frame_feed_image"], toggle_ctrl=self.ids["chkbx_open_face_track"])

        return True

    def toggle_bg_is_screen(self, checkbox, value):
        if self.video_feed_ctrl is None:
            return
        self.video_feed_ctrl.toggle_bg_is_screen(value == 'down')

    def toggle_maintain_track(self, checkbox, value):
        if self.video_feed_ctrl is None:
            return
        self.video_feed_ctrl.toggle_maintain_track(value == 'down')

    def toggle_video_track(self, checkbox, value):
        if self.video_feed_ctrl is None:
            return
        self.video_feed_ctrl.toggle_video_track(value == 'down')

    def toggle_tracker_track(self, checkbox, value):
        if self.video_feed_ctrl is None:
            return
        self.video_feed_ctrl.toggle_tracker_track(value == 'down')

    def toggle_camera_track(self, checkbox, value):
        if self.video_feed_ctrl is None:
            return
        self.video_feed_ctrl.toggle_camera_track(value == 'down')
    
    def toggle_open_face_track(self, checkbox, value):
        if self.video_feed_ctrl is None:
            return
        self.video_feed_ctrl.toggle_open_face_track(value == 'down')
    
    def on_ref_press_collapse(self, **kwargs):
        self.ids["frame_details_parent"].width = 0
        self.ids["frame_details"].width = 0
        self.ids["frame_details_container"].width = 30
        self.ids["expand_frame_details_parent"].width = 40
        self.ids["expand_frame_details_parent"].height = 40
        self.ids["toggle_expand_frame_details"].width = 40
    
    def on_ref_press_expand(self, **kwargs):
        self.ids["frame_details_parent"].width = 280
        self.ids["frame_details"].width = 280
        self.ids["frame_details_container"].width = 280
        self.ids["expand_frame_details_parent"].width = 0
        self.ids["expand_frame_details_parent"].height = 0
        self.ids["toggle_expand_frame_details"].width = 0

    def set_use_optimal_step(self, checkbox, value):
        if self.video_feed_ctrl is None:
            return
        self.video_feed_ctrl.set_use_optimal_step(value == 'down')

    def set_playback_step(self, ctrl):
        if not ctrl.text:
            return

        if self.video_feed_ctrl is None:
            return
        step = int(ctrl.text)

        self.video_feed_ctrl.set_frame_skip(step)

    def speed_times_fps(self, txt):
        spd = 1
        try :
            spd = txt.replace("x","")
            spd = float(spd)
        except Exception as err:
            spd = 1

        return spd * self.video_feed_ctrl.get_fps(False)

    def set_playback_fps(self, ctrl=None):
        if self.video_feed_ctrl is None:
            return

        if ctrl is None:
            ctrl = self.ids["select_box_replay_speed"]
            fps = self.speed_times_fps(ctrl.text)

        else:
            str_fps = str(ctrl.text)
            fps = float(str_fps)

        self.video_feed_ctrl.set_fps(fps)

    def process_open_face_video(self, output_dir):
        app = App.get_running_app()
        open_face_root = os.path.join(output_dir, "openface")
        status = app.process_open_face_video_finished(open_face_root)
        
        if status == -1:
            # we haven't yet tried to process 
            app.process_open_face_video(output_dir)

        return status == 1

    def input_dir_ready(self):
        # check the directory in the computer's filesystem
        ready = os.path.isdir(self.session_directory)
        # directory doesn't exist, scream for attention
        if not ready:
            self.__tracker_app_log(self.get_local_str("_directory_not_selected"))
            return ready
        
        # update window to have name of session
        session_name = self.session_directory.split(os.sep)[-1]
        Window.set_title("{} [{}]".format(get_local_str_util('_appname'), session_name))

        self.process_open_face_video(self.session_directory)
        return True

    def stimuli_video_ready(self):
        ready = False
        # checks if video path is a file, if it's even a video file
        if get_video_fps(self.ids['lbl_src_video'].text):
            return True

        self.__tracker_app_log(self.get_local_str("_load_stimuli_video"), "stimuli_video_log")

        return ready

    def btn_stop_click(self):
        if self.video_feed_ctrl is None:
            return
        self.stop()

    def step_to_frame(self, ctrl, touch):
        val = ctrl.value
        if self.video_feed_ctrl is None:
            return

        self.video_feed_ctrl.step_to_frame(val)

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

    def btn_export_video_click(self):
        if not self.input_dir_ready():
            return

        if self.ids["replay_video_canvas"].get_is_exporting():
            self.__tracker_app_log(self.get_local_str("_export_module_busy"), "tracker_log")
            return 
        
        # list the files inside the input dir
        files = os.listdir(self.session_directory)
        filename = "tracker-timeline.json"
        if filename not in files:
            file_log("[ERROR] the tracker timeline file could not be found ")
            self.__tracker_app_log(self.get_local_str("_error_loading_session"), "camera_log")
            return

        session_timeline_path = os.path.join(self.session_directory, filename)
        cam_video_path = os.path.join(self.session_directory, "out-video.avi")
        cumulative_stimuli_src = os.path.join(self.session_directory, "cumulative_stimuli_src.avi")

        maintain_track = self.ids["chkbx_maintain_track"].state == 'down'
        video_track = self.ids["chkbx_video_track"].state == 'down'
        tracker_track = self.ids["chkbx_tracker_track"].state == 'down'
        camera_track = self.ids["chkbx_camera_track"].state == 'down'
        bg_is_screen = self.ids["chkbx_bg_is_grab"].state == 'down'

        proc_instance = Thread(target=self.ids["replay_video_canvas"].export_as_video, args=(cumulative_stimuli_src, session_timeline_path, cam_video_path,
                                             bg_is_screen, video_track, camera_track, tracker_track, maintain_track))
        proc_instance.start()
        self.processes.append(proc_instance)

    def init_video_player(self):
        # check the directory in the computer's filesystem

        if self.session_directory is None:
            self.session_directory = os.path.join(self.get_default_from_prev_session('lbl_src_sessions_directory', self.get_user_dir()), self.ids["select_box_neighboring_sessions"].text)

        ready = os.path.isdir(self.session_directory)
        if not ready:
            return None, None, None

        if self.video_feed_ctrl is None:
            self.video_feed_ctrl = self.ids["replay_video_canvas"]

        # list the files inside the input dir
        files = os.listdir(self.session_directory)
        filename = "tracker-timeline.json"
        if filename not in files:
            file_log("[ERROR] the tracker timeline file could not be found ")
            self.__tracker_app_log(self.get_local_str("_error_loading_session"), "camera_log")

        session_timeline_path = os.path.join(self.session_directory, filename)
        cam_video_path = os.path.join(self.session_directory, "out-video.avi")
        cumulative_stimuli_src = os.path.join(self.session_directory, "cumulative_stimuli_src.avi")

        self.video_feed_ctrl.toggle_maintain_track(self.ids["chkbx_maintain_track"].state == 'down')
        self.video_feed_ctrl.toggle_video_track(self.ids["chkbx_video_track"].state == 'down')
        self.video_feed_ctrl.toggle_tracker_track(self.ids["chkbx_tracker_track"].state == 'down')
        self.video_feed_ctrl.toggle_camera_track(self.ids["chkbx_camera_track"].state == 'down')
        self.video_feed_ctrl.toggle_bg_is_screen(self.ids["chkbx_bg_is_grab"].state == 'down')

        initialized = self.video_feed_ctrl.initialized(cumulative_stimuli_src,
              session_timeline_path, cam_video_path, self.progress_cb)

        if not initialized:
            return False

        return initialized

    def btn_play_click(self):
        if not self.input_dir_ready():
            return

        # if playing pause
        if self.video_feed_ctrl is not None:
            if self.video_feed_ctrl.is_playing():
                self.video_feed_ctrl.pause_play()
                self.set_button_play_start()
                return
        
        initialized  = self.init_video_player()
        # toggle play button to stop
        self.set_button_play_start()

        # callback when showing the video is ended 
        end_cb=lambda **kwargs: self.set_button_play_start(True)
        
        started = self.video_feed_ctrl.start(self.progress_cb, end_cb)

        self.__tracker_app_log(self.get_local_str("_playback_started"), "camera_log")

        fps = self.video_feed_ctrl.get_fps(False)
        
        if isinstance(fps, float):
            if "txt_box_replay_video_speed" in self.ids:
                self.ids["txt_box_replay_video_speed"].text = "{:.5}".format(fps)

    def update_side_vid_stream_handle(self, cam_frame=None, ctrl=None, toggle_ctrl=None):
        if ctrl is None:
            return 
        
        if cam_frame is None:
            cam_frame = np.full((int(toggle_ctrl.height), int(toggle_ctrl.width), 3), 255, dtype=np.uint8)

        if toggle_ctrl is None:
            cam_frame[:, :, :] = 255
        else:
            if not toggle_ctrl.state == 'down':
                cam_frame[:, :, :] = 255
        
        buf_raw = cv2.flip(cam_frame, 0)
        if buf_raw is None:
            return

        buf = buf_raw.tostring()
        texture = Texture.create(size=(cam_frame.shape[1], cam_frame.shape[0]), colorfmt='bgr')

        texture.blit_buffer(buf, colorfmt='bgr', bufferfmt='ubyte')
        # update video canvas
        ctrl.texture = texture


    def progress_cb(self, current=0, total=None, **kwargs):
        video_progress = self.ids["video_progress"]

        if total is None:
            total = video_progress.max

        if total != video_progress.max:
            video_progress.max = total
        
        if current and total:
            video_log = "{}/{}".format(current, total)
            self.__tracker_app_log(video_log, "app_log")
            video_progress.value = current

        cam_frame = kwargs.get("cam_frame", None)
        self.update_side_vid_stream_handle(cam_frame, ctrl=self.ids["camera_feed_image"], toggle_ctrl=self.ids["chkbx_camera_track"])

        open_face_frame = kwargs.get("open_face_frame", None)
        self.update_side_vid_stream_handle(open_face_frame, ctrl=self.ids["open_face_frame_feed_image"], toggle_ctrl=self.ids["chkbx_open_face_track"])

        if self.ids["frame_details"].width != 0:
            self.ids["frame_details"].update(**kwargs)

    def set_button_play_start(self, force_stop=False):
        if force_stop:
            self.ids["btn_play"].text = self.get_local_str("_start")
            self.__tracker_app_log(self.get_local_str("_playback_stopped"), "camera_log")
            
            if self.video_feed_ctrl is not None:
                self.video_feed_ctrl.reset()
            return

        if self.get_local_str("_start") == self.ids["btn_play"].text:
            self.ids["btn_play"].text = self.get_local_str("_pause")
            self.__tracker_app_log(self.get_local_str("_playing"), "camera_log")
            return

        self.ids["btn_play"].text = self.get_local_str("_start")
        self.__tracker_app_log(self.get_local_str("_paused"), "camera_log")

    def stop(self):
        # stop video capture feed and callback toggle play button ready for next experiment
        if self.video_feed_ctrl is not None:
            self.video_feed_ctrl.stop()

        self.progress_cb(0)
        self.set_button_play_start(True)

    def load(self, path, filename):
        if os.path.exists(path):
            if not os.path.isdir(path):
                path = os.path.dirname(path)

        self.session_directory = path
        self.ids["select_box_neighboring_sessions"].set_options(self.populate_neighbor_sessions())

        if self.video_feed_ctrl is not None:
            self.video_feed_ctrl.stop()
            self.video_feed_ctrl.reset()

        self.input_dir_ready()
