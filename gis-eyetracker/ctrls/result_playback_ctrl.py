#!/usr/bin/python
from kivy.app import App
from kivy.uix.image import Image
from kivy.graphics.texture import Texture
from kivy.clock import Clock

from kivy.core.window import Window
import cv2
import json
import numpy as np

import platform
if platform.system() == 'Linux':
    import pyscreenshot as ImageGrab
else:
    from PIL import ImageGrab
    
import os
import time
import math

from kivy.config import Config
from collections import deque
from threading import Thread
from helpers import get_local_str_util, file_log


Config.set('graphics', 'kivy_clock', 'free_all')
Config.set('graphics', 'maxfps', 0)

def video_export_progress_cb(current, total):
    # give feedback to the user of what is happening behind the scenes
    app = App.get_running_app()
    try:
        if "replay_screen" in app.root.ids:
            rep_screen = app.root.ids["replay_screen"]
            if "video_export_progress" in rep_screen.ids:
                rep_screen.ids["video_export_progress"].value = current
                rep_screen.ids["video_export_progress"].max = total
            else:
                print("replay_screen has no progress ctrl")
        else:
            print("replay_screen not found")

    except Exception as er:
        file_log("[ERROR] {}".format(er))


class ResultVideoCanvas(Image):
    session_timeline = {}
    session_timeline_index = 0
    timestamp_keys = []
    video_fps = 100
    base_fps = 200
    frame_skip = 1
    use_optimal_step = True
    stop_threads = False
    is_paused = False
    

    video_interval = None

    video_capture = None

    SCREEN_SIZE = ImageGrab.grab().size
    bg_frame = np.zeros((SCREEN_SIZE[0], SCREEN_SIZE[1], 3), dtype=np.uint8)

    video_frames = deque()
    camera_frames = deque()

    current_vid_frame_id = 0
    current_cam_frame_id = 0

    initial_window_state = Window.fullscreen
    # for writing tracker on the video
    radius = 15
    color = (0, 255, 0)
    thickness = 2

    v_frame = None
    c_frame = None

    camera_frames_cap = None
    video_frames_cap = None
    open_face_video_frames_cap = None

    c_width = None
    c_height = None
    c_start_x = None

    bg_is_screen = False
    maintain_track = False
    camera_track = False
    tracker_track = False
    video_track = False
    open_face_track = True

    processes = []
    is_exporting_busy = False

    current_video_path = None
    current_session_timeline_path = None
    current_cam_video_path = None

    session_is_playing = False

    def set_use_optimal_step(self, val):
        self.use_optimal_step = bool(val)

    def set_frame_skip(self, step):
        if not isinstance(step, int):
            return
            
        self.frame_skip = max(1, int(step))

    def toggle_bg_is_screen(self, state=None):
        if state is None:
            self.bg_is_screen = not self.bg_is_screen
            return
        self.bg_is_screen = bool(state)

    def toggle_maintain_track(self, state=None):
        if state is None:
            self.maintain_track = not self.maintain_track
            return
        self.maintain_track = bool(state)

    def toggle_video_track(self, state=None):
        if state is None:
            self.video_track = not self.video_track
            return
        self.video_track = bool(state)

    def toggle_tracker_track(self, state=None):
        if state is None:
            self.tracker_track = not self.tracker_track
            return
        self.tracker_track = bool(state)

    def toggle_camera_track(self, state=None):
        if state is None:
            self.camera_track = not self.camera_track
            return
        self.camera_track = bool(state)

    def toggle_open_face_track(self, state=None):
        if state is None:
            self.open_face_track = not self.open_face_track
            return
        self.open_face_track = bool(state)

    def is_playing(self):
        return self.session_is_playing

    def end_play_cb(self, **kwargs):
        pass

    def get_progress(self):
        return self.session_timeline_index, len(self.timestamp_keys)

    def get_fps(self, current=True):        
        if current:
            return self.video_fps

        return self.base_fps
    
    def reset(self):
        self.session_is_playing = False
        self.session_timeline_index = 0        
        self.current_vid_frame_id = 0
        self.current_cam_frame_id = 0
        self.update_video_canvas(self.session_timeline_index)

    @staticmethod
    def current_frame_cb(current, total, record=None, **kwargs):
        print("[INFO] frame {}/{}".format(current, total))

    @staticmethod
    def __tracker_app_log(text, log_label='tracker_log'):
        # give feedback to the user of what is happening behind the scenes
        app = App.get_running_app()
        try:
            app.tracker_app_log(text, log_label)
        except Exception as er:
            file_log("[ERROR] {}".format(er))

    def pause_play(self):
        if self.video_interval is None:
            self.video_interval = Clock.schedule_interval(self.update_video_canvas, 1.0/self.video_fps)
            self.is_paused = False
            return

        # video is playing already
        self.is_paused = not self.is_paused

        if self.is_paused:
            self.video_interval.cancel()
        else:
            self.video_interval()

    def set_fps(self, video_fps):
        self.video_fps = max(video_fps, 1)

        if self.video_interval is not None:
            self.video_interval.cancel()
            self.video_interval = Clock.schedule_interval(self.update_video_canvas, 1.0/self.video_fps)
            if self.is_paused:
                self.video_interval.cancel()

    def step_to_frame(self, index):
        if self.video_interval is not None:
            # pause the playback for a moment
            if not self.is_paused:
                self.video_interval.cancel()
         
        len_tl = len(self.timestamp_keys)
        if isinstance(index, float):
            index = min(int(index), len_tl - 1)

        if not isinstance(index, int):
            return
        
        if index <= 0:
            if not self.is_paused and self.video_interval is not None:
                self.video_interval()
            return

        self.session_timeline_index = index

        if not self.is_paused and self.video_interval is not None:
            self.video_interval()

        self.update_video_canvas(index)

    def step_forward(self, step_size):
        # if self.video_interval is None:
        #     return

        len_tl = len(self.timestamp_keys)
        index = min(self.session_timeline_index + step_size, len_tl)
        self.update_video_canvas(index)

    def step_backward(self, step_size):
        # if self.video_interval is None:
        #     return

        index = max(self.session_timeline_index - step_size, 0)
        self.update_video_canvas(index)

    def __get_stop_threads(self):
        return self.stop_threads

    def initialized(self, video_path,
              session_timeline_path, cam_video_path, current_frame_cb):
        
        self.reset()

        if current_frame_cb is not None:
            self.current_frame_cb = current_frame_cb
    
        if self.current_video_path == video_path and self.current_session_timeline_path == session_timeline_path and self.current_cam_video_path == cam_video_path:
            return False
        
        if not os.path.isfile(session_timeline_path):
            self.__tracker_app_log(get_local_str_util("_session_timeline_not_found"))
            file_log("[ERROR] {}".format(get_local_str_util("_session_timeline_not_found")))
            return False

        self.session_timeline = {}

        with open(session_timeline_path, "r") as fp:
            all_session = json.load(fp)
            for k in all_session.keys():
                if all_session[k]["video"] is not None and all_session[k]["camera"] is not None:
                    self.session_timeline[k] = all_session[k]

            fp.close()


        self.SCREEN_SIZE = ImageGrab.grab().size
        self.bg_image = np.zeros((self.SCREEN_SIZE[1], self.SCREEN_SIZE[0], 3), dtype=np.uint8)

        image_grab_path = os.sep.join(session_timeline_path.split(os.sep)[:-1])
        image_grab_path = os.path.join(image_grab_path, "screen.png")

        if os.path.isfile(image_grab_path):
            self.bg_image = cv2.imread(image_grab_path)
            self.SCREEN_SIZE = self.bg_image.shape

        self.bg_frame = np.zeros((self.SCREEN_SIZE[0], self.SCREEN_SIZE[1], 3), dtype=np.uint8)

        self.timestamp_keys = [i for i in self.session_timeline.keys()]
        float_timestamp_keys = [float(i) for i in self.timestamp_keys]
        len_keys = len(self.timestamp_keys)

        if len_keys == 0:
            error_text = "[ERROR] timeline is empty"
            self.__tracker_app_log(get_local_str_util("_session_timeline_empty"))
            file_log(error_text)
            self.stop()
            return False

        diff = max(float_timestamp_keys) - min(float_timestamp_keys)
        self.base_fps = len_keys / max(diff,1)

        self.set_fps(self.base_fps)

        if self.session_timeline_index >= len_keys - 1:
            self.session_timeline_index = 0

        if not os.path.isfile(video_path):
            self.__tracker_app_log(get_local_str_util("_src_video_not_exists"))
            file_log(get_local_str_util("_src_video_not_exists"))
            self.stop()
            return False

        self.video_frames_cap = self.init_video_frame_capture(video_path, self.video_frames_cap)

        self.camera_frames_cap = self.init_video_frame_capture(cam_video_path, self.camera_frames_cap)

        self.init_open_face_frames(cam_video_path)

        self.current_frame_cb(cam_fps=self.camera_frames_cap.get(cv2.CAP_PROP_FPS), 
            vid_fps=self.video_frames_cap.get(cv2.CAP_PROP_FPS),
            gaze_fps=self.base_fps/3.0, pos_fps=self.base_fps/3.0, origin_fps=self.base_fps/3.0)

        self.current_video_path = video_path
        self.current_session_timeline_path = session_timeline_path
        self.current_cam_video_path = cam_video_path

        return True

    def init_open_face_frames(self, cam_video_path):
        if self.open_face_video_frames_cap is not None:
            self.open_face_video_frames_cap.release()

        self.open_face_video_frames_cap = None
        cam_video_arr = cam_video_path.split(os.sep)
        out_dir = os.sep.join(cam_video_arr[:-1])
        open_face_root = os.path.join(out_dir, "openface")
        open_face_video_path = os.path.join(open_face_root, cam_video_arr[-1])

        app = App.get_running_app()
        open_face_status = app.process_open_face_video_finished(open_face_root) 

        if open_face_status == -1:
            app.process_open_face_video(out_dir) 
            Clock.schedule_once(lambda dt: self.init_open_face_frames(cam_video_path),60)
            return None
        if open_face_status == 0:
            # processing in progress 
            Clock.schedule_once(lambda dt: self.init_open_face_frames(cam_video_path),30)
            return None

        # processed already 
        self.open_face_video_frames_cap = self.init_video_frame_capture(open_face_video_path, self.open_face_video_frames_cap)

    def init_video_frame_capture(self, path, cap):
        if cap is not None:
            cap.release()
        cap = None

        if not os.path.isfile(path):
            return cap

        cap = cv2.VideoCapture(path)
        return cap 

    def start(self, current_frame_cb, end_cb):

        if end_cb is not None:
            self.end_play_cb = end_cb
        if current_frame_cb is not None:
            self.current_frame_cb = current_frame_cb

        self.v_frame = None
        self.c_frame = None

        # if playing stop
        if self.video_interval is not None:
            self.stop()
            return 1

        # ensures we are full screen
        # self.initial_window_state = Window.fullscreen
        # Window.fullscreen = 'auto'
        # play video
        self.pause_play()
        self.session_is_playing = True

    def update_video_canvas(self, dt):
        # read next frame
        frame = self.bg_frame
        if dt:
            frame = self.frames_cb(dt)
        
        if frame is None:
            return 
        
        buf_raw = cv2.flip(frame, 0)
        if buf_raw is None:
            if dt is None:
                # avoid infinite recursion
                return
            self.stop()
            return

        buf = buf_raw.tostring()
        texture = Texture.create(size=(frame.shape[1], frame.shape[0]), colorfmt='bgr')

        texture.blit_buffer(buf, colorfmt='bgr', bufferfmt='ubyte')
        # update video canvas
        self.texture = texture
        
    
    def __set_session_timeline_index(self, value):
        self.session_timeline_index = value
    
    def __get_session_timeline_index(self):
        return self.session_timeline_index

    def frames_cb(self, dt=True):
        # dt is None when called from stop to stop recursions
        show_frame = self.bg_frame [:, :, :]
        show_frame[:, :, :] = 250
        # show current screen as background
        if self.bg_is_screen:
            show_frame[:, :, :] = self.bg_image

        len_timeline = len(self.timestamp_keys)

        optimal_frame_step = self.get_fps()/min(Clock.get_fps(),60.0)

        if isinstance(dt, int):
            self.session_timeline_index = dt
        else:
            self.session_timeline_index = self.__get_session_timeline_index()
        
        if self.session_timeline_index >= len_timeline:
            self.stop()
            return None
            
        key = self.timestamp_keys[self.session_timeline_index]
        record = self.session_timeline[key]

        v_x = None
        v_y = None
        # add video feed data
        if record["video"] is not None:
            if self.current_vid_frame_id != record["video"]["frame_id"]:
                self.current_vid_frame_id = record["video"]["frame_id"]

            if self.video_track:
                # self.v_frame = self.get_video_frame_at(self.current_vid_frame_id)
                self.v_frame = self.get_capture_frame_at(self.current_vid_frame_id, self.video_frames_cap)
                if "width" in record["video"]:
                    sz = (int(record["video"]["width"]), int(record["video"]["height"]))
                    self.v_frame = cv2.resize(self.v_frame, sz)

                    v_x = int(record["video"]["x"])
                    v_y = int(record["video"]["y"])

                    try:
                        show_frame[v_y:self.v_frame.shape[0] + v_y,
                                        v_x:self.v_frame.shape[1] + v_x, :] = self.v_frame

                    except ValueError as err:
                        file_log("[ERROR] a video resize error occurred {}".format(err))

        xo = None
        yo = None
        # add gaze feed data
        if record["gaze"] is not None and self.tracker_track:
            xr = record["gaze"]['x']
            yr = record["gaze"]['y']

            xo = int(show_frame.shape[1] * xr)
            yo = int(show_frame.shape[0] * yr)


        if xo is not None and yo is not None and self.tracker_track:
            show_frame = cv2.circle(show_frame, (xo, yo),
                                       self.radius, self.color, self.thickness)
            if self.maintain_track:
                # write all the positions of the track from 0 - this index
                for i in range(self.session_timeline_index):
                    his_key = self.timestamp_keys[i]
                    if "gaze" in self.session_timeline[his_key]:
                        xr = self.session_timeline[his_key]["gaze"]['x']
                        yr = self.session_timeline[his_key]["gaze"]['y']

                        xr = int(show_frame.shape[1] * xr)
                        yr = int(show_frame.shape[0] * yr)
                        show_frame = cv2.circle(show_frame, (xr, yr), 2, (0, 0, 255, 1), self.thickness)

        if dt:
            if self.use_optimal_step:
                val = self.session_timeline_index + max(math.floor(optimal_frame_step), 1)
            else:
                val = self.session_timeline_index + self.frame_skip
            
            self.__set_session_timeline_index(val)
            
            self.__tracker_app_log("{}: {:.4}".format(get_local_str_util("_optimal_frame_skip"), optimal_frame_step), log_label='stimuli_video_log')

        if not self.bg_is_screen:
            if v_x is not None and v_y is not None:
                # pan to the video size
                sh = show_frame[v_y:, v_x:, :].shape
                if self.v_frame is not None:
                    h = self.v_frame.shape[0] + v_y
                    show_frame = show_frame[v_y:h, v_x:, :]
                else:
                    show_frame = show_frame[v_y:, v_x:, :]

        # add camera feed data
        open_face_frame = None
        if record["camera"] is not None:
            if self.current_cam_frame_id != record["camera"]["frame_id"]:
                self.current_cam_frame_id = record["camera"]["frame_id"]

            if self.camera_track:
                self.c_frame = self.get_capture_frame_at(self.current_cam_frame_id, self.camera_frames_cap)

            if self.open_face_track:
                open_face_frame = self.get_capture_frame_at(self.current_cam_frame_id, self.open_face_video_frames_cap)
        
        self.current_frame_cb(self.session_timeline_index, len_timeline, frame_details=record, cam_frame=self.c_frame, open_face_frame=open_face_frame)

        return show_frame

    def get_video_frame_at(self, index):
        if index < len(self.video_frames):
            return self.video_frames[index]
        return np.zeros((self.SCREEN_SIZE[1], self.SCREEN_SIZE[0], 3), dtype=np.uint8)

    def get_camera_frame_at(self, index):
        if index < len(self.camera_frames):
            return self.camera_frames[index]
        return np.zeros((self.SCREEN_SIZE[1], self.SCREEN_SIZE[0], 3), dtype=np.uint8)

    def get_capture_frame_at(self, index, cap):
        if cap is not None:
            frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
            # fps = cap.get(cv2.CAP_PROP_FPS)
            if index < frame_count:
                cap.set(cv2.CAP_PROP_POS_FRAMES, index)
                success, frame = cap.read()
                if success:
                    return frame

        return np.zeros((self.SCREEN_SIZE[1], self.SCREEN_SIZE[0], 3), dtype=np.uint8)

    def kill(self):
        if self.camera_frames_cap is not None:
            self.camera_frames_cap.release()
        if self.video_frames_cap is not None:
            self.video_frames_cap.release()
        if self.open_face_video_frames_cap is not None:
            self.open_face_video_frames_cap.release()
        
        self.stop_threads = True
        
        for p in self.processes:
            p.join()

    def stop(self):
        # Window.fullscreen = self.initial_window_state
        if self.video_interval is not None:
            # cancel schedule
            self.video_interval.cancel()
            # nullifies the schedule handle
            self.video_interval = None
            # reset the timeline index
        self.reset()
        self.end_play_cb(arg=None)
    
    def get_is_exporting(self):
        return self.is_exporting_busy

    def export_as_video(self, video_path,
                        session_timeline_path, cam_video_path,
                        bg_is_screen, video_track,
                        camera_track, tracker_track, maintain_track, 
                        export_frame_cb=video_export_progress_cb):

        if self.get_is_exporting():
            self.is_exporting_busy = False
            self.__tracker_app_log(get_local_str_util("_export_module_busy"))
            return 

        self.is_exporting_busy = True
        

        if not os.path.isfile(session_timeline_path):
            self.is_exporting_busy = False
            self.__tracker_app_log(get_local_str_util("_session_timeline_not_found"))
            return

        if not bg_is_screen and not camera_track and not tracker_track and not maintain_track:
            # this is just the existing cumulative video
            export_frame_cb(current=100,total=100)
            self.is_exporting_busy = False
            self.__tracker_app_log(get_local_str_util("_video_exists"))
            return

        if not bg_is_screen and not video_track and not tracker_track and not maintain_track:
            # this is just the existing camera video
            export_frame_cb(current=100,total=100)
            self.is_exporting_busy = False
            self.__tracker_app_log(get_local_str_util("_video_exists"))
            return

        root_path = os.sep.join(session_timeline_path.split(os.sep)[:-1])
        export_name_ext = "screen_bg-{}-video_track-{}-camera_track-{}-tracker_track-{}-track_path-{}.avi".format(int(bg_is_screen), int(video_track), int(camera_track), int(tracker_track), int(maintain_track))

        export_name = os.path.join(root_path, export_name_ext)

        if os.path.isfile(export_name):
            export_frame_cb(current=100,total=100)
            self.is_exporting_busy = False
            self.__tracker_app_log(get_local_str_util("_video_exists"))
            return

        session_timeline = {}
        try:
            with open(session_timeline_path, "r") as fp:
                session_timeline = json.load(fp)
                fp.close()
        except Exception as err:
            self.__tracker_app_log(get_local_str_util("_session_timeline_corrupted"))
            file_log("[ERROR] occurred while reading session data {}".format(err))

        SCREEN_SIZE = ImageGrab.grab().size
        bg_image = np.zeros((SCREEN_SIZE[1], SCREEN_SIZE[0], 3), dtype=np.uint8)

        image_grab_path = os.sep.join(session_timeline_path.split(os.sep)[:-1])
        image_grab_path = os.path.join(image_grab_path, "screen.png")

        if os.path.isfile(image_grab_path):
            bg_image = cv2.imread(image_grab_path)
            SCREEN_SIZE = bg_image.shape

        bg_frame = np.zeros((SCREEN_SIZE[0], SCREEN_SIZE[1], 3), dtype=np.uint8)

        timestamp_keys = [i for i in session_timeline.keys()]
        
        len_keys = len(timestamp_keys)

        if len_keys == 0:
            error_text = "[ERROR] timeline is empty"
            self.__tracker_app_log(get_local_str_util("_session_timeline_empty"))
            self.is_exporting_busy = False
            return

        path_history = deque()

        if not os.path.isfile(video_path):
            self.is_exporting_busy = False
            self.__tracker_app_log(get_local_str_util("_src_video_not_exists"))
            return

        video_frames = deque()
        camera_frames = deque()
        video_capture = cv2.VideoCapture(video_path)

        camera_capture = None
        if os.path.isfile(cam_video_path):
            camera_capture = cv2.VideoCapture(cam_video_path)

        float_timestamp_keys = [float(i) for i in timestamp_keys]
        diff = max(float_timestamp_keys) - min(float_timestamp_keys)

        vid_fps = len_keys/max(diff,1)

        counter = 0
        current_vid_frame_id = 0
        v_frame = None
        current_cam_frame_id = 0
        c_frame = None

        # define video writer
        fourcc = cv2.VideoWriter_fourcc('M', 'J', 'P', 'G')
        out_video = cv2.VideoWriter()
        sh = bg_frame.shape
        success = out_video.open(export_name, fourcc, vid_fps, (sh[1], sh[0]), True)
        # loop through the frames
        self.__tracker_app_log(get_local_str_util("_video_export_commences"))
        for key in timestamp_keys:
            counter += 1
            record = session_timeline[key]
            if self.__get_stop_threads():
                break
            
            if record["video"] is not None:
                if current_vid_frame_id != record["video"]["frame_id"]:
                    current_vid_frame_id = record["video"]["frame_id"]

                    if video_capture.isOpened():
                        ret, v_frame = video_capture.read()
                        if not ret:
                            video_capture.release()

            if record["camera"] is not None:
                if current_cam_frame_id != record["camera"]["frame_id"]:
                    current_cam_frame_id = record["camera"]["frame_id"]

                    if camera_capture.isOpened():
                        ret, c_frame = camera_capture.read()
                        if not ret:
                            camera_capture.release()

            output_frame, path_history = self.fast_frames_cb(bg_frame, bg_image, record, v_frame, c_frame,
                                                             bg_is_screen=bg_is_screen, video_track=video_track,
                                                             camera_track=camera_track, tracker_track=tracker_track,
                                                             maintain_track=maintain_track, path_history=path_history)

            out_video.write(output_frame)
            # update export progress
            
            export_frame_cb(current=counter, total=len_keys)
        # release worker
        self.__tracker_app_log(get_local_str_util("_export_video_finished"))
        out_video.release()
        camera_capture.release()
        video_capture.release()

        self.is_exporting_busy = False

    def fast_frames_cb(self, bg_frame, bg_image, record, v_frame, c_frame,
                       bg_is_screen=False, video_track=True,
                       camera_track=False, tracker_track=True, maintain_track=True, path_history=deque()):

        bg_frame[:, :, :] = 255
        # show current screen as background
        if bg_is_screen:
            bg_frame[:, :, :] = bg_image

        # add video feed data
        if video_track and record.get("video", None) and v_frame is not None:
            if "width" in record.get("video", None):
                sz = (int(record["video"]["width"]), int(record["video"]["height"]))
                v_frame = cv2.resize(v_frame, sz)

                v_x = int(record["video"]["x"])
                v_y = int(record["video"]["y"])

                bg_frame[v_y:v_frame.shape[0] + v_y, v_x:v_frame.shape[1] + v_x, :] = v_frame

        # add camera feed data
        if camera_track and c_frame is not None:
            rel_w = 0.25 * bg_frame.shape[1]
            rel_h = rel_w * bg_frame.shape[0]/ bg_frame.shape[1]
            sh = (int(rel_w), int(rel_h))
            c_frame = cv2.resize(c_frame, sh)

            start_x = bg_frame.shape[1] - sh[0]
            bg_frame[:sh[1], start_x:, :] = c_frame

        xo = None
        yo = None
        # add gaze feed data
        if record.get("gaze", None) is not None and tracker_track:
            xr = record["gaze"]['x']
            yr = record["gaze"]['y']

            xo = int(bg_frame.shape[1] * xr)
            yo = int(bg_frame.shape[0] * yr)

            path_history.append((xo, yo))

        if xo is not None and yo is not None and tracker_track:
            bg_frame = cv2.circle(bg_frame, (xo, yo),
                                       self.radius, self.color, self.thickness)
            if maintain_track:
                # write all the positions of the track from 0 - this index
                for i in path_history:
                    bg_frame = cv2.circle(bg_frame, (i[0], i[1]), 2, (0, 0, 255, 1), self.thickness)

        return bg_frame, path_history
