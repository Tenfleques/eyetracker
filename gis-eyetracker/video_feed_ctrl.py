#!/usr/bin/python

from kivy.uix.image import Image
from kivy.graphics.texture import Texture
from kivy.clock import Clock
import json
from helpers import frame_processing, process_fps, get_video_fps, props

from kivy.core.window import Window
import cv2
from collections import deque
from camera_feed_ctrl import Frame
from kivy.lang.builder import Builder

from kivy.config import Config
import logging
import numpy as np

logging.basicConfig(filename='~/logs/video_feed_ctrl.log', level=logging.DEBUG)

Config.set('graphics', 'kivy_clock', 'free_all')
Config.set('graphics', 'maxfps', 0)


class VideoCanvas(Image):
    video_frames = deque()
    video_frame_index = 0
    video_interval = None

    actual_video_stimuli_fps = None
    video_capture = None

    initial_window_state = Window.fullscreen

    def on_start(self):
        frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        buf = frame.tostring()
        texture = Texture.create(size=(frame.shape[1], frame.shape[0]), colorfmt='bgr')

        texture.blit_buffer(buf, colorfmt='bgr', bufferfmt='ubyte')

        self.texture = texture

    def is_playing(self):
        return self.video_interval is not None

    def end_play_cb(self, **kwargs):
        pass

    def get_progress(self):
        return self.session_timeline_index, len(self.timestamp_keys)

    def current_frame_cb(self, current, total):
        print("[INFO] frame {}/{}".format(current, total))

    def start(self, video_src="",
              fps=1000, is_recording=True, current_frame_cb=None, end_cb=None):

        if end_cb is not None:
            self.end_play_cb = end_cb

        if current_frame_cb is not None:
            self.current_frame_cb = current_frame_cb

        # if playing stop
        if self.video_interval is not None:
            self.stop()
            return 1

        # can't run if video not ready can we?
        if not get_video_fps(video_src):
            return -1

        # ensures we are full screen
        self.initial_window_state = Window.fullscreen
        # Window.fullscreen = 'auto'

        # play video
        return self.play(video_src, fps, is_recording)

    def frames_cb(self, frame):
        frame = frame_processing(frame)

        # calculate position from top of screen

        xprime,yprime = self.to_window(self.x, self.y, False, False)
        app_window_bottom_pos_from_screen_top = Window.top + Window.height
        vid_start_pos = app_window_bottom_pos_from_screen_top - yprime  # start of video pos, after infobar
        vid_start_from_screen_top = vid_start_pos - self.height
        # x, y, width, height
        frame_coords = (Window.left + xprime, vid_start_from_screen_top, self.width, self.height)

        self.video_frames.append(Frame(self.video_frame_index, coords=frame_coords))
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

    def stop(self):
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

        self.end_play_cb()

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
#        print(props(self))

    def get_frames(self):
        return self.video_frames

    def get_json(self):
        return [i.to_dict() for i in self.video_frames]

    def save_json(self, path=b"./results.json"):
        with open(path, "w") as f:
            f.write(json.dumps(self.get_json()))
            f.close()

