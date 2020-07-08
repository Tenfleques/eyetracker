import matplotlib.pyplot as plt
import math
import numpy as np
import cv2 as cv
import copy
import json

def calculateDistance(x1,y1,x2,y2):
    dist = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
    return dist

def GetCord(P1,P2,off):
    vx = P2[0]-P1[0]
    vy = P2[1]-P1[1]
    vx = vx*off
    vy = vy*off
    
    tx = P1[0]+vx
    ty = P1[1]+vy
    
    return(tx,ty)

class CurrPoint:
    def __init__(self):
        self.pos = 0
        self.off = 0.0
    
    def update(self, X,Y,L,v):
        if self.pos+1>len(L):
                return -1
            
            
        curroffs = (1-self.off)*L[self.pos]
        
        while (curroffs<v):
            self.pos = self.pos+1
            if self.pos+1>len(L):
                return -1
            curroffs = curroffs+L[self.pos]
        
        dist_left = curroffs-v
        self.off = 1-dist_left/L[self.pos]
        
        #self.off = v_left/L[self.pos]
        
        #print(X,Y,v,curroffs, self.off)
        
        #print(X,Y,v,curroffs,)
        #print((X[self.pos],Y[self.pos]))
        X,Y = GetCord((X[self.pos],Y[self.pos]),(X[self.pos+1],Y[self.pos+1]),self.off)
        #print(X,Y)
        return X,Y
    def dist(self, L):
        return sum(L[:self.pos])+L[self.pos]*self.off
        
    


#timestamp in format 'frame_float -> speed'
def rel2abs(tsteps, sumL, v0):
    res = []
    for k in tsteps:
        p1 = k[0]*sumL
        p2 = k[1]*v0
        res.append((p1,p2))
    return res


def update_v(offset, speed_list):
    res_v = speed_list[0][1]
    for d,v in speed_list:
        #print(v,d,offset)
        if d<offset:
            #print('v=',v)
            res_v = v
    return res_v

def GenerateVideoSVG(name, image, counturs, speed_list, width, height, fps):
    print("Video generation start")
    background = np.full((height,width,3),255).astype(dtype = 'uint8')
    fourcc = cv.VideoWriter_fourcc('m', 'p', '4', 'v')
    out = cv.VideoWriter()
    
    success = out.open(name +'.mp4',fourcc,fps,(width, height),True) 
    
    X = [a[0] for a in counturs]
    Y = [a[1] for a in counturs]
    L = [calculateDistance(X[i],Y[i],X[i+1],Y[i+1]) for i in range(len(X)-1)]
    
    
    im_height,im_width,_ = image.shape
    scale = min(height/im_height,width/im_width)
    offset_x = int((width-im_width*scale)/2)
    offset_y = int((height-im_height*scale)/2)
    
    
    plt.scatter(X,Y)
    sumL = sum(L)
    print('NAME=',name)
    print('start_speed:',speed_list[0][1])
    v_fps = speed_list[0][1]/fps
        
    ball = CurrPoint()
    
    radius = int((max(width,height)*0.005))
    color = (0, 0, 255)
    thickness = int((max(width,height)*0.005))
    
    cont = True
    c_pos = 0
    
    cnter_frames = 0
    dt = 1.0/fps
    
    print(v_fps, dt)
    framecount= 0;
    
    trajectory_points = []
    
    while True:
        
        passed_distance = ball.dist(L)
        passed_distance_perc = passed_distance/sumL
        v_new = update_v(passed_distance_perc, speed_list)
        v_new_fps = v_new/fps
        print(v_new_fps)
        #print(passed_distance, passed_distance_perc, v_new, v_new_fps)
        #print(ball.off)
        if (v_new_fps==0):
            print('ALERT')
            print(passed_distance, passed_distance_perc, v_new, v_new_fps,cnter_frames)
            break
        P = ball.update(X,Y,L,v_new_fps)
        if P==-1:
            break
        
        cnter_frames = cnter_frames+1
        X_o,Y_o = P
        center_coordinates = (int(offset_x+X_o*scale),int(offset_y+Y_o*scale))
        
        pnt = {'x':center_coordinates[0], 'y': center_coordinates[1]}
        trajectory_points.append(pnt)
        
        back = copy.deepcopy(background)
        frame = cv.circle(back, center_coordinates, radius, color, thickness)
        out.write(frame)
        framecount = framecount+1
        
    
    out.release()  
    
    
    with open(name+'.stimulus.json', 'w') as outfile:
        json.dump(trajectory_points, outfile)
    
    #duration = dt*cnter_frames
    #fout = open("data_tmp/"+name+'.meta','w')
    #fout.write('type = SVG\n')
    #fout.write('duration = '+str(duration)+'\n')
    #fout.close()
    
    print("Video generation finished")
    return framecount*1.0/fps;