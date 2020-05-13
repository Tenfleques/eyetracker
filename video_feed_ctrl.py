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


class VideoFeedCtrl:
    video_frames = deque()
    camera_frames = deque()
    stop_session = True
    camera_is_up = False
    frame_buffer = deque()
    video_meta = {
        "factual_fps": -1.0,
        "requested_fps": -1.0
    }
    camera_meta = {
        "factual_fps": -1.0,
        "requested_fps": -1.0
    }

    def __init__(self):
        self.SCREEN_SIZE = ImageGrab.grab().size

    def get_camera_meta(self, key=None):
        if key in self.camera_meta.keys():
            return self.camera_meta[key]
        return self.camera_frames

    def get_video_meta(self, key=None):
        if key in self.video_meta.keys():
            return self.video_meta[key]
        return self.video_meta

    def preprocess_video(self, video_path):
        cap = cv2.VideoCapture(video_path)
        win_name = video_path.split(os.sep)[-1]

        if not cap.isOpened():
            print("[ERROR] reading video {}    ".format(time.strftime("%H:%M:%S")))
            return
        self.__preprocessed_video(cap, win_name, 0, preprocess_only=True)

    def start(self, video_path, output_path='./', video_fps=0, camera_fps=0,
              camera_index=0, preprocess=True, save_images=False):
        self.stop_session = False
        print("[INFO] starting the video feed {}    ".format(time.strftime("%H:%M:%S")))

        self.video_meta["factual_fps"] = self.__video_thread(video_path, output_path, video_fps,
                                                             camera_fps, camera_index, preprocess, save_images)
        self.stop_session = True
        print("[INFO] closed the video feed {}    ".format(time.strftime("%H:%M:%S")))
        return self.stop_session

    def __get_camera_is_up(self):
        return self.camera_is_up

    def stop(self):
        self.stop_session = True

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

    def __camera_thread(self, output_path, camera_index=0, fps=0, save_images=False):
        """

        :param output_path:
        :param camera_index:
        :param fps:
        :param save_images:
        :return:
        """
        cap = cv2.VideoCapture(camera_index)
        frame_id = 0
        frame_width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        frame_height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        if fps == 0:
            fps = max(cap.get(cv2.CAP_PROP_FPS), 1)

        delay = 1000.0 / fps
        out = self.__video_output(output_path, fps, frame_width, frame_height)
        self.camera_meta["requested_fps"] = fps
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
            # time.sleep(delay / 1000)
            frame_id += 1

        time_diff = time.time() - st
        print("[INFO] stopping the camera feed {}    ".format(time.strftime("%H:%M:%S")))
        sys.stdout.flush()
        if time_diff:
            self.camera_meta["factual_fps"] = (frame_id + 1) / time_diff
        cap.release()
        out.release()
        self.camera_is_up = False
        return frame_id

    def __get_frame_buffer_front(self):
        if len(self.frame_buffer) > 0:
            frame = self.frame_buffer.popleft()
            return frame
        return None

    def __mem_queue_frames(self, cap, store_frames_in_memory=False):
        in_memory_already = False
        if len(self.video_frames):
            in_memory_already = self.video_frames[0].img_data is not None
        if in_memory_already:
            return

        print("[INFO] copying video frames to memory {}    ".format(time.strftime("%H:%M:%S")))
        sys.stdout.flush()
        bg_frame = np.zeros(shape=(self.SCREEN_SIZE[1], self.SCREEN_SIZE[0], 3), dtype=np.uint8)
        bg_frame[:, :, :] = 255
        font = cv2.FONT_HERSHEY_PLAIN
        color = (20, 20, 120)
        font_size = 1.1

        frame_id = 0
        while cap.isOpened():
            # Capture frame-by-frame
            ret, frame = cap.read()
            if ret:
                bg_frame = np.zeros(shape=(self.SCREEN_SIZE[1], self.SCREEN_SIZE[0], 3), dtype=np.uint8)
                bg_frame[:, :, :] = 255
                bg_frame[:frame.shape[0], :frame.shape[1], :] = frame
                cv2.putText(bg_frame, get_local_str_util("_press_q_to_quit"), (50, 80), font, font_size, color, 1, cv2.LINE_AA)

                self.frame_buffer.append(bg_frame)

                if store_frames_in_memory:
                    self.video_frames.append(Frame(frame_id, bg_frame))
            else:
                break
            frame_id += 1
        cap.release()

    def __preprocessed_video(self, cap, win_name, fps, preprocess_only=False):
        factual_rate = fps

        fps = max(fps, 1)
        delay = int(1000.0 / fps)
        queue_thread = Thread(target=self.__mem_queue_frames, args=(cap, preprocess_only))
        queue_thread.start()

        if preprocess_only:
            return factual_rate

        st = time.time()
        frame_id = 0

        if platform.system() != 'Darwin':
            cv2.namedWindow(win_name, cv2.WND_PROP_FULLSCREEN)
            cv2.setWindowProperty(win_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

        while True:
            if self.__halt_recording():
                break
            frame = self.__get_frame_buffer_front()
            if frame is None:
                break
            cv2.imshow(win_name, frame)
            # self.video_frames[frame_id].update()
            key = cv2.waitKey(delay)
            # signal stop if user press Q, or q
            if key == ord('Q') or key == ord('q'):
                break
            frame_id += 1
        # calculate the factual fps
        time_diff = time.time() - st
        if time_diff:
            factual_rate = (frame_id + 1) / time_diff

        queue_thread.join()

        return self.__video_show_end(win_name, factual_rate)

    @staticmethod
    def __init_video_capture(video_path, video_fps):
        cap = cv2.VideoCapture(video_path)

        if not cap.isOpened():
            print("[ERROR] reading video {}    ".format(time.strftime("%H:%M:%S")))

        if video_fps == 0:
            # determine from video
            video_fps = max(cap.get(cv2.CAP_PROP_FPS), 1)

        return cap, video_fps

    def play_video(self, video_path, video_fps=0):
        cap, video_fps = self.__init_video_capture(video_path, video_fps)
        win_name = video_path.split(os.sep)[-1]

        self.__inline_video(cap, win_name, video_fps, save_frame=False)

    def __inline_video(self, cap, win_name, fps, save_frame=True):
        frame_id = 0
        factual_rate = fps
        delay = int(1000.0 / fps)

        bg_frame = np.zeros(shape=(self.SCREEN_SIZE[1], self.SCREEN_SIZE[0], 3), dtype=np.uint8)
        bg_frame[:, :, :] = 255

        print("[INFO] showing video frames from file, going fullscreen... {}    "
              .format(time.strftime("%H:%M:%S")))
        sys.stdout.flush()

        font = cv2.FONT_HERSHEY_PLAIN
        color = (20, 20, 120)
        font_size = 1.1

        if platform.system() != 'Darwin':
            cv2.namedWindow(win_name, cv2.WND_PROP_FULLSCREEN)
            cv2.setWindowProperty(win_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

        st = time.time()
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            bg_frame[:frame.shape[0], :frame.shape[1], :] = frame
            cv2.putText(bg_frame, get_local_str_util("_press_q_to_quit"), (50, 80), font, font_size, color, 1, cv2.LINE_AA)
            # show frame
            cv2.imshow(win_name, bg_frame)
            # save frame record - image data for memory efficiency
            if save_frame:
                self.video_frames.append(Frame(frame_id, None))

            key = cv2.waitKey(delay)
            # signal stop if user press Q, or q
            if key == ord('Q') or key == ord('q'):
                break
            frame_id += 1

        time_diff = time.time() - st
        if time_diff:
            factual_rate = (frame_id + 1) / time_diff
        cap.release()
        return self.__video_show_end(win_name, factual_rate)

    @staticmethod
    def __video_show_end(win_name, factual_rate):
        print("[INFO] finished playing video. Factual Frame rate used: {:.4} {}    "
              .format(factual_rate, time.strftime("%H:%M:%S")))
        sys.stdout.flush()

        key = cv2.waitKey(0)
        if key == ord('Q') or key == ord('q'):
            cv2.destroyWindow(win_name)

        cv2.destroyAllWindows()

        return factual_rate

    def __video_thread(self, video_path, output_path='./', video_fps=0, camera_fps=0,
                       camera_index=0, preprocess=True, save_images=False):
        """

        :param video_path:
        :param output_path:
        :param video_fps:
        :param camera_fps:
        :param camera_index:
        :param preprocess:
        :param save_images:
        :return:
        """
        cap, video_fps = self.__init_video_capture(video_path, video_fps)
        # start camera thread
        cam_th = Thread(target=self.__camera_thread, args=(output_path, camera_index, camera_fps, save_images))
        self.video_meta["requested_fps"] = video_fps
        factual_rate = video_fps
        win_name = video_path.split(os.sep)[-1]
        try:
            cam_th.start()
            # wait till camera is up
            polling_camera_times = 0
            while not self.__get_camera_is_up():
                print("[INFO] waiting for camera {}     ".format(time.strftime("%H:%M:%S")))
                time.sleep(1)
                polling_camera_times += 1
                if polling_camera_times > 5:
                    print("[INFO] got tired of waiting for camera {}    ".format(time.strftime("%H:%M:%S")))
                    return -1.0

            # preprocess video for higher fps
            if preprocess:
                print("[INFO] preprocessing video {}    ".format(time.strftime("%H:%M:%S")))
                # failing _preprocessing method. TODO better optimisation
                # factual_rate = self.__preprocessed_video(cap, win_name, video_fps)
                factual_rate = self.__inline_video(cap, win_name, video_fps)
            else:
                print("[INFO] processing video and showing inline {}    ".format(time.strftime("%H:%M:%S")))
                # user want to minimise memory log, slower fps due to read video, process and show
                factual_rate = self.__inline_video(cap, win_name, video_fps)
            # signal stop session
            self.stop_session = True
            cam_th.join()

        except KeyboardInterrupt:
            self.stop()
        except Exception as e:
            print("{} {}    ".format(e, time.strftime("%H:%M:%S")))
            self.stop()
        return factual_rate

    def save_images(self, path):
        """

        :param path:
        :return:
        """
        for (i, frame) in enumerate(self.camera_frames):
            frame.save_to_file(path)

    def save_json(self, path=b"./results.json"):
        with open(path, "w") as f:
            f.write(json.dumps(self.get_json()))
            f.close()

    def get_json(self):
        obj = {
                "camera": [i.to_dict() for i in self.camera_frames],
                "video": [i.to_dict() for i in self.video_frames]
        }
        return obj


if __name__ == "__main__":
    video_feed_ctrl = VideoFeedCtrl()

    # video_path, \
    # output_path='./', \
    # video_fps=0, \
    # camera_fps=0,
    # camera_index=0, \
    # preprocess=True, \
    # save_images=False

    video_feed_ctrl.start(video_path="./data/stimulus_sample.mp4",
                          output_path="./data", preprocess=True)
    video_feed_ctrl.stop()
    # print(video_feed_ctrl.get_json())
