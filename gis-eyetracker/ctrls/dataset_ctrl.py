import os 
import json 

class DatasetCtrl:
    data_dir = None
    def __init__(self, data_dir):
        self.data_dir = data_dir
        print(data_dir)
    
    def split_video_camera(self):
        video_camera_json = os.path.join(self.data_dir, "video_camera.json")
        video_camera_data = {"camera" : [], "video": []}

        if os.path.isfile(video_camera_json):
            with open(video_camera_json, "r") as fp:
                video_camera_data = json.load(fp)
                fp.close()
        
        video_json_file = os.path.join(self.data_dir, "video.json")
        # write the split file 
        with open(video_json_file, "w") as fp:
            json.dump(video_camera_data.get("video", {}), fp)
            fp.close()

        camera_json_file = os.path.join(self.data_dir, "camera.json")
        # write the split file 
        with open(camera_json_file, "w") as fp:
            json.dump(video_camera_data.get("camera", {}), fp)
            fp.close()

    def process_directory(self):
        pass


if __name__ == "__main__":
    dataset_ctrl = DatasetCtrl("/Volumes/GoogleDrive/My Drive/data/eyetracker-recordings/exp-2020-06-10_11-54-14")
    dataset_ctrl.split_video_camera()