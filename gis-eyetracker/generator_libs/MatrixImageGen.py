import cv2
import numpy as np
import matplotlib.pyplot as plt
from PIL import ImageFont, ImageDraw, Image
def get_Matrix_image(M, size, space, width, heigh, font_file):
    background = np.full((heigh,width,3),255).astype(dtype = 'uint8')
    dt = size+space
    #fontpath = font_file 
    print(font_file)
    font = ImageFont.truetype(font_file, size)
    
    img_pil = Image.fromarray(background)
    draw = ImageDraw.Draw(img_pil)
    
    size_Y = size*len(M)+space*(len(M)-1)
    size_X = size*len(M[0])+space*(len(M[0])-1)
    
    start_Y = int(heigh/2-size_Y/2)
    start_X = int(width/2-size_X/2)
    
    print(size_X,size_Y)
    print(start_X,start_Y)
    
    for i,lmas in enumerate(M):
        for j, let in enumerate(lmas):
            draw.text((start_X+j*dt,start_Y+i*dt),  let, font = font, fill = (0,0,0))
            
    img = np.array(img_pil)
    return img