from kivy.app import App
from kivy.lang import Builder
from  kivy.uix.boxlayout import BoxLayout
from  kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.button import Button
from kivy.clock import Clock, mainthread
from kivy.uix.image import Image
from kivy.uix.label import Label
import cv2
import json
from  kivy.graphics.texture import Texture
import threading
from  kivy.uix.slider import Slider

from kivy.config import Config
Config.set('graphics', 'width', '800')
Config.set('graphics', 'height', '600')


class MyPlayerWidget(BoxLayout):
    def __init__(self, pp, **kwargs):
        super(MyPlayerWidget, self).__init__(**kwargs)
        self.pp = pp
        self.orientation = 'vertical'
        self.vidlay = AnchorLayout()
        self.im = Image()
        self.vidlay.add_widget(self.im)
        self.add_widget(self.vidlay)
        
        self.slider = Slider(size_hint = [1.0, 0.05], on_touch_up = self.on_slider)
        
        self.button = Button(size_hint = [1.0, 0.05], text = "Закрыть", on_press = self.close)
        
        self.add_widget(self.slider)
        self.add_widget(self.button)
        
        
        
            
        self.curr_frame = 0
        self.max_framecnt = 0
        self.event  = None
        self.play = False
        self.data = []
        
    def close(self, instance):
        print('close')
        if self.play:
            self.play = False
            
        self.event.cancel()
        self.pp.dismiss()
        
    def on_slider(self, instance, touch):  
        print(instance.value)  
        self.curr_frame = int(instance.value)
        if not self.play:
            self.play = True
            self.event = Clock.schedule_interval(self.update, 1.0/self.fps)
            
    def extract_frames(self, input_file):
        
        cap = cv2.VideoCapture(input_file) 
        self.fps = cap.get(cv2.CAP_PROP_FPS)
        print(self.fps)
        if (cap.isOpened()== False):  
          print("Error opening video  file") 
        
        cnt = 0
        while(cap.isOpened()): 
          # Capture frame-by-frame 
          ret, frame = cap.read() 
          if ret == True:
              self.data.append(frame)
              cnt = cnt+1
          else:  
            break
        
        self.max_framecnt = cnt
        self.slider.min = 0
        self.slider.max = cnt
        cap.release() 
        
    def start_play(self, input_file):
        if self.event!= None:
            self.event.cancel()
        self.extract_frames(input_file)
        self.start_point = 0
        self.frame_offset = 0
        self.play = True
        self.event = Clock.schedule_interval(self.update, 1.0/self.fps)
        
    def update(self, dt):
        #self.im = Image()
        
        curr_frame = self.curr_frame
        
        #print('frame:',curr_frame)
        if curr_frame<self.max_framecnt:
            
            frame = self.data[curr_frame]
            frame = cv2.flip(frame, 0)
            buf = frame.tostring()
            texture = Texture.create(size=(frame.shape[1], frame.shape[0]), colorfmt='bgr')
            texture.blit_buffer(buf, colorfmt='bgr', bufferfmt='ubyte')
            self.im.texture = texture
            self.slider.value = curr_frame
        else:
            self.play = False
            self.event.cancel()
            self.im.text = 'Предобработка видео'
        
        self.curr_frame = self.curr_frame+1
            
            

class ConfigApp(App):

    def build(self):
        return MyPlayerWidget()

if __name__ == '__main__':
    ConfigApp().run()
