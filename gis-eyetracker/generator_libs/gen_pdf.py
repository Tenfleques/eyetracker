from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.filechooser import FileChooserIconView
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.core.window import Window
from kivy.uix.button import Button

from kivy.uix.textinput import TextInput
from kivy.uix.label import Label

from kivy.config import Config
from kivy.uix.video import Video
from kivy.core.window import Window
import json

from generator_libs.VideoGenerator import *
from generator_libs.SettingBox import *

from pdf2image import convert_from_path, convert_from_bytes
import numpy as np
import cv2

#Window.fullscreen = False
Window.show_cursor = True
window_sizes=Window.size


Config.set('graphics', 'width', window_sizes[0])
Config.set('graphics', 'height', window_sizes[1])
Config.set('graphics', 'fullscreen', False)
Config.write()


GlobVideoSet = None
GlobVideoSetMenu = None


class gen_PDF(BoxLayout):
    
    DATA_LOADED = False 
    def __init__(self, work_folder, VideoSettings, VideoSetWidget, **kwargs):
        
        global GlobVideoSet 
        GlobVideoSet = VideoSettings
        global GlobVideoSetMenu 
        GlobVideoSetMenu = VideoSetWidget
        
        
        self.work_folder = work_folder
        
        super(gen_PDF, self).__init__(**kwargs)
        #left part
        blay1 = BoxLayout(orientation = 'vertical',size_hint = [0.3, 1.0])
        self.files = FileChooserIconView(filters = ['*.pdf'],\
                                         rootpath = self.work_folder+'input/', \
                                         multiselect = True,\
                                         on_selection = self.press_select)
        blay1.add_widget(self.files)
        blay1.add_widget(Button(on_press = self.press_select, text = 'Загрузить',\
                                size_hint = [1.0,0.1]))
        
        self.add_widget(blay1)
        #right part
        blay2 = BoxLayout(orientation = 'vertical')
        self.image_lay = AnchorLayout()
        blay3 = BoxLayout(size_hint = [1.0,0.1])
        
        blay4 = BoxLayout(orientation = 'vertical')
        #blay4.add_widget(Label(text = 'Длительность[секунды]:'))
        #self.dur_input = TextInput(text = '10', input_filter = 'float')
        #blay4.add_widget(self.dur_input)
        
        #blay3.add_widget(blay4)
        blay3.add_widget(Button(text = 'Настройки', on_press = self.press_settings))
        blay3.add_widget(Button(text = 'Генерация видео', on_press = self.press_generation))
        
        blay2.add_widget(self.image_lay)
        blay2.add_widget(blay3)
        self.add_widget(blay2)
    
    
    
    
    def press_select(self, instance):
        print('touch')
        if len(self.files.selection)==0:
            pp1 = Popup(title = 'Ошибка', size_hint = [0.3,0.3])
            bb1 = Button(text = 'Пожалуйста, выберите PDF', on_press = pp1.dismiss)
            pp1.add_widget(bb1)
            pp1.open()
            return
            
        print(self.files.selection[-1])
        file = self.files.selection[-1]
        images = convert_from_path(file)
        pix = np.array(images[0])
        im_out = self.work_folder+'tmp/'+file.split('\\')[-1]+'.png'
        cv2.imwrite(im_out, pix)
        self.image_lay.clear_widgets()
        self.image_lay.add_widget(Image(source = im_out))
        self.DATA_LOADED = True
        
    def press_settings(self, instance):
        GlobVideoSetMenu.open()
        
    def press_generation(self, instance):
        
        if not self.DATA_LOADED:
            pp1 = Popup(title = 'Ошибка', size_hint = [0.3,0.3])
            bb1 = Button(text = 'Пожалуйста, загрузите данные', on_press = pp1.dismiss)
            pp1.add_widget(bb1)
            pp1.open()
            return
        
        #duration = float(self.dur_input.text)
        fps = int(GlobVideoSet.ValueDict['FPS'])
        width = int(GlobVideoSet.ValueDict['Width'])
        height = int(GlobVideoSet.ValueDict['Heigh'])
        
        for file in self.files.selection:
            file_name = self.work_folder+'output/'+file.split('\\')[-1][:-4]
            images = convert_from_path(file)
            pix = np.array(images[0])
            cv2.imwrite(self.work_folder+'output/'+file.split('\\')[-1][:-4]+'.png', pix)
            
            meta_dict = {}
            meta_dict['name']=file.split('\\')[-1][:-4]+'.png'
            meta_dict['type']='image'
            meta_dict['duration']=10.0
            with open(self.work_folder+'output/'+file.split('\\')[-1][:-4]+'.meta', 'w') as f:
                    json.dump(meta_dict, f)
            
            
            #GenerateVideoText(file_name, duration, width, height, fps, pix)
        
        pp1 = Popup(title = 'Информация', size_hint = [0.3,0.3])
        bb1 = Button(text = 'Генерация видео завершена', on_press = pp1.dismiss)
        pp1.add_widget(bb1)
        pp1.open()


class main(App):
    def build(self):
        InitGlobSet()
        return gen_PDF()
    
            
  
if __name__ == '__main__':
    main().run()