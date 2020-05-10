from ctypes import cdll, c_int, POINTER, c_char_p, c_char, create_string_buffer, c_size_t
import time

CString = POINTER(c_char)


class TrackerCtrl:
    def __init__(self, dll_path="./TobiiEyeLib.dll"):
        self.tracker_lib = cdll.LoadLibrary(dll_path)
        self.tracker_lib.start.restype = c_int

        self.tracker_lib.save_json.restype = c_size_t
        self.tracker_lib.save_json.argtypes =[CString]

    def start(self):
        started = self.tracker_lib.start()
        if started == 0:
            print("[INFO] started the tracker device {}    ".format(time.strftime("%H:%M:%S")))
        else:
            print("[ERROR] failed to start the tracker device {}    ".format(time.strftime("%H:%M:%S")))

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

    def save_json(self, path="./data/results.json"):
        path = path.encode()
        return self.tracker_lib.save_json(path)

    def get_json(self):
        required_size = self.tracker_lib.get_json(c_char_p(None), -1)
        print(required_size)
        buf = create_string_buffer(required_size)
        self.tracker_lib.get_json(buf, required_size)
        return buf


if __name__ == "__main__":
    a_tracker = TrackerCtrl()
    a_tracker.start()

    i = 0
    while i < 2:
        time.sleep(1)
        i += 1
    a_tracker.stop()
    print("[INFO] saved {} bytes".format(a_tracker.save_json()))

    a_tracker.kill()



