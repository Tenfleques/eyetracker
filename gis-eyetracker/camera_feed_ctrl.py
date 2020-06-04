from kivy.app import App
import time
import cv2
from threading import Thread
from collections import deque
import os
import sys
from helpers import get_local_str_util

import logging
logging.basicConfig(filename='./logs/camera_feed_ctrl.log',level=logging.DEBUG)


class Frame:
    timestamp = 0  # double
    frame_id = 0  # long
    img_data = None  # numpy Mat object
    x = 0.0
    y = 0.0
    width = 0.0
    height = 0.0

    def __init__(self, frame_id, coords=(0, 0, 0, 0), f=None):
        self.timestamp = time.time()
        self.frame_id = frame_id
        self.img_data = f
        self.x, self.y, self.width, self.height = coords

    def update(self):
        self.timestamp = time.time()

    def to_dict(self):
        return {
            "timestamp": self.timestamp,
            "frame_id": self.frame_id,
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height
        }

    def save_to_file(self, path):
        images_path = path + "/"

        if path.endswith("/"):
            images_path = path

        return cv2.imwrite(self.img_data, "{}frame-{}.png".format(images_path, self.frame_id))


class CameraFeedCtrl:
    camera_frames = deque()
    stop_session = True
    camera_is_up = False
    cam_th = None

    @staticmethod
    def __tracker_app_log(text, log_label='app_log'):
        # give feedback to the user of what is happening behind the scenes
        app = App.get_running_app()
        try:
            app.tracker_app_log(text, log_label)
        except Exception as er:
            print("[ERROR] {}".format(er))

    def start(self, output_path='./',
              camera_index=0, save_images=False):
        self.cam_th = Thread(target=self.__camera_thread, args=(output_path, camera_index, save_images))
        self.camera_frames.clear()
        self.stop_session = False
        try:
            self.cam_th.start()
            # wait till camera is up
            polling_camera_times = 0
            while not self.get_camera_is_up():
                print("[INFO] waiting for camera {}     ".format(time.strftime("%H:%M:%S")))
                self.__tracker_app_log(get_local_str_util("_waiting_for_camera"), "camera_log")
                time.sleep(1)
                polling_camera_times += 1
                if polling_camera_times > 10:
                    print("[INFO] got tired of waiting for camera {}    ".format(time.strftime("%H:%M:%S")))
                    self.__tracker_app_log(get_local_str_util("_gave_up_waiting_camera"), "camera_log")
                    self.stop()
                    return False

            self.__tracker_app_log(get_local_str_util("_started_camera"), "camera_log")
            return True  # camera has started
        except KeyboardInterrupt:
            self.stop()
        except Exception as e:
            print("{} {}    ".format(e, time.strftime("%H:%M:%S")))
            self.__tracker_app_log("[ERROR] {}".format(e), "camera_log")
            self.stop()

    def get_camera_is_up(self):
        return self.camera_is_up

    def stop(self):
        self.stop_session = True
        if self.cam_th is not None:
            self.cam_th.join()

    def __halt_recording(self):
        return self.stop_session

    @staticmethod
    def __video_output(output_path, fps, frame_width, frame_height):
        """

        :param output_path:
        :param fps:
        :param frame_width:
        :param frame_height:
        :return:
        """
        video_filename = os.path.join(output_path, 'out-video.avi')

        frame_width = int(frame_width)
        frame_height = int(frame_height)

        fourcc = cv2.VideoWriter_fourcc('M', 'J', 'P', 'G')
        out = cv2.VideoWriter()

        success = out.open(video_filename, fourcc, fps, (frame_width, frame_height), True)
        print("[INFO] opening the output video for writing success: {} {}    "
              .format(success, time.strftime("%H:%M:%S")))
        return out

    def __camera_thread(self, output_path, camera_index=0, save_images=False):
        """

        :param output_path:
        :param camera_index:
        :param fps:
        :param save_images:
        :return:
        """
        cap = cv2.VideoCapture(camera_index)
        frame_id = 0
        actual_fps = None
        frame_width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        frame_height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        fps = cap.get(cv2.CAP_PROP_FPS)

        out = self.__video_output(output_path, fps, frame_width, frame_height)

        print("[INFO] starting the camera feed {}    ".format(time.strftime("%H:%M:%S")))
        self.__tracker_app_log(get_local_str_util("_started_camera"), "camera_log")
        sys.stdout.flush()
        st = time.time()
        while cap.isOpened() and not self.__halt_recording():
            ret, frame = cap.read()
            self.camera_is_up = True
            if ret:
                if save_images:
                    self.camera_frames.append(Frame(frame_id, f=frame))
                else:
                    self.camera_frames.append(Frame(frame_id, f=None))
                out.write(frame)
            else:
                break
            frame_id += 1
        time_diff = time.time() - st
        self.__tracker_app_log(get_local_str_util("_stopped_camera"), "camera_log")
        sys.stdout.flush()
        if time_diff:
            actual_fps = (frame_id + 1) / time_diff
        cap.release()
        out.release()
        self.camera_is_up = False
        return frame_id, actual_fps

    def save_images(self, path):
        """
        :param path:
        :return:
        """
        for (i, frame) in enumerate(self.camera_frames):
            frame.save_to_file(path)

    def get_frames(self):
        return self.camera_frames

    def get_json(self):
        return [i.to_dict() for i in self.camera_frames]
