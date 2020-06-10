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
import json

from generator_libs.VideoGenerator import *
from generator_libs.SettingBox import *
from generator_libs.MatrixImageGen import *

PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), '/user')
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


def transliterate(name):
   """
   Автор: LarsKort
   Дата: 16/07/2011; 1:05 GMT-4;
   Не претендую на "хорошесть" словарика. В моем случае и такой пойдет,
   вы всегда сможете добавить свои символы и даже слова. Только
   это нужно делать в обоих списках, иначе будет ошибка.
   """
   # Слоаврь с заменами
   slovar = {'а':'a','б':'b','в':'v','г':'g','д':'d','е':'e','ё':'e',
      'ж':'zh','з':'z','и':'i','й':'i','к':'k','л':'l','м':'m','н':'n',
      'о':'o','п':'p','р':'r','с':'s','т':'t','у':'u','ф':'f','х':'h',
      'ц':'c','ч':'cz','ш':'sh','щ':'scz','ъ':'','ы':'y','ь':'','э':'e',
      'ю':'u','я':'ja', 'А':'A','Б':'B','В':'V','Г':'G','Д':'D','Е':'E','Ё':'E',
      'Ж':'ZH','З':'Z','И':'I','Й':'I','К':'K','Л':'L','М':'M','Н':'N',
      'О':'O','П':'P','Р':'R','С':'S','Т':'T','У':'U','Ф':'F','Х':'H',
      'Ц':'C','Ч':'CZ','Ш':'SH','Щ':'SCH','Ъ':'','Ы':'y','Ь':'','Э':'E',
      'Ю':'U','Я':'YA',',':'','?':'',' ':'_','~':'','!':'','@':'','#':'',
      '$':'','%':'','^':'','&':'','*':'','(':'',')':'','-':'','=':'','+':'',
      ':':'',';':'','<':'','>':'','\'':'','"':'','\\':'','/':'','№':'',
      '[':'',']':'','{':'','}':'','ґ':'','ї':'', 'є':'','Ґ':'g','Ї':'i',
      'Є':'e', '—':''}
        
   # Циклически заменяем все буквы в строке
   for key in slovar:
      name = name.replace(key, slovar[key])
   return name


