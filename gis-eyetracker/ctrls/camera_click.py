from kivy.app import App
from kivy.lang import Builder
from kivy.uix.camera import Camera
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock

from kivy.graphics.texture import Texture
from kivy.properties import ObjectProperty
import itertools
import cv2 
import os
import numpy as np

from helpers.cam_calibrator_utils import Calibrator
from helpers import get_local_str_util, get_app_dir

APP_DIR = get_app_dir()
widget = Builder.load_file(os.path.join(APP_DIR, "settings", "subscreens", "camera_click.kv"))

class CameraClick(BoxLayout):
    is_playing = True
    video_cap = None
    video_interval = None
    index = ObjectProperty(None)

    def build(self):
        pass

    @staticmethod
    def get_local_str(key):
        # gets the localized string for literal text on the UI
        return get_local_str_util(key)

    def on_stop(self):
        self.stop_interval()

    def start_interval(self):
        self.video_cap = cv2.VideoCapture(self.index)
        fps = self.video_cap.get(cv2.CAP_PROP_FPS)
        interval = max(fps, 5)/1000
        self.update_image(None)
        self.video_interval = Clock.schedule_interval(self.update_image, interval)

    def stop_interval(self):
        if self.video_interval is not None:
            self.video_interval.cancel()
        
        if self.video_cap is not None:
            self.video_cap.release()

    def update_image(self, dt):
        if not self.is_playing:
            return 0

        if self.video_cap is None:
            self.stop_interval()
            return 0
        
        ret, frame = self.video_cap.read()
        if not ret:
            self.stop_interval()
            return 0

        frame = cv2.flip(frame, 0)

        buf = frame.tostring()
        texture = Texture.create(size=(frame.shape[1], frame.shape[0]), colorfmt='bgr')
        texture.blit_buffer(buf, colorfmt='bgr', bufferfmt='ubyte')

        self.ids['camera'].texture = texture

    def capture(self):
        '''
    	Take a photo when you push "capture"
    	'''

        CAL = Calibrator()
        
        camera = self.ids['camera']

        nparr = np.fromstring(self.ids['camera'].texture.pixels, dtype=np.uint8)
        
        a = np.reshape(nparr, (int(camera.texture.height),int(camera.texture.width), 4))

        CAL.fit_calibrator_from_stream(a, camera_index = self.index)
