from ctrls.tracker_ctrl import TrackerCtrl
import time 
from helpers import file_log

a_tracker = TrackerCtrl()
a_tracker.start()

i = 0
while i < 2:
    time.sleep(1)
    i += 1
a_tracker.stop()
print("[INFO] saved {} bytes".format(a_tracker.save_json("user/test_tracker.json")))

print("[INFO] the json from get {}", a_tracker.get_json())

file_log("[INFO] the track box in json")
file_log(a_tracker.get_meta_json())

a_tracker.kill()