class gen_MATRIX(BoxLayout):
    
    DATA_LOADED = False 
    
    orientation = 'horizontal'
    
    def __init__(self, work_folder, VideoSettings, VideoSetWidget, font, **kwargs):
        
        global GlobVideoSet 
        GlobVideoSet = VideoSettings
        global GlobVideoSetMenu 
        GlobVideoSetMenu = VideoSetWidget
        
        self.font = font
        self.work_folder = work_folder
        
        super(gen_MATRIX, self).__init__(**kwargs)
        #left part
        self.blay1 = SettingBox(orientation = 'vertical', size_hint = [0.3, 1.0])
        
        self.blay1.add_widget(Label(text = 'Размеры матрицы:', size_hint = [1.0, 0.4]))
        s1 = Parameter(key = 'MWidth', label = 'Ширина:', startval = 10, halign_in = 'left', valign_in = 'bottom', orientation = 'vertical')
        s2 = Parameter(key = 'MHeigh', label = 'Высота:', startval = 10, halign_in = 'left', valign_in = 'bottom',  orientation = 'vertical')
        s3 = Parameter(key = 'MFontSz', label = 'Размер шрифта:', startval = 50, halign_in = 'left', valign_in = 'bottom',  orientation = 'vertical')
        s4 = Parameter(key = 'MLetDist', label = 'Расстояние между буквами:', startval = 20, halign_in = 'left', valign_in = 'bottom',  orientation = 'vertical')
        self.blay1.add_widget(s1)
        self.blay1.add_widget(s2)
        self.blay1.add_widget(s3)
        self.blay1.add_widget(s4)
        
        self.blay1.add_widget(Label(text = 'Ключевое слово:', size_hint = [1.0, 1.0]))
        self.word = TextInput(text = '', size_hint = [1.0, 0.5], multiline = False)
        self.blay1.add_widget(self.word)
        
        
        self.blay1.add_widget(Label(text = 'Файл с ключевыми словами:', size_hint = [1.0, 0.3]))
        self.files = FileChooserListView(filters = ['*.txt'],\
                                         rootpath = self.work_folder+'input', \
                                         multiselect = True,\
                                         on_selection = self.press_select)
        
        self.blay1.add_widget(self.files)
        self.blay1.add_widget(Label(text = 'Расположение в матрице\n(0 - случайная координата):'))
        s5 = Parameter(key = 'MWidthPos', label = 'По ширине:', startval = 3, halign_in = 'left', valign_in = 'bottom',  orientation = 'vertical')
        s6 = Parameter(key = 'MHeighPos', label = 'По высоте:', startval = 3, halign_in = 'left', valign_in = 'bottom',  orientation = 'vertical')
        
        self.blay1.add_widget(s5)
        self.blay1.add_widget(s6)
        self.blay1.add_widget(Button(text = 'Горизонтально', on_press = self.press_orientation, size_hint = [1.0, 0.5]))
        self.blay1.add_widget(Button(text = 'Предпросмотр матрицы', on_press = self.press_showmatrix, size_hint = [1.0, 0.5]))
        
        s1.change_text()
        s2.change_text()
        s3.change_text()
        s4.change_text()
        
        self.add_widget(self.blay1)
        
        #right part
        blay2 = BoxLayout(orientation = 'vertical')
        self.image_lay = AnchorLayout()
        #self.image_lay = BoxLayout()
        blay3 = BoxLayout(size_hint = [1.0,0.1])
        
        blay4 = BoxLayout(orientation = 'vertical')
        #blay4.add_widget(Label(text = 'Длительность[секунды]:'))
        #self.dur_input = TextInput(text = '10')
        #blay4.add_widget(self.dur_input)
        
       # blay3.add_widget(blay4)
        blay3.add_widget(Button(text = 'Настройки', on_press = self.press_settings))
        blay3.add_widget(Button(text = 'Генерация видео', on_press = self.press_generation))
        
        blay2.add_widget(self.image_lay)
        blay2.add_widget(blay3)
        self.add_widget(blay2)
    
    def press_select(self, instance):
        print('touch')
        print(self.files.selection[-1])
        file = self.files.selection[-1]
        images = convert_from_path(file)
        pix = np.array(images[0])
        im_out = 'data/tmp/'+file.split('\\')[-1]+'.png'
        cv2.imwrite(im_out, pix)
        self.image_lay.clear_widgets()
        self.image_lay.add_widget(Image(source = os.path.join(PATH, im_out)))
        self.DATA_LOADED = True
        
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
    
    
    tmpstate = 1;
    curr_pict_id = 1;
    
    matrix_shown = False
    
    def press_showmatrix(self,instance):
        GlobVideoSet.update()
        #duration = float(self.dur_input.text)
        fps = int(GlobVideoSet.ValueDict['FPS'])
        width = int(GlobVideoSet.ValueDict['Width'])
        height = int(GlobVideoSet.ValueDict['Heigh'])
        
        self.blay1.update()
        X_size = int(self.blay1.ValueDict['MWidth'])
        Y_size = int(self.blay1.ValueDict['MHeigh'])
        X_start = int(self.blay1.ValueDict['MWidthPos'])-1
        Y_start = int(self.blay1.ValueDict['MHeighPos'])-1
        
        font_size = int(self.blay1.ValueDict['MFontSz'])
        font_space = int(self.blay1.ValueDict['MLetDist'])
        
        word = self.word.text
        if word == '':
            pp1 = Popup(title = 'Ошибка', size_hint = [0.3,0.3])
            bb1 = Button(text = 'Пожалуйста, введите ключевое слово', on_press = pp1.dismiss)
            pp1.add_widget(bb1)
            pp1.open()
            return
            
        M = self.AdjustAndGenerateMatrix(word, X_size, Y_size, X_start, Y_start, self.orientation) 
        
        image = get_Matrix_image(M, font_size, font_space, width, height, self.font)  
        
        im_out = self.work_folder+'tmp/matrix'+str(self.curr_pict_id)+'.png'
        
        if os.path.exists(im_out):
            os.remove(im_out)
        self.curr_pict_id = self.curr_pict_id+1
        
        im_out = self.work_folder+'tmp/matrix'+str(self.curr_pict_id)+'.png'
        
        
      
        
        #os.remove('data/tmp/matrix.png')
        cv2.imwrite(im_out, image)
        
        self.image_lay.clear_widgets()
        self.image_lay.add_widget(Image(source = im_out))
    
        self.matrix_shown = True
    
    def AdjustAndGenerateMatrix(self, word, X_size, Y_size, X_start, Y_start, orientation):
        X_start_actual = X_start
        Y_start_actual = Y_start
               
        if self.orientation == 'random':
            local_orientation = random.choice(['horizontal', 'vertical'])
        else:
            local_orientation = self.orientation
         
        if (X_start_actual == -1):
            if (local_orientation == 'horizontal'):
                if len(word)>X_size:
                    X_start_actual = 0
                else:
                    X_start_actual = random.randint(0,X_size-len(word))
            else:
                X_start_actual = random.randint(0,X_size-1)
                
        if (Y_start_actual == -1):
            if (local_orientation == 'vertical'):
                if len(word)>Y_size:
                    Y_start_actual = 0
                else:
                    Y_start_actual = random.randint(0,Y_size-len(word))
            else:
                Y_start_actual = random.randint(0,Y_size-1)
                
            
        M = self.GenerateMatrix(word, X_size, Y_size, X_start_actual, Y_start_actual, local_orientation)
        return M
            
            
    def GenerateMatrix(self, word, sizeX, sizeY, startX, startY, orientation):
        alphabet = "АБГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ"
        M = [[random.choice(alphabet) for i in range(sizeX)] for j in range(sizeY)]
        
        posX = startX
        posY = startY
        for k,w in enumerate(word):
            
            if (posX<sizeX)and(posY<sizeY):
                M[posY][posX] = w
            if orientation=='vertical':
                posY = posY+1
            else:
                posX = posX+1
                
        return M
        
    
    
    def press_generation(self, instance):
        
        word_list = []
        print(self.files.selection)
        
        if (self.word.text != ''):
            word_list.append(self.word.text)
            
        if self.files.selection!=[]:
            for a in open(self.files.selection[0],'r',encoding='utf-8').readlines():
                a = a.strip()
                word_list.append(a)
                
        print(word_list)
        if word_list == []:
            pp1 = Popup(title = 'Ошибка', size_hint = [0.3,0.3])
            bb1 = Button(text = 'Пожалуйста, загрузите данные', on_press = pp1.dismiss)
            pp1.add_widget(bb1)
            pp1.open()
            return
        

        GlobVideoSet.update()
        #duration = float(self.dur_input.text)
        fps = int(GlobVideoSet.ValueDict['FPS'])
        width = int(GlobVideoSet.ValueDict['Width'])
        height = int(GlobVideoSet.ValueDict['Heigh'])
        
        self.blay1.update()
        X_size = int(self.blay1.ValueDict['MWidth'])
        Y_size = int(self.blay1.ValueDict['MHeigh'])
        X_start = int(self.blay1.ValueDict['MWidthPos'])-1
        Y_start = int(self.blay1.ValueDict['MHeighPos'])-1
        
        font_size = int(self.blay1.ValueDict['MFontSz'])
        font_space = int(self.blay1.ValueDict['MLetDist'])
        
        
        
        for i,word in enumerate(word_list):
            image = None
            
            if (i==0)and(word==self.word.text)and(self.matrix_shown):
                im_out = self.work_folder+'tmp/matrix'+str(self.curr_pict_id)+'.png'
                image = cv2.imread(im_out)
            else:
                M = self.AdjustAndGenerateMatrix(word, X_size, Y_size, X_start, Y_start, self.orientation) 
                image = get_Matrix_image(M, font_size, font_space, width, height, 'fonts/main_font.ttf')
            
            word_trans = transliterate(word)
            
            file_name = self.work_folder+'output/'+'_'.join([word_trans, str(X_size), str(Y_size), str(X_start), str(Y_start), self.orientation])
            
            
            
            im = PilImage.fromarray(image)
            im.save(file_name+'.png')
            
            file_name_pref='_'.join([word_trans, str(X_size), str(Y_size), str(X_start), str(Y_start), self.orientation])
            meta_dict = {}
            meta_dict['name']=file_name_pref+'.png'
            meta_dict['type']='image'
            meta_dict['duration']=10.0
            with open(self.work_folder+'output/'+file_name_pref+'.meta', 'w') as f:
                    json.dump(meta_dict, f)
            #file_name = file_name.encode('utf-8')
            #cv2.imwrite(file_name+'.png', image)
            #scipy.misc.toimage(image, cmin=0.0, cmax=...).save(file_name+'.png')
            #GenerateVideoText(file_name, duration, width, heigh, fps, image)
        
        pp1 = Popup(title = 'Информация', size_hint = [0.3,0.3])
        bb1 = Button(text = 'Генерация стимулов завершена', on_press = pp1.dismiss)
        pp1.add_widget(bb1)
        pp1.open()
                        
                
            
            
        


class main(App):
    def build(self):
        InitGlobSet()
        return gen_MATRIX()
    
            
  
if __name__ == '__main__':
    main().run()