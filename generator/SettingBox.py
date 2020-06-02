from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.gridlayout import GridLayout
from kivy.core.window import Window
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.lang import Builder

from pathlib import Path
PATH = str(Path(__file__).parent.absolute()).replace('\\','/')+'/'
print("current dir:", PATH)

Builder.load_file(PATH+'SettingBox.kv')
Window.show_cursor = True
# Create both screens. Please note the root.manager.current: this is how
# you can control the ScreenManager from kv. Each screen has by default a
# property manager that gives you the instance of the ScreenManager used.

from kivy.uix.popup import Popup
import random
from pathlib import Path
from os import path

def decision(probability):
    return random.random() < probability

class Parameter(BoxLayout):
    def __init__(self, key, inputtype = 'int', label = "label", halign_in = 'right', valign_in = 'middle', startval = -1, **kwargs):
        print('newone')
        super(Parameter, self).__init__(**kwargs)
        print(label)
        self.ids['l_val'].text = label
        self.ids['l_val'].halign = halign_in
        self.ids['l_val'].valign = valign_in
        self.name = key
        
        self.ids['t_val'].text = str(startval)
        #self.parent.ValueDict[label] = str(startval)
        self.value = str(startval)
        
        if (inputtype=='int'):
            self.ids['t_val'].input_filter = 'int';
        elif(inputtype == 'float'):
            self.ids['t_val'].input_filter = 'float';
        elif(inputtype == 'text'):
            pass
        
        pass
        
    def press(self):
        print(self.value)
    
    def checkreturn(self):
        if self.ids['t_val'].text[-1] == '\n':
            self.ids['t_val'].text = self.ids['t_val'].text[:-1]
    
    def on_change_text(self):
        if len(self.ids['t_val'].text)==0:
            return
        if (self.ids['t_val'].input_filter == 'int')or(self.ids['t_val'].input_filter == 'float'):
            if self.ids['t_val'].text[0]=='0':
                self.ids['t_val'].text = self.ids['t_val'].text[1:]
    
    def change_text(self):
        key = self.name
        value = self.value
        print(key, value)
        
        self.parent.ValueDict[key] = value
        pass
    
    def set_label_align(self,align):
        self.ids['l_val'].halign = align
    pass
        

class Changer(BoxLayout):
    def __init__(self, label = "label1", startval = -1, **kwargs):
        super(Changer, self).__init__(**kwargs)
        print(label)
        self.ids['l_val'].text = label
        self.name = label
        
        self.ids['b_val'].text = str(startval)
        self.parent.ValueDict[label] = str(startval)
        self.value = str(startval)
        pass
        
    def press(self):
        print(self.value)
        
        
    def change_mode(self):
        print('modechange')
        pass
    pass


class SettingBox(BoxLayout):
    ValueDict = {}
    def __init__(self, label = "label1", startval = -1, **kwargs):
        super(SettingBox, self).__init__(**kwargs)
        self.active_button = Button()
    def update(self):
        for i, l in enumerate(self.children):
            if type(l) is Parameter:
                self.children[i].change_text()