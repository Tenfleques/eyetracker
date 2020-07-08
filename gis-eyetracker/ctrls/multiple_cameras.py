from kivy.app import App
from kivy.lang import Builder
from kivy.uix.camera import Camera
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock

from kivy.graphics.texture import Texture
from ctrls.camera_click import CameraClick
import itertools
import cv2 
import os

from helpers.cam_calibrator_utils import Calibrator
from helpers import get_local_str_util, create_log, get_video_fps, props, get_default_from_prev_session, set_default_from_prev_session, file_log, get_app_dir

APP_DIR = get_app_dir()
widget = Builder.load_file(os.path.join(APP_DIR, "settings", "subscreens", "muliticams_calibrator.kv"))

def discover_cameras():
    cap = cv2.VideoCapture()
    nums_ind = []
    for i in itertools.count(start=0):
        if cap.open(i):
            nums_ind.append(i)
        else:
            break
    cap.release()

    return nums_ind

class MultipleCameras(BoxLayout):
    @staticmethod
    def get_local_str(key):
        # gets the localized string for literal text on the UI
        return get_local_str_util(key)

    def start_all(self):
        ids = discover_cameras()
        
        for cam_index in ids:
            
            widget = CameraClick(index=cam_index)
            widget.start_interval()
            self.ids["cameras_zone"].add_widget(widget)


class TestCamera(App):
    def build(self):
        mcs = MultipleCameras()
        mcs.start_all()
        return mcs

if __name__ == "__main__":
    TestCamera().run()
