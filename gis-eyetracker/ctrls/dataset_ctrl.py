import os 
import json 

from helpers import file_log

class DatasetCtrl:
    data_dir = None
    def __init__(self, data_dir):
        self.data_dir = data_dir
        print(data_dir)

    def read_json_data(self, filename):
        json_data_file = os.path.join(self.data_dir, filename)
        json_data = {}

        if os.path.isfile(json_data_file):
            with open(json_data_file, "r") as fp:
                json_data = json.load(fp)
                fp.close()

        return json_data

    def save_data_file(self, data, filename):
        with open(filename, "w") as fp:
            json.dump(data, fp)
            fp.close()

    def split_video_camera(self):
        video_camera_data = self.read_json_data("video_camera.json")

        video_json_file = os.path.join(self.data_dir, "video.json")
        self.save_data_file(video_camera_data.get("video", []), video_json_file)

        camera_json_file = os.path.join(self.data_dir, "camera.json")
        self.save_data_file(video_camera_data.get("camera", []), camera_json_file)

    def create_stimuli_timeline(self):
        timeline_data = list(self.read_json_data("tracker-timeline.json").values())
        
        stimuli_timeline = {}
        if not len(timeline_data):
            return stimuli_timeline

        for timeline_instance in timeline_data:
            video_frame = timeline_instance.get("video", None)
            if video_frame is None:
                continue

            instance_key = video_frame.get("src", None)
            if instance_key is None:
                continue 
            
            if stimuli_timeline.get(instance_key, None) is None:
                stimuli_timeline[instance_key] = []
            
            video_obj = timeline_instance.get("video")

            stimuli_timeline[instance_key].append(timeline_instance)
        
        os.makedirs(os.path.join(self.data_dir, "dataset"), exist_ok=True)

        for key in stimuli_timeline:
            stimuli_timeline_json_file = os.path.join(self.data_dir, "dataset", "{}-stimuli_timeline.json".format(key))
            self.save_data_file(stimuli_timeline[key], stimuli_timeline_json_file )

        return stimuli_timeline

def updates_cb(**kwargs):
    for i in kwargs:
        print(kwargs[i])

def make_datasets_from_data_dir(directory, updates_cb=updates_cb):
    d_sources = [os.path.join(directory, i) for i in os.listdir(directory) if os.path.isdir(os.path.join(directory, i))]
    k = 1
    total = len(d_sources) * 2
    for i in d_sources:
        if os.path.isdir(i):
            try:

                name = i.split(os.sep)[-1]
                dataset_ctrl = DatasetCtrl(i)
                
                dataset_ctrl.split_video_camera()
                updates_cb(name=name, current=k, total=total)
                k += 1
                dataset_ctrl.create_stimuli_timeline()
                updates_cb(name=name, current=k, total=total)
                k += 1
            except Exception as err:
                print(err)
                file_log(err)

if __name__ == "__main__":
    dataset_ctrl = DatasetCtrl("/Volumes/GoogleDrive/My Drive/data/eyetracker-recordings/exp-2020-06-10_11-54-14")
    dataset_ctrl.split_video_camera()
    dataset_ctrl.create_stimuli_timeline()