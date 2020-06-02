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
# sys.path.append('libs')
from gen_matrix import gen_MATRIX
from gen_pdf import gen_PDF
from gen_traject import gen_TRAJECT
from SettingBox import *

from pathlib import Path
PATH = str(Path(__file__).parent.absolute()).replace('\\','/')+'/'
print("current dir:", PATH)


GlobVideoSet = SettingBox(orientation = 'vertical')
GlobVideoSetMenu = Popup(title = 'Настройки', size_hint = [0.3,0.3])
def InitGlobSet():
    window_sizes=Window.size
    s3 = Parameter(key = 'FPS', label = 'FPS:', startval = 60)
    s4 = Parameter(key = 'Width', label = 'Width:', startval = window_sizes[0])
    s5 = Parameter(key = 'Heigh', label = 'Height:', startval = window_sizes[1])

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

        def __init__(self, **kwargs):
            super(gen_MAIN, self).__init__(**kwargs)
            self.orientation = 'vertical'
            self.control_lay = BoxLayout(size_hint = [1.0, 0.05])
            self.generator_lay = AnchorLayout();

            self.add_widget(self.generator_lay)
            self.add_widget(self.control_lay)


            self.gen_pdf = gen_PDF(PATH+'data/', GlobVideoSet, GlobVideoSetMenu);
            self.gen_matrix = gen_MATRIX(PATH+'data/', GlobVideoSet, GlobVideoSetMenu, PATH+'fonts/main_font.ttf');
            self.gen_traject = gen_TRAJECT(PATH+'data/', GlobVideoSet, GlobVideoSetMenu);

            self.control_lay.add_widget(Button(text = 'Загрузить в базу данных',size_hint = [0.9, 1.0]))
            self.control_lay.add_widget(Button(text = 'Сгенерировать стимул-текст', on_press = self.press_pdf))
            self.control_lay.add_widget(Button(text = 'Сгенерировать стимул-матрицу', on_press =self.press_matrix))
            self.control_lay.add_widget(Button(text = 'Сгенерировать стимул-траекторию', on_press = self.press_traject))



        def press_pdf(self,instance):
            self.generator_lay.clear_widgets()
            self.generator_lay.add_widget(self.gen_pdf)


        def press_matrix(self,instance):
            self.generator_lay.clear_widgets()
            self.generator_lay.add_widget(self.gen_matrix)


        def press_traject(self, instance):
            self.generator_lay.clear_widgets()
            self.generator_lay.add_widget(self.gen_traject)

class main(App):
    def build(self):
        InitGlobSet()
        return gen_MAIN()



if __name__ == '__main__':
    main().run()
