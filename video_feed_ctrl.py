#!/usr/bin/python

from kivy.uix.image import Image
from kivy.graphics.texture import Texture
from kivy.clock import Clock
import json
from eye_utilities.helpers import  frame_processing, process_fps

from kivy.core.window import Window
import cv2
from collections import deque
from camera_feed_ctrl import Frame

from kivy.config import Config

Config.set('graphics', 'kivy_clock', 'free_all')
Config.set('graphics', 'maxfps', 0)


class VideoCanvas(Image):
    video_frames = deque()
    video_frame_index = 0
    video_interval = None

    actual_video_stimuli_fps = None
    video_capture = None

    initial_window_state = Window.fullscreen

    def is_playing(self):
        return self.video_interval is not None

    def start(self, video_src="",
              fps=1000, is_recording=True):

        print("[INFO] started")

        # if playing stop
        if self.video_interval is not None:
            self.stop()
            return 1

        # can't run if video not ready can we?
        # if get_video_fps(video_src):
        #     return -1

        # ensures we are full screen
        self.initial_window_state = Window.fullscreen
        # Window.fullscreen = 'auto'

        # play video
        return self.play(video_src, fps, is_recording)

    def frames_cb(self, frame):
        frame = frame_processing(frame)
        self.video_frames.append(Frame(self.video_frame_index))
        self.video_frame_index += 1
        return frame

    def play(self, video_src, fps, is_recording=True):
        cb = lambda f: f
        if is_recording:
            self.video_frames.clear()
            self.video_frame_index = 0
            cb = self.frames_cb

        self.video_capture = cv2.VideoCapture(video_src)

        em_fps = self.video_capture.get(cv2.CAP_PROP_FPS)
        if fps == 0:
            fps = em_fps

        if fps == 0:
            return

        self.video_interval = Clock.schedule_interval(lambda dt:
                                                      self.update_video_canvas(dt, self.video_capture, cb), 1.0/fps)
        return 0

    def stop(self, cb=lambda: print("[INFO] video playing ")):
        # stop video feed
        # we are not even running, are we?
        if self.video_capture is None:
            return

        self.video_capture.release()

        # viewpoint_size = (Window.width, Window.height)

        # Window.fullscreen = self.initial_window_state

        if self.video_interval is not None:
            # cancel schedule
            self.video_interval.cancel()
            # nullifies the schedule handle
            self.video_interval = None
            # get actual FPS details for stimuli video
            info_1, info_2, self.actual_video_stimuli_fps = process_fps(self.video_frames)
        cb()

    def get_actual_fps(self):
        return self.actual_video_stimuli_fps

    def update_video_canvas(self, dt, cap, cb):
        # get the canvas for drawing
        # read next frame
        ret, frame = cap.read()
        if not ret:
            # end of video
            self.stop()
            return
        # do the callback for video frame, e.g add some color or some text, real time rendering
        frame = cb(frame)

        buf_raw = cv2.flip(frame, 0)
        buf = buf_raw.tostring()
        texture = Texture.create(size=(frame.shape[1], frame.shape[0]), colorfmt='bgr')

        texture.blit_buffer(buf, colorfmt='bgr', bufferfmt='ubyte')
        # update video canvas
        self.texture = texture


    def get_json(self):
        return [i.to_dict() for i in self.video_frames]

    def save_json(self, path=b"./results.json"):
        with open(path, "w") as f:
            f.write(json.dumps(self.get_json()))
            f.close()

