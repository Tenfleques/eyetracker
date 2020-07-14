# -*- coding: utf-8 -*-
import time
import subprocess
import json
import pandas as pd
import os

from helpers import file_log, recurse_directory_files
import platform

if platform.system() == 'Linux':
    import pyscreenshot as ImageGrab
else:
    from PIL import ImageGrab

import sys
from io import StringIO

APP_DIR = os.path.dirname(__file__)
APP_DIR = os.path.dirname(APP_DIR)

def get_xy(p0, pv):
    #print(pv[2])
    if pv[2]!=0:
        k = (0-p0[2])/pv[2]
        x = k*pv[0]+p0[0]
        y = k*pv[1]+p0[1]
        return [x,y]
    else:
        return p0[:2]

def get_point(frame,i):
    eye00 = (frame['eye_lmk_X_27'][i],frame['eye_lmk_Y_27'][i], frame['eye_lmk_Z_27'][i])
    eye01 = (frame['eye_lmk_X_23'][i],frame['eye_lmk_Y_23'][i], frame['eye_lmk_Z_23'][i])
    eye0 = [(eye00[a]+eye01[a])*0.5 for a in range(3)]
    
    pv0 = (frame['gaze_0_x'][i], frame['gaze_0_y'][i], frame['gaze_0_z'][i])
    
    eye10 = (frame['eye_lmk_X_55'][i],frame['eye_lmk_Y_55'][i], frame['eye_lmk_Z_55'][i])
    eye11 = (frame['eye_lmk_X_51'][i],frame['eye_lmk_Y_51'][i], frame['eye_lmk_Z_51'][i])
    eye1 = [(eye10[a]+eye11[a])*0.5 for a in range(3)]

    pv1 = (frame['gaze_1_x'][i], frame['gaze_1_y'][i], frame['gaze_1_z'][i])
    
    #gaze_point0 = get_xy(eye00, pv0)
    #gaze_point1 = get_xy(eye10, pv1)
    
    gaze_point0 = get_xy(eye0, pv0)
    gaze_point1 = get_xy(eye1, pv1)
    
    return(gaze_point0, gaze_point1)

def subprocess_call(*args, **kwargs):
    #also works for Popen. It creates a new *hidden* window, so it will work in frozen apps (.exe).
    if platform.system() == 'Windows':
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags = subprocess.CREATE_NEW_CONSOLE | subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
        kwargs['startupinfo'] = startupinfo

    status_output_full = subprocess.call(*args, **kwargs)
    return status_output_full
    

class OpenFaceController:
    def __init__(self, PATH2APP, width, height):
        self.PATH = PATH2APP
        self.w = width
        self.h = height

        self.data = {}
        config_path = os.path.join(APP_DIR, "user", "configs", "camera", "cam_config.json")
        if os.path.isfile(config_path):
            with open(config_path) as json_file:
                self.data = json.load(json_file)
                json_file.close()
        else:
            file_log("[ERROR] camera configuration not found")
    
    def get_exe_file(self):
        exe_file = ""
        if os.path.isdir(self.PATH):
            all_files = recurse_directory_files(self.PATH, 0, 2)
            for f in all_files:
                if "FeatureExtraction" in f:
                    exe_file = f
                    break

        return exe_file

    def proceed(self, file_in):
        exe_file = self.get_exe_file()

        if not os.path.isfile(exe_file):
            file_log("[ERROR] Openface FeatureExtraction executable not found")
            return -1

        out_dir = os.sep.join(file_in.split(os.sep)[:-1])
        out_dir = os.path.join(out_dir, "openface")
        os.makedirs(out_dir, exist_ok=True)

        args = [exe_file, '-f', file_in, '-out_dir', out_dir]

        file_tmp = os.path.join(out_dir, "proc.log")
        with open(file_tmp, 'w') as fp:
            fp.write("[INFO] started processing {} {}".format(time.strftime("%H:%M:%S"), os.linesep))
            fp.close()

        status_output = -1

        try:
            status_output = subprocess_call(args, stdout=True, stderr=True)
        except Exception as err:
            file_log("[ERROR] {}".format(err))

        if status_output != 0:
            error = "[ERROR] failed to process with openface {} ".format(status_output)
            print(error)
            file_log(error)
            return status_output

        fname = file_in.split(os.sep)[-1].split('.')[0]
        CSV_IN = os.path.join(out_dir, fname+'.csv')


        df = pd.read_csv(CSV_IN)
        df.columns = [a[1:] for a in df.columns]
        df2 = df[['gaze_0_x', 'gaze_0_y', 'gaze_0_z',\
                  'gaze_1_x', 'gaze_1_y', 'gaze_1_z',\
                  'gaze_angle_x', 'gaze_angle_y', \
                  'eye_lmk_X_27', 'eye_lmk_Y_27', 'eye_lmk_Z_27', \
                  'eye_lmk_X_23', 'eye_lmk_Y_23', 'eye_lmk_Z_23', \
                  'eye_lmk_X_55', 'eye_lmk_Y_55', 'eye_lmk_Z_55', \
                  'eye_lmk_X_51', 'eye_lmk_Y_51', 'eye_lmk_Z_51']]

        tracks_tmp = []
        for i in range(len(df2)):
            tracks_tmp.append(get_point(df,i))
            # tracks_tmp.append(get_point(df,i, self.w, self.h))

        tracks = []
        for t in tracks_tmp:
            p0 = t[0]
            p1 = t[1]

            p0 = ((p0[0]+self.data['x_offset'])/self.data['width'], \
                  (p0[1]+self.data['y_offset'])/self.data['height'])
            p1 = ((p1[0]+self.data['x_offset'])/self.data['width'], \
                  (p1[1]+self.data['y_offset'])/self.data['height'])
    
            tracks.append((p0,p1)) 

        
        output_data = []
        for i, k in enumerate(tracks):
            tmp = {'eye_0_x': tracks[i][0][0],
                   'eye_0_y': tracks[i][0][1],
                   'eye_1_x': tracks[i][1][0],
                   'eye_1_y': tracks[i][1][1]}
            output_data.append(tmp)

        file_out = os.path.join(out_dir, "openface_out.json")

        with open(file_out, 'w') as json_file:
            json.dump(output_data, json_file)
            json_file.close()

        with open(file_tmp, 'a') as fp:
            fp.write("[INFO] finished processing {} {}".format(time.strftime("%H:%M:%S"), os.linesep))
            fp.close()

        return status_output


if __name__ == "__main__":
    PATH = os.path.dirname(os.path.abspath(__file__))
    PATH = os.path.dirname(PATH)
    PATH = os.path.dirname(PATH)
    APP = os.path.join(PATH, "gis-eyetracker", "bin", "OpenFace_2.2.0_win_x64")
    FILE = os.path.join(PATH, "data", "exp-2020-06-16_17-57-31", "out-video.avi")
    screen_grab = ImageGrab.grab()
    w, h = screen_grab.size
    openface = OpenFaceController(APP, w, h)
    openface.proceed(FILE)
