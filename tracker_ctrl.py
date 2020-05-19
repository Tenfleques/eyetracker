from ctypes import cdll, c_int, POINTER, c_char_p, c_char, create_string_buffer, c_size_t, Structure, c_float
import time
import platform
from threading import Thread
from gaze_listener import LogRecordSocketReceiver

CString = POINTER(c_char)


class Point2D(Structure):
    _fields_ = [('x', c_float), ('y', c_float)]

    @classmethod
    def from_param(cls, self):
        if not isinstance(self, cls):
            raise TypeError
        return self


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
    def __init__(self, dll_path="./TobiiEyeLib.dll"):
        if platform.system() == 'Windows':
            self.tracker_lib = cdll.LoadLibrary(dll_path)
            self.tracker_lib.start.restype = c_int

            self.tracker_lib.save_json.restype = c_size_t
            self.tracker_lib.save_json.argtypes =[CString]

            self.tracker_lib.get_trackbox.restype = POINTER(TrackBox)

            self.save_json = self.__save_json_win
            self.get_json = self.__get_json_win

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
                print("[ERROR] an error connecting to the tracker log server occurred {}     ".format(ex))

            self.save_json = self.__save_json_mac
            self.get_json = self.__get_json_mac

    def get_track_box(self):
        if platform.system() == 'Windows':
            track_box = self.tracker_lib.get_trackbox()[0]
            return track_box

    def start(self):
        started = self.tracker_lib.start()
        if started == 0:
            print("[INFO] started the tracker device {}    ".format(time.strftime("%H:%M:%S")))
        else:
            print("[ERROR] failed to start the tracker device {}    ".format(time.strftime("%H:%M:%S")))
        return started

    def stop(self):
        print("[INFO] stopping the recording of tracker device data {}    ".format(time.strftime("%H:%M:%S")))
        try:
            self.tracker_lib.stop()
        except Exception as e:
            print("[ERROR] an error occurred while stopping the tracker session {}    ".format(e))

    def kill(self):
        print("[INFO] stopping the tracker device {}    ".format(time.strftime("%H:%M:%S")))
        try:
            self.tracker_lib.kill()
        except Exception as e:
            print("[ERROR] an error occurred while stopping the tracker device {}    ".format(e))

    def __save_json_win(self, path="./data/results.json"):
        path = path.encode()
        return self.tracker_lib.save_json(path)

    def __get_json_win(self):
        required_size = self.tracker_lib.get_json(c_char_p(None), -1)
        print(required_size)
        buf = create_string_buffer(required_size)
        self.tracker_lib.get_json(buf, required_size)
        return buf

    def __save_json_mac(self, path="./data/results.json"):
        self.tracker_lib.save_json(path)

    def __get_json_mac(self):
        return self.tracker_lib.get_json()


if __name__ == "__main__":
    a_tracker = TrackerCtrl()
    a_tracker.start()

    i = 0
    while i < 2:
        time.sleep(1)
        i += 1
    a_tracker.stop()
    print("[INFO] saved {} bytes".format(a_tracker.save_json()))

    print("[INFO] the track box", a_tracker.get_track_box())

    a_tracker.kill()



