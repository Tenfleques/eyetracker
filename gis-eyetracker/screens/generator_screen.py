# -*- coding: utf-8 -*-
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.filechooser import FileChooserIconView
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.button import Button

from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
import random
from kivy.config import Config
from kivy.uix.video import Video
from kivy.core.window import Window

from generator_libs.gen_matrix import gen_MATRIX
from generator_libs.gen_pdf import gen_PDF
from generator_libs.gen_traject import gen_TRAJECT
from generator_libs.gen_stim_series import gen_SERIES

from generator_libs.SettingBox import *
p = os.path.dirname(__file__)
PATH = os.path.join(os.path.dirname(p), 'user')
print(p)
PATH2FONT = '/'.join(p.split('\\')[:-1])+'/assets/main_font.ttf'
print("GENERATOR LOG: current dir:", PATH)
PATH2TMP = '/'.join(p.split('\\')[:-1])+'/user/tmp/'


GlobVideoSet = SettingBox(orientation = 'vertical')
GlobVideoSetMenu = Popup(title = 'Настройки', size_hint = [0.3,0.3])

def InitGlobSet():
    window_sizes=Window.size
    s3 = Parameter(key = 'FPS', label = 'FPS:', startval = 60)
    s4 = Parameter(key = 'Width', label = "_width", startval = window_sizes[0])
    s5 = Parameter(key = 'Heigh', label = "_height", startval = window_sizes[1])
        
    GlobVideoSet.add_widget(s3)
    GlobVideoSet.add_widget(s4)
    GlobVideoSet.add_widget(s5)
    GlobVideoSet.add_widget(GlobVideoSet.active_button)
    s3.change_text()
    s4.change_text()
    s5.change_text()
    
    GlobVideoSetMenu.add_widget(GlobVideoSet)
    GlobVideoSet.active_button.on_press = GlobVideoSetMenu.dismiss
    GlobVideoSet.active_button.text = 'Сохранить настройки'
    

class gen_MAIN(BoxLayout):

    def build(self):
        self.orientation = 'vertical'
        self.padding = [5, 0, 5, 20]
        self.control_lay = BoxLayout(size_hint = [1.0, 0.05])
        self.generator_lay = AnchorLayout()
        
        self.add_widget(self.generator_lay)
        self.add_widget(self.control_lay)
        
        os.makedirs(os.path.join(PATH,'data/'), exist_ok=True)
        os.makedirs(os.path.join(PATH,'data', 'input'), exist_ok=True)
        os.makedirs(os.path.join(PATH,'data', 'output'), exist_ok=True)
        os.makedirs(os.path.join(PATH,'tmp/'), exist_ok=True)
        self.gen_series = gen_SERIES(os.path.join(PATH,'data/'))
        self.gen_pdf = gen_PDF(os.path.join(PATH,'data/'), PATH2TMP, GlobVideoSet, GlobVideoSetMenu)
        print('PATH TO FONTS:', PATH2FONT)
        self.gen_matrix = gen_MATRIX(os.path.join(PATH,'data/'), PATH2TMP, GlobVideoSet, GlobVideoSetMenu, \
                                     PATH2FONT)
        self.gen_traject = gen_TRAJECT(os.path.join(PATH,'data/'), PATH2TMP, GlobVideoSet, GlobVideoSetMenu)
        
        self.control_lay.add_widget(Button(text = 'Созданные стимулы', size_hint = [0.9, 1.0], on_press = self.press_series))
        self.control_lay.add_widget(Button(text = 'Сгенерировать стимул-текст', on_press = self.press_pdf))
        self.control_lay.add_widget(Button(text = 'Сгенерировать стимул-матрицу', on_press =self.press_matrix))
        self.control_lay.add_widget(Button(text = 'Сгенерировать стимул-траекторию', on_press = self.press_traject))
        
        self.generator_lay.add_widget(self.gen_series)
        self.gen_series.files._update_files()

    def press_series(self,instance):
        self.generator_lay.clear_widgets()
        self.generator_lay.add_widget(self.gen_series)
        self.gen_series.files._update_files() 
        
    def press_pdf(self,instance):
        self.generator_lay.clear_widgets()
        self.generator_lay.add_widget(self.gen_pdf)
        
        
    def press_matrix(self,instance):
        self.generator_lay.clear_widgets()
        self.generator_lay.add_widget(self.gen_matrix)
        
        
    def press_traject(self, instance):
        self.generator_lay.clear_widgets()
        self.generator_lay.add_widget(self.gen_traject)
            
class GeneratorScreen(Screen):

    def build(self):
        InitGlobSet()
        gen_main = gen_MAIN()
        gen_main.build()
        self.add_widget(gen_main)


class main(App):
    def build(self):
        InitGlobSet()
        return gen_MAIN()


if __name__ == '__main__':
    GeneratorScreen().run()
