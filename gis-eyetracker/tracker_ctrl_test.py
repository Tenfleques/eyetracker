from ctypes import cdll, c_int, POINTER, c_char_p, c_char, create_string_buffer, c_size_t
import time
import logging
logging.basicConfig(filename='~/logs/view_trackbox.log',level=logging.DEBUG)

CString = POINTER(c_char)


class TrackerCtrl:
    def __init__(self, dll_path="./TobiiEyeLib.dll"):
        self.tracker_lib = cdll.LoadLibrary(dll_path)
        # self.tracker_lib.save_json.restype = c_size_t
        # self.tracker_lib.save_json.argtypes =[c_char_p]

        self.tracker_lib.save_json.restype = c_size_t
        self.tracker_lib.save_json.argtypes =[CString]

    def start(self):
        self.tracker_lib.start()
        print("[INFO] started the tracker device {}    ".format(time.strftime("%H:%M:%S")))

    def stop(self):
        print("[INFO] stopping the tracker device {}    ".format(time.strftime("%H:%M:%S")))
        time.sleep(3)
        try:
            self.tracker_lib.stop()
        except Exception as e:
            print("[ERROR] an error occured while stopping the tracker session {}    ".format(e))

    def save_json(self, path="./results.json"):
        path = path.encode()
        return self.tracker_lib.save_json(path)

    def get_json(self):
        required_size = self.tracker_lib.get_json(c_char_p(None), -1)
        print(required_size)
        buf = create_string_buffer(required_size)
        self.tracker_lib.get_json(buf, required_size)
        return buf

import json
import numpy as np
if __name__ == "__main__":
    a_tracker = TrackerCtrl()
    a_tracker.start()
    time.sleep(10)
    a_tracker.stop()
    print("[INFO] saved {} bytes".format(a_tracker.save_json('test_results_10secs.json')))


    PATH2RESULT = "test_results_10secs.json"
    with open(PATH2RESULT, "r") as read_file:
        data = json.load(read_file)

    d = []
    for i in range(len(data['gaze'])-1):
        d.append(data['gaze'][i+1]['timestamp_us']-data['gaze'][i-1]['timestamp_us'])
    d = np.mean(d)
    q = data['gaze'][-1]['timestamp']-data['gaze'][0]['timestamp']
    print('Difference between first and last timestamps[secs]',q)
    input();
