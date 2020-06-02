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
import random
from kivy.config import Config
from kivy.uix.video import Video
from kivy.core.window import Window

import sys
#sys.path.append('libs')
from VideoGenerator import *
from SettingBox import *
from MatrixImageGen import *
from VideoSpeedRegulator import *
from ImagePrep import *
from SvgGenerator import *

from pathlib import Path
PATH = str(Path(__file__).parent.absolute()).replace('\\','/')+'/'
print("current dir:", PATH)

import scipy.misc
from pdf2image import convert_from_path, convert_from_bytes
from PIL import Image as PilImage
import numpy as np
import cv2
import os
from kivy.uix.image import Image
#Window.fullscreen = False
Window.show_cursor = True
window_sizes=Window.size
# -*- coding: utf-8 -*-

Config.set('graphics', 'width', window_sizes[0])
Config.set('graphics', 'height', window_sizes[1])
Config.set('graphics', 'fullscreen', False)
Config.write()



GlobVideoSet = None
GlobVideoSetMenu = None

class gen_TRAJECT(BoxLayout):

    DATA_LOADED = False

    orientation = 'horizontal'

    selected_image = ''
    selected_countur = None

    clockwise = True
    preproc = True


    def __init__(self, work_folder, VideoSettings, VideoSetWidget, **kwargs):

        global GlobVideoSet
        GlobVideoSet = VideoSettings
        global GlobVideoSetMenu
        GlobVideoSetMenu = VideoSetWidget

        self.work_folder = work_folder


        super(gen_TRAJECT, self).__init__(**kwargs)
        #left part
        self.blay1 = SettingBox(orientation = 'vertical', size_hint = [0.3, 1.0])

        self.blay1.add_widget(Label(text = 'Файл с изображением:', size_hint = [1.0, 0.05]))


        self.files = FileChooserListView(filters = ['*.png', '*.jpg'],\
                                         rootpath = self.work_folder+'input', \
                                         multiselect = False,\
                                         on_submit = self.press_select_image)

        self.blay1.add_widget(self.files)

        self.image_preview = AnchorLayout()

        self.blay1.add_widget(self.image_preview)
        self.blay1.add_widget(Button(text = 'По часовой стрелке', on_press = self.press_clockwise, size_hint = [1.0, 0.3]))
        self.blay1.add_widget(Button(text = 'Постобработка контура: включена', on_press = self.press_preproc, size_hint = [1.0, 0.3]))
        self.blay1.add_widget(Button(text = 'Загрузить изображение \nи сгенерировать контур', on_press = self.press_select, size_hint = [1.0, 0.3]))


        self.add_widget(self.blay1)

        blay2 = BoxLayout(orientation = 'vertical')

        self.image_lay = BoxLayout(orientation = 'vertical')
        self.contour_lay =  AnchorLayout()
        #self.contour_lay.add_widget(Button(text = 'image_area'))

        self.speed_lay = BoxLayout(size_hint = [1.0,0.31])
        self.speed_painter = MyPaintWidget()
        self.blay_speed = SettingBox(orientation = 'vertical', size_hint = [0.5,1.0])


        s1 = Parameter(key = 'MaxSpeed', label = 'max speed:', startval = 200, halign_in = 'left', valign_in = 'bottom', orientation = 'vertical')
        s2 = Parameter(key = 'MinSpeed', label = 'min speed:', startval = 50, halign_in = 'left', valign_in = 'bottom',  orientation = 'vertical')



        self.blay_speed.add_widget(s1)
        self.blay_speed.add_widget(s2)

        s1.change_text()
        s2.change_text()


        self.speed_lay.add_widget(self.blay_speed)
        self.speed_lay.add_widget(self.speed_painter)
        self.image_lay.add_widget(self.contour_lay)
        self.image_lay.add_widget(self.speed_lay)

        blay2.add_widget(self.image_lay)


        blay3 = BoxLayout(size_hint = [1.0,0.1])
        blay4 = BoxLayout(orientation = 'vertical', size_hint = [1.0,1.0])
        blay4.add_widget(Label(text = 'Длительность[секунды]:'))
        self.dur_input = TextInput(text = '10')
        blay4.add_widget(self.dur_input)

        blay3.add_widget(blay4)
        blay3.add_widget(Button(text = 'Настройки', on_press = self.press_settings))
        blay3.add_widget(Button(text = 'Генерация видео', on_press = self.press_generation))


        blay2.add_widget(blay3)
        self.add_widget(blay2)
        self.spacing = 2;


    def press_preproc(self, instance):
        if self.preproc:
            self.preproc = False
            instance.text = 'Постобработка контура: отключена'
        else:
            self.preproc = True
            instance.text = 'Постобработка контура: включена'


    def press_clockwise(self,instance):
        if self.clockwise:
            self.clockwise = False
            instance.text = 'Против часовой стрелки'
        else:
            self.clockwise = True
            instance.text = 'По часовой стрелке'

    def press_select_image(self, instance, selection, touch):
        im = Image(source = self.files.selection[0])
        self.image_preview.clear_widgets()
        self.image_preview.add_widget(im);
        self.selected_image = self.files.selection[0]
        #self.speed_painter.reinit();
        #self.speed_painter.redraw();

    cnter=1;
    def press_select(self, instance):

        image = cv2.imread(self.selected_image)
        image, counters = process_image(image, self.preproc)


        self.cnter = self.cnter+1
        cv2.imwrite(self.work_folder+'tmp/'+str(self.cnter)+'.png', image)


        self.contour_lay.clear_widgets()
        print('source:',self.work_folder+'tmp/'+str(self.cnter)+'.png')
        self.contour_lay.add_widget(Image(source = self.work_folder+'tmp/'+str(self.cnter)+'.png'))
        self.selected_countur = [a[0] for a in counters]
        self.speed_painter.reinit();
        self.speed_painter.redraw();

    def press_postproc(self, instance):
        pass

    def press_settings(self, instance):
        GlobVideoSetMenu.open()

    def press_orientation(self,instance):
        if self.orientation == 'horizontal':
            self.orientation = 'vertical'
            instance.text = 'Вертикально'
        elif self.orientation == 'vertical':
            self.orientation = 'random'
            instance.text = 'Случайно'

        elif self.orientation == 'random':
            self.orientation = 'horizontal'
            instance.text = 'Горизонтально'

    def press_generation(self, instance):

        if self.selected_countur == None:
            pp1 = Popup(title = 'Ошибка', size_hint = [0.3,0.3])
            bb1 = Button(text = 'Пожалуйста, загрузите данные', on_press = pp1.dismiss)
            pp1.add_widget(bb1)
            pp1.open()
            return


        GlobVideoSet.update()
        duration = float(self.dur_input.text)
        fps = int(GlobVideoSet.ValueDict['FPS'])
        width = int(GlobVideoSet.ValueDict['Width'])
        height = int(GlobVideoSet.ValueDict['Heigh'])


        self.blay_speed.update()
        min_speed = float(self.blay_speed.ValueDict['MaxSpeed'])
        max_speed = float(self.blay_speed.ValueDict['MinSpeed'])

        fname = self.selected_image.split('\\')[-1][:-4]
        speed_vect = self.speed_painter.get_speed_vector(min_speed, max_speed)
        if not self.clockwise:
            self.selected_countur = self.selected_countur[::-1]
        image = cv2.imread(self.selected_image)
        GenerateVideoSVG(self.work_folder+'output/'+fname, image, self.selected_countur, speed_vect, width, height, fps)

        pp1 = Popup(title = 'Информация', size_hint = [0.3,0.3])
        bb1 = Button(text = 'Генерация видео завершена', on_press = pp1.dismiss)
        pp1.add_widget(bb1)
        pp1.open()



class main(App):
    def build(self):
        InitGlobSet()
        ps = gen_TRAJECT()
        ##ps.painter.drawbase()
        return ps



if __name__ == '__main__':
    main().run()
