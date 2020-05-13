import json
import cv2
import time
import os
from collections import deque
import numpy as np
from PIL import ImageGrab
import copy
from threading import Thread
from multiprocessing import Process
import sys


def create_timeline(tracker_data, video_data):
    gaze_frames = tracker_data["gaze"]
    camera_frames = video_data["camera"]
    video_frames = video_data["video"]

    timeline_keys = deque()

    g_fs = {}
    c_fs = {}
    v_fs = {}

    for frame in gaze_frames:
        timeline_keys.append(frame["timestamp"])
        g_fs[frame["timestamp"]] = frame

    for frame in camera_frames:
        timeline_keys.append(frame["timestamp"])
        c_fs[frame["timestamp"]] = frame

    for frame in video_frames:
        timeline_keys.append(frame["timestamp"])
        v_fs[frame["timestamp"]] = frame

    last_gaze_frame = None
    last_camera_frame = None
    last_video_frame = None
    sess_timeline = {}

    unique_sorted_timeline_keys = np.unique(timeline_keys)

    for key in unique_sorted_timeline_keys:
        last_gaze_frame = copy.copy(g_fs.get(key, last_gaze_frame))
        last_camera_frame = copy.copy(c_fs.get(key, last_camera_frame))
        last_video_frame = copy.copy(v_fs.get(key, last_video_frame))

        if last_gaze_frame is not None:
            if (last_camera_frame is not None) or (last_video_frame is not None):
                sess_timeline[key] = {
                    "gaze": last_gaze_frame,
                    "camera": last_camera_frame,
                    "video": last_video_frame
                }

    return sess_timeline


def process_demo_video(video_path, session_timeline, cam_video_path="", cb=lambda: print("[INFO] finished processing "
                                                                                         "video")):
    timestamp_keys = session_timeline.keys()
    len_keys = len(timestamp_keys)
    if len_keys == 0:
        return

    cap_video = cv2.VideoCapture(video_path)
    cap_camera = None

    if os.path.isfile(cam_video_path):
        cap_camera = cv2.VideoCapture(cam_video_path)

    if not cap_video.isOpened():
        print("[INFO] error opening stimuli video {}    ".format(time.strftime("%H:%M:%S")))
        return

    fourcc = cv2.VideoWriter_fourcc('M', 'J', 'P', 'G')
    out = cv2.VideoWriter()

    diff = max(timestamp_keys) - min(timestamp_keys)

    video_fps = max(len_keys / diff, 30)
    print(video_fps)

    demo_video_path = cam_video_path.replace(".avi", "-demonstration.avi")
    SCREEN_SIZE = ImageGrab.grab().size
    bg_frame = np.zeros((SCREEN_SIZE[1], SCREEN_SIZE[0], 3), dtype=np.uint8)

    success = out.open(demo_video_path, fourcc, video_fps,
                       (bg_frame.shape[1], bg_frame.shape[0]), True)

    radius = 10
    color = (0, 255, 0)
    thickness = 2

    sh = (int(cap_video.get(cv2.CAP_PROP_FRAME_WIDTH)),
          int(cap_video.get(cv2.CAP_PROP_FRAME_HEIGHT)))

    c_start_x = sh[0] + 40

    if cap_camera is not None:
        w, h = (cap_camera.get(cv2.CAP_PROP_FRAME_WIDTH),
                cap_camera.get(cv2.CAP_PROP_FRAME_HEIGHT))

        c_width = SCREEN_SIZE[0] - c_start_x
        c_height = int(h * c_width / w)

    st = time.time()

    cam_frame_id = 0
    vid_frame_id = 0
    v_frame = None
    c_frame = None
    xo = None
    yo = None

    for key, record in session_timeline.items():
        bg_frame[:, :, :] = 255
        if not cap_video.isOpened():
            break

        if record["video"] is not None:
            if not record["video"]["frame_id"] == vid_frame_id:
                ret, v_frame = cap_video.read()
                vid_frame_id = record["video"]["frame_id"]
                if not ret:
                    break

        if v_frame is not None:
            bg_frame[:sh[1], :sh[0], :] = v_frame

        # add gaze feed data
        if record["gaze"] is not None:
            xr = record["gaze"]['x']
            yr = record["gaze"]['y']

            xo = int(bg_frame.shape[1] * xr)
            yo = int(bg_frame.shape[0] * yr)

        if xo is not None and yo is not None:
            bg_frame = cv2.circle(bg_frame, (xo, yo), radius, color, thickness)

        # add camera feed data
        if cap_camera is not None:
            if cap_camera.isOpened():
                if record["camera"] is not None:
                    if not record["camera"]["frame_id"] == cam_frame_id:
                        ret, c_frame = cap_camera.read()
                        cam_frame_id = record["camera"]["frame_id"]
                        if ret:
                            c_frame = cv2.resize(c_frame, (c_width, c_height))

        if c_frame is not None:
            bg_frame[:c_height, c_start_x:c_start_x + c_width, :] = c_frame
        out.write(bg_frame)

    total_time = time.time() - st

    cap_video.release()
    if cap_camera is not None:
        cap_camera.release()
    out.release()
    if success:
        print("[INFO] written demonstration video {} {}    ".format(demo_video_path.replace("\\", "/"),
                                                                    time.strftime("%H:%M:%S")))
    cb()
    return total_time


def gaze_stimuli(tracker_json_path, video_json_path, video_path, selfie_video_path=None,
                 timeline_exist=False, process_video=True,
                 session_timeline_cb=lambda x: print("[INFO] finished creating session timeline"),
                 video_cb=lambda: print("[INFO] finished demonstration video ")):
    with open(tracker_json_path, "r") as read_file:
        tracker_data = json.load(read_file)
        read_file.close()

    with open(video_json_path, "r") as v_read_file:
        video_data = json.load(v_read_file)
        v_read_file.close()

    sess_timeline_file = tracker_json_path.replace(".json", "-timeline.json")

    if timeline_exist and os.path.isfile(sess_timeline_file):
        with open(sess_timeline_file, "r") as read_sess:
            sess_timeline = json.load(read_sess)
            read_sess.close()
    else:
        sess_timeline = create_timeline(tracker_data, video_data)
        with open(sess_timeline_file, "w") as write_sess:
            json.dump(sess_timeline, write_sess)
            write_sess.close()

    session_timeline_cb(sess_timeline)

    if process_video:
        p = Thread(target=process_demo_video, args=(video_path, sess_timeline, selfie_video_path, ))
        p.start()
        p.join()
        video_cb()

    return sess_timeline


def info(title):
    print(title)
    print('module name:', __name__)
    print('parent process:', os.getppid())
    print('process id:', os.getpid())


if __name__ == '__main__':
    info('main line')
    # p = Process(target=f, args=('bob',))
    timeline = gaze_stimuli("./data/tracker.json",
                            "./data/video_camera.json",
                            "./data/stimulus_sample.mp4",
                            "./data/out-video.avi", False, True, )
