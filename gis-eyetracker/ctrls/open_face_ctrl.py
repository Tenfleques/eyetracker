# -*- coding: utf-8 -*-
import time
import subprocess
import json
import pandas as pd
import os
from PIL import ImageGrab
from helpers import file_log
import platform
import sys
from io import StringIO

def get_xy(p0, pv):
    #print(pv[2])
    if pv[2]!=0:
        k = (0-p0[2])/pv[2]
        x = k*pv[0]+p0[0]
        y = k*pv[1]+p0[1]
        return [x,y]
    else:
        return p0[:2]

def get_point(frame,i, wnorm, hnorm):
    eye00 = (frame['eye_lmk_X_27'][i],frame['eye_lmk_Y_27'][i], frame['eye_lmk_Z_27'][i])
    eye01 = (frame['eye_lmk_X_23'][i],frame['eye_lmk_X_23'][i], frame['eye_lmk_X_23'][i])
    eye0 = [(eye00[a]+eye01[a])*0.5 for a in range(3)]
    
    pv0 = (frame['gaze_0_x'][i], frame['gaze_0_y'][i], frame['gaze_0_z'][i])
    
    eye10 = (frame['eye_lmk_X_55'][i],frame['eye_lmk_X_55'][i], frame['eye_lmk_X_55'][i])
    eye11 = (frame['eye_lmk_X_51'][i],frame['eye_lmk_Y_51'][i], frame['eye_lmk_Y_51'][i])
    eye1 = [(eye10[a]+eye11[a])*0.5 for a in range(3)]

    pv1 = (frame['gaze_1_x'][i], frame['gaze_1_y'][i], frame['gaze_1_z'][i])
    
    gaze_point0 = get_xy(eye0, pv0)
    gaze_point1 = get_xy(eye1, pv1)

    gaze_point0_norm = (gaze_point0[0]*1.0/wnorm, gaze_point0[1]*1.0/wnorm)
    gaze_point1_norm = (gaze_point1[0]*1.0/wnorm, gaze_point1[1]*1.0/wnorm)
    
    return[gaze_point0, gaze_point1, gaze_point0_norm, gaze_point1_norm]


class OpenFaceController:
    def __init__(self, PATH2APP, width, heigh):
        self.PATH = PATH2APP
        self.w = width*1.0/2
        self.h = heigh
    
    def proceed(self, file_in):

        exe_file = ""
        if platform.system() == 'Windows':
            exe_file = os.path.join(self.PATH, "OpenFace_2.2.0_win_x64", "FeatureExtraction.exe")
        
        if platform.system() == 'Darwin':
            exe_file = os.path.join(self.PATH, "OpenFace_2.2.0", "FeatureExtraction")

        if not os.path.isfile(exe_file):
            file_log("[ERROR] Openface FeatureExtraction executable not found")
            return -1

        out_dir = os.sep.join(file_in.split(os.sep)[:-1])
        out_dir = os.path.join(out_dir, "openface")
        os.makedirs(out_dir, exist_ok=True)

        args = [exe_file, '-f', file_in, '-out_dir', out_dir]
        old_stdout = sys.stdout
        sys.stdout = str_stdout = StringIO()

        file_tmp = os.path.join(out_dir, "proc.log")
        with open(file_tmp, 'w') as fp:
            fp.write("[INFO] started processing {} {}".format(time.strftime("%H:%M:%S"), os.linesep))
            fp.close()
    
        status_output_full = subprocess.run(args,stdout=True, stderr=True)
        status_output = status_output_full.returncode

        file_log(str_stdout.getvalue())
        sys.stdout = old_stdout

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

        tracks = []
        for i in range(len(df2)):
            tracks.append(get_point(df,i, self.w, self.h))


        output_data = []
        for i, k in enumerate(tracks):
            tmp = {'eye_0_x': tracks[i][0][0],
                   'eye_0_y': tracks[i][0][1],
                   'eye_0_xn': tracks[i][2][0],
                   'eye_0_yn': tracks[i][2][1],
                   'eye_1_x': tracks[i][1][0],
                   'eye_1_y': tracks[i][1][1],
                   'eye_1_xn': tracks[i][3][0],
                   'eye_1_yn': tracks[i][3][1]}
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
