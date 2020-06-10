import numpy as np
import cv2 as cv
import copy
import math

def plot(img):
    fig, ax = plt.subplots(figsize = (10,10))
    ax.imshow(img)
    
def get_speed(size, delta, framerate):
    speed = size*delta/framerate
    return speed
   
def GenerateVideoText(name, duration, width, height, fps, image_array):
    print("Text generation start")
    
    background = np.full((height,width,3),255).astype(dtype = 'uint8')
    print(background.shape)
    image = image_array
    print(image.shape)
    #print(image)
    im_height,im_width,_ = image.shape
    scale = height/im_height
    image = cv.resize(image, None, fx = scale, fy = scale)
    im_height,im_width,_ = image.shape
    
    offset_x = int((width-im_width)/2)
    
    x1 = offset_x
    x2 = offset_x+im_width
    
    background[:,x1:x2,:] = image
    
    fourcc = cv.VideoWriter_fourcc('m', 'p', '4', 'v')
    out = cv.VideoWriter()
    success = out.open(name +'.mp4',fourcc,fps,(width, height),True) 
    
    cv.imwrite(name+'.png', background)
    
    framecounts = int(duration*fps)
    for i in range(framecounts):
         out.write(background)
    out.release()
    
    
    
    fout = open(name+'.meta','w')
    
    
    fout.write('type = text\n')
    fout.write('duration = '+str(duration)+'\n')
    
    fout.close()
    return 0;
    
    
    print("Text generation end")



