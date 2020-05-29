#!/usr/bin/python

from kivy.uix.image import Image
from kivy.graphics.texture import Texture
from kivy.clock import Clock

from kivy.core.window import Window
import cv2
import json
import numpy as np
from PIL import ImageGrab
import os
import time
from kivy.config import Config
from collections import deque

Config.set('graphics', 'kivy_clock', 'free_all')
Config.set('graphics', 'maxfps', 0)


class ResultVideoCanvas(Image):
    session_timeline = {}
    session_timeline_index = 0
    timestamp_keys = []
    video_fps = None

    is_paused = False

    video_frame_index = 0
    video_interval = None

    video_capture = None
    bg_frame = None

    current_vid_frame_id = 0

    initial_window_state = Window.fullscreen
    # for writing tracke on the video
    radius = 10
    color = (0, 255, 0)
    thickness = 2

    v_frame = None
    c_frame = None

    sh = []
    v_x = 0.0
    v_y = 0.0
    current_cam_frame_id = 0

    xo = None
    yo = None
    c_width = None
    c_height = None
    c_start_x = None

    bg_is_screen = False
    maintain_track = False

    path_history = deque()

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

    def is_playing(self):
        return self.video_interval is not None

    def end_play_cb(self, **kwargs):
        pass

    def get_progress(self):
        return self.session_timeline_index, len(self.timestamp_keys)

    def get_fps(self):
        return self.video_fps

    def current_frame_cb(self, current, total, record=None):
        print("[INFO] frame {}/{}".format(current, total))

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
        self.video_fps = video_fps
        if self.video_interval is not None:
            self.video_interval.cancel()
            self.video_interval = Clock.schedule_interval(self.update_video_canvas, 1.0/self.video_fps)
            if self.is_paused:
                self.video_interval.cancel()

    def step_to_frame(self, index):
        if isinstance(index, float):
            len_tl = len(self.timestamp_keys)
            index = min(int(index), len_tl - 1)

        if not isinstance(index, int):
            return

        if self.video_interval is not None:
            # pause the playback for a moment
            if not self.is_paused:
                self.video_interval.cancel()

        self.session_timeline_index = index

        if not self.is_paused and self.video_interval is not None:
            self.video_interval()

        self.update_video_canvas(1)

    def step_forward(self, step_size):
        if self.video_interval is None:
            return

        len_tl = len(self.timestamp_keys) - 1
        self.session_timeline_index = min(self.session_timeline_index + step_size, len_tl)
        self.update_video_canvas(1)

    def step_backward(self, step_size):
        if self.video_interval is None:
            return

        self.session_timeline_index = max(self.session_timeline_index - step_size, 0)
        self.update_video_canvas(1)

    def start(self, video_path,
              session_timeline_path, viewpoint_size, cam_video_path,
              current_frame_cb, end_cb):

        if end_cb is not None:
            self.end_play_cb = end_cb
        if current_frame_cb is not None:
            self.current_frame_cb = current_frame_cb

        with open(session_timeline_path, "r") as fp:
            self.session_timeline = json.load(fp)
            fp.close()

        SCREEN_SIZE = viewpoint_size
        if viewpoint_size is None:
            SCREEN_SIZE = ImageGrab.grab().size

        image_grab_path = os.sep.join(session_timeline_path.split(os.sep)[:-1])
        image_grab_path = os.path.join(image_grab_path, "screen.png")

        self.bg_image = np.zeros((SCREEN_SIZE[1], SCREEN_SIZE[0], 3), dtype=np.uint8)
        self.bg_frame = np.zeros((SCREEN_SIZE[1], SCREEN_SIZE[0], 3), dtype=np.uint8)
        if os.path.isfile(image_grab_path):
            self.bg_image = cv2.imread(image_grab_path)
            self.bg_frame[:, :, :] = self.bg_image

    
        self.timestamp_keys = [i for i in self.session_timeline.keys()]
        float_timestamp_keys = [float(i) for i in self.timestamp_keys]
        len_keys = len(self.timestamp_keys)

        if len_keys == 0:
            error_text = "[ERROR] timeline is empty"
            end_cb(error_text)
            print(error_text)
            return

        if self.session_timeline_index >= len_keys - 1:
            self.session_timeline_index = 0
        
        self.path_history.clear()

        self.video_capture = cv2.VideoCapture(video_path)
        self.camera_capture = None

        if os.path.isfile(cam_video_path):
            self.camera_capture = cv2.VideoCapture(cam_video_path)

        if not self.video_capture.isOpened():
            print("[INFO] error opening stimuli video {}    ".format(time.strftime("%H:%M:%S")))
            return

        fourcc = cv2.VideoWriter_fourcc('M', 'J', 'P', 'G')
        self.out_video = cv2.VideoWriter()

        diff = max(float_timestamp_keys) - min(float_timestamp_keys)

        if self.video_fps is None:
            self.set_fps(len_keys / (diff * 3)) # multiplies by three coz of gaze, pos, and origin 

        demo_video_path = cam_video_path.replace(".avi", "-demonstration.avi")

        success = self.out_video.open(demo_video_path, fourcc, self.video_fps,
                                      (self.bg_frame.shape[1], self.bg_frame.shape[0]), True)

        self.sh = [int(self.video_capture.get(cv2.CAP_PROP_FRAME_WIDTH)),
                   int(self.video_capture.get(cv2.CAP_PROP_FRAME_HEIGHT))]

        self.c_start_x = self.sh[0] + 40
        self.v_x, self.v_y = (0, 0)

        if self.camera_capture is not None:
            w, h = (self.camera_capture.get(cv2.CAP_PROP_FRAME_WIDTH),
                    self.camera_capture.get(cv2.CAP_PROP_FRAME_HEIGHT))

            self.c_width = SCREEN_SIZE[0] - self.c_start_x
            self.c_height = int(h * self.c_width / w)

        self.current_vid_frame_id = 0
        self.current_cam_frame_id = 0
        self.v_frame = None
        self.c_frame = None
        self.xo = None
        self.yo = None

        # if playing stop
        if self.video_interval is not None:
            self.stop()
            return 1

        # ensures we are full screen
        # self.initial_window_state = Window.fullscreen
        # Window.fullscreen = 'auto'

        print("[INFO] entering video loop. FPS: {}".format(self.video_fps))
        # play video
        self.pause_play()

    def update_video_canvas(self, dt):
        # read next frame
        frame = self.bg_frame
        if dt:
            frame = self.frames_cb(dt)

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

    def frames_cb(self, dt=True):
        # dt is None when called from stop to stop recursions
        if self.bg_is_screen:
            self.bg_frame[:, :, :] = self.bg_image
        else:
            self.bg_frame[:, :, :] = 255
        
        if not self.video_capture:
            self.stop()
            return None
            
        if not self.video_capture.isOpened() and dt:
            self.stop()
            return None

        len_timeline = len(self.timestamp_keys)

        if self.session_timeline_index >= len_timeline:
            self.stop()
            return None

        key = self.timestamp_keys[self.session_timeline_index]
        record = self.session_timeline[key]

        if record["video"] is not None:
            if not record["video"]["frame_id"] == self.current_vid_frame_id:
                ret, self.v_frame = self.video_capture.read()
                if not ret:
                    return

                if "width" in record["video"]:
                    # updated version with cordinates
                    self.v_frame = cv2.resize(self.v_frame, (int(record["video"]["width"]),
                                                             int(record["video"]["height"])))
                    self.v_x = int(record["video"]["x"])
                    self.v_y = int(record["video"]["y"])
                    self.sh[0] = int(record["video"]["width"])
                    self.sh[1] = int(record["video"]["height"])

                    self.c_start_x = self.v_x + self.sh[0] + 40

                self.current_vid_frame_id = record["video"]["frame_id"]

        try:
            if self.v_frame is not None:
                self.bg_frame[self.v_y:self.sh[1] + self.v_y, self.v_x:self.sh[0] + self.v_x, :] = self.v_frame
        except ValueError as verr:
            print("[ERROR] a video resize error occured ")

        # add gaze feed data
        if record["gaze"] is not None:
            xr = record["gaze"]['x']
            yr = record["gaze"]['y']

            self.xo = int(self.bg_frame.shape[1] * xr)
            self.yo = int(self.bg_frame.shape[0] * yr)

            self.path_history.append((self.xo, self.yo))

        if self.xo is not None and self.yo is not None:
            self.bg_frame = cv2.circle(self.bg_frame, (self.xo, self.yo),
                                       self.radius, self.color, self.thickness)
            if self.maintain_track:
                # write all the positions of the track from 0 - this index
                for i in self.path_history:
                    self.bg_frame = cv2.circle(self.bg_frame, (i[0], i[1]),
                                       2, (0,0,255,1), self.thickness)

        # add camera feed data
        if self.camera_capture is not None:
            if self.camera_capture.isOpened():
                if record["camera"] is not None:
                    if not record["camera"]["frame_id"] == self.current_cam_frame_id:
                        ret, self.c_frame = self.camera_capture.read()
                        self.current_cam_frame_id = record["camera"]["frame_id"]
                        if ret:
                            self.c_frame = cv2.resize(self.c_frame, (self.c_width, self.c_height))

        if self.c_frame is not None:
            b_sh = self.bg_frame.shape
            self.bg_frame[:self.c_height, b_sh[1] - self.c_width:, :] = self.c_frame
        self.video_frame_index += 1

        self.current_frame_cb(self.session_timeline_index, len_timeline, record)

        if dt:
            self.session_timeline_index += 1

        self.out_video.write(self.bg_frame)
        return self.bg_frame

    def stop(self):
        # stop video feed
        # we are not even running, are we?
        if self.video_capture is None:
            return

        self.video_capture.release()
        if self.camera_capture is not None:
            self.camera_capture.release()
        self.out_video.release()

        # viewpoint_size = (Window.width, Window.height)

        # Window.fullscreen = self.initial_window_state

        if self.video_interval is not None:
            # cancel schedule
            self.video_interval.cancel()
            # nullifies the schedule handle
            self.video_interval = None
            # reset the timeline index
            # self.session_timeline_index = 0

        self.update_video_canvas(None)
        self.end_play_cb("")

    def get_json(self):
        return [i.to_dict() for i in self.video_frames]

    def save_json(self, path=b"./results.json"):
        with open(path, "w") as f:
            f.write(json.dumps(self.get_json()))
            f.close()
