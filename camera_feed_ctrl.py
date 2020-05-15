import time
import cv2
from threading import Thread
import json
from PIL import ImageGrab
from collections import deque
import numpy as np
import os
import sys
from eye_utilities.helpers import get_local_str_util
import platform

class Frame:
    timestamp = 0  # double
    frame_id = 0  # long
    img_data = None  # numpy Mat object

    def __init__(self, frame_id, f=None):
        self.timestamp = time.time()
        self.frame_id = frame_id
        self.img_data = f

    def update(self):
        self.timestamp = time.time()

    def to_dict(self):
        return {
            "timestamp": self.timestamp,
            "frame_id": self.frame_id
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

    def start(self, output_path='./',
              camera_index=0, save_images=False):
        self.cam_th = Thread(target=self.__camera_thread, args=(output_path, camera_index, save_images))
        self.camera_frames.clear()
        self.stop_session = False
        try:
            self.cam_th.start()
            # wait till camera is up
            polling_camera_times = 0
            while not self.__get_camera_is_up():
                print("[INFO] waiting for camera {}     ".format(time.strftime("%H:%M:%S")))
                time.sleep(1)
                polling_camera_times += 1
                if polling_camera_times > 5:
                    print("[INFO] got tired of waiting for camera {}    ".format(time.strftime("%H:%M:%S")))
                    self.stop()
                    return False

            return True # camera has started 
        except KeyboardInterrupt:
            self.stop()
        except Exception as e:
            print("{} {}    ".format(e, time.strftime("%H:%M:%S")))
            self.stop()

    def __get_camera_is_up(self):
        return self.camera_is_up

    def stop(self):
        self.stop_session = True
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
        sys.stdout.flush()
        st = time.time()
        while cap.isOpened() and not self.__halt_recording():
            ret, frame = cap.read()
            self.camera_is_up = True
            if ret:
                if save_images:
                    self.camera_frames.append(Frame(frame_id, frame))
                else:
                    self.camera_frames.append(Frame(frame_id, None))
                out.write(frame)
            else:
                break
            frame_id += 1
        time_diff = time.time() - st
        print("[INFO] stopping the camera feed {}    ".format(time.strftime("%H:%M:%S")))
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