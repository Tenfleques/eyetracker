from talon import app

from talon import ctrl, tap, ui
from talon_plugins.eye_mouse import tracker
from talon.track.geom import Point2d, Point3d, EyeFrame

import time
import json

import logging
import logging.handlers

main = ui.main_screen()


def props(cls, is_dict=True):
    if is_dict:
        return [i for i in cls.keys() if i[:1] != '_']
    return [i for i in cls.__dict__.keys() if i[:1] != '_']


def is_on_main(p):
    return (main.x <= p.x < main.x + main.width and
            main.y <= p.y < main.y + main.height)


class EyeRecord(EyeFrame):
    timestamp_sys = time.time()

    def set_time(self):
        self.timestamp_sys = time.time()

    def get_pos(self):
        return {
            "x": self.rel.x,
            "y": self.rel.y,
            "z": self.rel.z,
            "validity": self.validity,
            "timestamp": self.timestamp_sys
        }

    def get_timestamp(self):
        return self.timestamp_sys

    def get_origin(self):
        return {
            "x": self.gaze3d.x,
            "y": self.gaze3d.y,
            "z": self.gaze3d.z,
            "validity": self.validity,
            "timestamp": self.timestamp_sys
        }

    def get_gaze_raw(self):
        return self.gaze

    def get_gaze(self):
        return {
            "x": self.gaze.x,
            "y": self.gaze.y,
            "validity": self.validity,
            "timestamp": self.timestamp_sys
        }


def get_gaze_center(left, right):
    p = (left.get_gaze_raw() + right.get_gaze_raw()) / 2
    main_gaze = -0.02 < p.x < 1.02 and -0.02 < p.y < 1.02 and bool(left or right)
    return {
        "x": p.x,
        "y": p.y,
        "validity": main_gaze,
        "timestamp": left.get_timestamp()
    }


def get_gaze_record(left, right):
    left.set_time()
    right.set_time()

    return {
        "pos": {
            "left": left.get_pos(),
            "right": right.get_pos()
        },
        "origin": {
            "left": left.get_pos(),
            "right": right.get_pos()
        },
        "gaze": get_gaze_center(left, right)
    }


class MonEyes:
    def __init__(self):
        self.gaze_logger = logging.getLogger('gaze_logger')
        self.gaze_logger.setLevel(logging.INFO)

        socketHandler = logging.handlers.SocketHandler('localhost',
                                                       logging.handlers.DEFAULT_TCP_LOGGING_PORT)

        self.gaze_logger.addHandler(socketHandler)
        self.saved_mouse = None
        self.main_mouse = False
        self.main_gaze = False
        self.restore_counter = 0

    def start(self):
        if not tracker:
            return False

        tracker.register('gaze', self.on_gaze)

        self.saved_mouse = None
        self.restore_counter = 0
        return True

    def stop(self):
        if tracker:
            tracker.unregister('gaze', self.on_gaze)
        return

    def on_gaze(self, b):
        l, r = EyeRecord(b, 'Left'), EyeRecord(b, 'Right')

        record = get_gaze_record(l, r)

        # b = Timestamp,
        # Left Eye 3D Position,
        # Left Eye 3D Relative Position,
        # Left Eye 3D Gaze Point,
        # Left Eye 2D Gaze Point,
        # Left Eye Pupil Diameter,
        # Left Eye Validity,
        # Right Eye 3D Position,
        # Right Eye 3D Relative Position,
        # Right Eye 3D Gaze Point,
        # Right Eye 2D Gaze Point,
        # Right Eye Pupil Diameter,
        # Right Eye Validity,
        # Right Eye Detected,
        # Left Eye Detected,
        # Left EyeBall Center position,
        # Right EyeBall Center Position,
        # Relative Combined Gaze Validity,
        # Relative Combined Gaze Point,
        # extra,type,cmd,eye

        # l = name,
        # validity,
        # detected,
        # pupil,
        # gaze,
        # gaze3d,
        # rel,pos

        message = json.dumps(record)

        self.gaze_logger.info(message)


class EyeTracker:
    def __init__(self):
        self.active = False

        self.menu = app.menu.item('Ай Трекер', weight=3000, checked=self.active, cb=self.toggle_tracker)

        # self.gaze_logger.addHandler(socketHandler)

        self.track_monitor = MonEyes()

    def toggle_tracker(self, inf):
        self.active = not self.active
        self.menu.checked = self.active
        if self.active:
            if self.track_monitor.start():
                app.notify('Ай Трекер',
                           'Ай Трекер активный', sound=False)
            else:
                self.active = False
                self.menu.checked = False
        else:
            self.track_monitor.stop()


menu = EyeTracker()
