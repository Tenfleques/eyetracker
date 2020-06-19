import subprocess
import json
import pandas as pd

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
        print(self.w, self.h)
        
    def proceed(self, file, file_out):
        args = [self.PATH+"FeatureExtraction.exe", '-f', file]
        #status_output = subprocess.call(args) 
        #print(status_output)

        fname = file.split('/')[-1].split('.')[0]

        
        CSV_IN = self.PATH+'processed/'+fname+'.csv'

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

        with open(file_out, 'w') as json_file:
            json.dump(output_data, json_file)



#APP = "G:/Main/WorkFolder/NeuroLab/OpenFace_2.2.0_win_x64/"
#FILE = "C:/Users/Sergey/Pictures/Camera Roll/WIN_20200618_13_11_52_Pro.mp4"
#openface = OpenFaceController(APP, 500, 400)
#openface.proceed(FILE, "test.json")
