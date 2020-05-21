from kivy.uix.gridlayout import GridLayout
from kivy.lang.builder import Builder
from kivy.uix.button import Button
import os
import json
import math
from eye_utilities.helpers import get_local_str_util
from datetime import datetime

widget = Builder.load_file(os.path.join(os.path.dirname(__file__), "framedetails.kv"))


class FrameDetails(GridLayout):

    def build(self):
        return widget

    def get_local_str(self, key):
        return get_local_str_util(key)

    def update_key(self, label, key, value):
        id_in_ids = "lbl_{}_{}".format(label, key)
        if id_in_ids in self.ids:
            self.ids[id_in_ids].text = value

    def update(self, frame_details):
        # print(frame_details)
        gaze = frame_details.get("gaze", {"timestamp": 0})
        if gaze is None:
            gaze = {"timestamp": 0}
        video = frame_details.get("video", {"timestamp": 0})
        if video is None:
            video = {"timestamp": 0}
        camera = frame_details.get("camera", {"timestamp": 0})
        if camera is None:
            camera = {"timestamp": 0}

        ts_tracker = datetime.utcfromtimestamp(gaze.get("timestamp", 0)).strftime("%H:%M:%S.%f")[:-3]
        self.update_key("tracker", "time", ts_tracker)
        ts_video = datetime.utcfromtimestamp(video.get("timestamp", 0)).strftime("%H:%M:%S.%f")[:-3]
        self.update_key("video", "time", ts_video)
        ts_camera = datetime.utcfromtimestamp(camera.get("timestamp", 0)).strftime("%H:%M:%S.%f")[:-3]
        self.update_key("camera", "time", ts_camera)
