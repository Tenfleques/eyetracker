from kivy.app import App
from ctypes import cdll, c_int, POINTER, c_char_p, c_char, create_string_buffer, c_size_t, Structure, c_float
import time
import platform
from helpers import get_local_str_util, file_log
import os
from threading import Thread
from ctrls.gaze_listener import LogRecordSocketReceiver

CString = POINTER(c_char)


class Point2D(Structure):
    _fields_ = [('x', c_float), ('y', c_float)]

    @classmethod
    def from_param(cls, self):
        if not isinstance(self, cls):
            raise TypeError
        return self

    def to_dict(self):
        return {
            "x": self.x,
            "y": self.y
        }


class Point3D(Point2D):
    _fields_ = [('z', c_float)]

    def __init__(self):
        self.x = 0.0
        self.y = 0.0
        self.z = 0.0

    @classmethod
    def from_param(cls, self):
        if not isinstance(self, cls):
            raise TypeError
        return self

    def to_dict(self):
        return {
            "x" : self.x,
            "y" : self.y,
            "z" : self.z
        }


class TrackBox(Structure):
    _fields_ = [('back_bottom_right', Point3D), ('back_bottom_left', Point3D),
                ('back_top_right', Point3D), ('back_top_left', Point3D),
                ('front_bottom_right', Point3D), ('front_bottom_left', Point3D),
                ('front_top_right', Point3D), ('front_top_left', Point3D),
                ]

    @classmethod
    def from_param(cls, self):
        if not isinstance(self, cls):
            raise TypeError
        return self


class TrackerCtrl:
    is_up = False

    def __init__(self, dll_path="./TobiiEyeLib.dll"):
        if platform.system() == 'Windows':
            self.tracker_lib = cdll.LoadLibrary(dll_path)
            self.tracker_lib.start.restype = c_int

            self.tracker_lib.save_json.restype = c_size_t
            self.tracker_lib.save_json.argtypes = [CString]
            self.tracker_lib.get_json.argtypes = [CString, c_size_t]
            self.tracker_lib.get_meta_json.argtypes = [CString, c_size_t]

            self.save_json = self.__save_json_win
            self.get_json = self.__get_json_win
            self.get_meta_json = self.__get_meta_json_win

        if platform.system() == 'Darwin':
            self.tracker_lib = LogRecordSocketReceiver()
            self.socket_thread = Thread(target=self.tracker_lib.init,)
            try:
                # Start the thread
                self.socket_thread.start()
            # When ctrl+c is received
            except KeyboardInterrupt as e:
                # Set the alive attribute to false
                self.kill()
            except Exception as ex:
                self.kill()
                file_log("[ERROR] an error connecting to the tracker log server occurred {}".format(ex))

            self.save_json = self.__save_json_mac
            self.get_json = self.__get_json_mac
            self.get_meta_json = self.__get_meta_json_mac

    @staticmethod
    def __tracker_app_log(text, log_label='app_log'):
        # give feedback to the user of what is happening behind the scenes
        app = App.get_running_app()
        try:
            app.tracker_app_log(text, log_label)
        except Exception as er:
            print("[ERROR] {}".format(er))

    def start(self):
        started = self.tracker_lib.start()
        if started == 0:
            file_log("[INFO] started the tracker device")
            self.is_up = True
            self.__tracker_app_log(get_local_str_util("_connected_tracker"), "tracker_log")
        else:
            file_log("[ERROR] failed to start the tracker device")
            self.__tracker_app_log(get_local_str_util("_failed_to_connect_tracker"), "tracker_log")
        return started

    def get_is_up(self):
        return self.is_up

    def stop(self):
        file_log("[INFO] stopping the recording of tracker device data")
        try:
            self.is_up = False
            self.tracker_lib.stop()
            self.__tracker_app_log(get_local_str_util("_stopped_tracking"), "tracker_log")
        except Exception as e:
            file_log("[ERROR] an error occurred while stopping the tracker session {}    ".format(e))
            self.__tracker_app_log("{}: {}".format(get_local_str_util("_error_stopping_tracking"), e), "tracker_log")

    def kill(self):
        file_log("[INFO] stopping the tracker device")
        try:
            self.is_up = False
            self.tracker_lib.kill()
            self.__tracker_app_log(get_local_str_util("_disconnected_tracker"), "tracker_log")
        except Exception as e:
            file_log("[ERROR] an error occurred while stopping the tracker device {}    ".format(e))
            self.__tracker_app_log("{}: {}".format(get_local_str_util("_error_disconnecting_tracker"), e), "tracker_log")

    def __save_json_win(self, path="./data/results.json"):
        b_path = path.encode()
        try:
            saved = self.tracker_lib.save_json(b_path)
            session_name = path.split(os.sep)[-2]
            self.__tracker_app_log("{}: {}".format(get_local_str_util("_saved_tracker"), session_name), "tracker_log")
            return saved
        except Exception as err:
            file_log("[ERROR] exception while trying to save he tracker data", err)
            self.__tracker_app_log("{}: {}".format(get_local_str_util("_error_saving_tracker_session"), err), "tracker_log")

    def __get_json_win(self):
        required_size = self.tracker_lib.get_json(c_char_p(None), -1)
        buf = create_string_buffer(required_size)
        self.tracker_lib.get_json(buf, required_size)
        return buf.value

    def __get_meta_json_win(self):
        required_size = self.tracker_lib.get_meta_json(c_char_p(None), -1)
        buf = create_string_buffer(required_size)
        self.tracker_lib.get_meta_json(buf, required_size)
        return buf.value.decode("utf-8")

    @staticmethod
    def __get_meta_json_mac():
        return "{}"

    def __save_json_mac(self, path="./data/results.json"):
        self.tracker_lib.save_json(path)

    def __get_json_mac(self):
        return self.tracker_lib.get_json()



