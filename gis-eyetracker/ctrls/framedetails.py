from kivy.uix.gridlayout import GridLayout
from kivy.lang.builder import Builder
from kivy.uix.button import Button
import os
import json
import math
from helpers import get_local_str_util
from datetime import datetime

p = os.path.dirname(__file__)
p = os.path.dirname(p)
widget = Builder.load_file(os.path.join(p, "framedetails.kv"))


class FrameDetails(GridLayout):

    def build(self):
        return widget

    def get_local_str(self, key):
        return get_local_str_util(key)

    def update_key(self, label, key, value):
        if isinstance(value, float):
            value = datetime.utcfromtimestamp(value).strftime("%H:%M:%S.%f")[:-3]
        
        
        id_in_ids = "lbl_{}_{}".format(label, key)
        if id_in_ids in self.ids:
            self.ids[id_in_ids].text = str(value)

    def update(self, **kwargs):
        frame_details = kwargs.get("frame_details", None)

        self.ids["lbl_video_fps"].text = "{:.4}".format(kwargs.get("vid_fps", self.ids["lbl_video_fps"].text))
        self.ids["lbl_tracker_gaze_fps"].text = "{:.4}".format(kwargs.get("gaze_fps", self.ids["lbl_tracker_gaze_fps"].text))
        self.ids["lbl_tracker_origin_fps"].text = "{:.4}".format(kwargs.get("gaze_fps", self.ids["lbl_tracker_origin_fps"].text))
        self.ids["lbl_tracker_pos_fps"].text = "{:.4}".format(kwargs.get("gaze_fps", self.ids["lbl_tracker_pos_fps"].text))
        self.ids["lbl_camera_fps"].text = "{:.4}".format(kwargs.get("cam_fps", self.ids["lbl_camera_fps"].text))

        if frame_details is not None:
            gaze = frame_details.get("gaze", {"timestamp": 0})
            if gaze is None:
                gaze = {"timestamp": 0}
            video = frame_details.get("video", {"timestamp": 0})
            if video is None:
                video = {"timestamp": 0}
            camera = frame_details.get("camera", {"timestamp": 0})
            if camera is None:
                camera = {"timestamp": 0}
            pos = frame_details.get("pos", {"timestamp": 0})
            if pos is None:
                pos = {"timestamp": 0}
            origin = frame_details.get("origin", {"timestamp":0})
            if origin is None:
                origin = {"timestamp": 0}

            self.update_key("tracker_gaze", "time", gaze.get("timestamp", 0))
            self.update_key("tracker_pos", "time", pos.get("timestamp", 0))
            self.update_key("tracker_origin", "time", origin.get("timestamp", 0))
            self.update_key("video", "time", video.get("timestamp", 0))
            self.update_key("camera", "time", camera.get("timestamp", 0))
