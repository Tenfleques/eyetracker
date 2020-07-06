from kivy.app import App
from kivy.lang import Builder
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.core.window import Window
from kivy.uix.button import Button
from  kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
import random
from kivy.config import Config
from kivy.uix.video import Video
from kivy.core.window import Window
from functools import partial
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.label import Label
from kivy.properties import BooleanProperty
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.uix.behaviors import FocusBehavior
from kivy.uix.recycleview.layout import LayoutSelectionBehavior
from  kivy.clock import Clock
import json
import copy
import os
from kivy.uix.image import Image
import threading
import cv2
from  kivy.graphics.texture import Texture
from generator_libs.video_player_kivy import *


play_func = None


class gen_SERIES(BoxLayout):
    def __init__(self, work_folder, **kwargs):
        super(gen_SERIES, self).__init__(**kwargs)
        self.orientation = 'vertical'
        
        self.work_folder = work_folder
        
        
        
        self.video_lay = BoxLayout()
        self.control_lay = BoxLayout(size_hint = [1.0, 0.1])
        
        
        self.files = FileChooserListView(filters = ['*.meta', '*.meta_s'],\
                                         rootpath = self.work_folder+'output', \
                                         multiselect = False,
                                         on_submit = self.press_double_click)
        
        self.rv = RV()
        
        meta_lay = BoxLayout(orientation = 'vertical')
        meta_lay.add_widget(Label(text = 'Сохраненные стимулы и серии', size_hint = [1.0, 0.05]))
        meta_lay.add_widget(self.files)
        
        
        ser_lay = BoxLayout(orientation = 'vertical')
        
        name_lay = BoxLayout(size_hint = [1.0, 0.05])
        lab = Label(text = 'Серия стимулов:', halign = 'right')
        name_lay.add_widget(lab)
        
        
        self.series_name = TextInput(text = self.gen_series_name(), multiline = False)
        name_lay.add_widget(self.series_name)
        
        ser_lay.add_widget(name_lay)
        ser_lay.add_widget(self.rv)
        
        self.video_lay.add_widget(meta_lay)
        self.video_lay.add_widget(ser_lay)
        
        #self.control_lay.add_widget(Button(text = 'Просмотр стимула', size_hint = [.8, 1.0], on_press = self.press_preview))
        #self.control_lay.add_widget(Button(text = 'Загрузить', on_press = self.press_add))
        #self.control_lay.add_widget(Button(text = 'Установить\nдлительность', halign = 'center',on_press = self.press_setduration))
        self.control_lay.add_widget(Button(text = 'Переместить вверх', on_press = self.press_moveUp))
        self.control_lay.add_widget(Button(text = 'Переместить вниз', on_press = self.press_moveDown))
        self.control_lay.add_widget(Button(text = 'Удалить стимул', on_press = self.press_moveOut))
        self.control_lay.add_widget(Button(text = 'Сохранить серию', on_press = self.press_Save))
        self.control_lay.add_widget(Button(text = 'Очистить серию', on_press = self.press_Clear))
        
        global play_func
        play_func = self.press_preview
        
        self.add_widget(self.video_lay)
        self.add_widget(self.control_lay)
    
    def press_preview(self, instance):
        if self.rv.selected_idx == None:
            pp1 = Popup(title = 'Ошибка', size_hint = [0.3,0.3])
            bb1 = Button(text = 'Пожалуйста, выберите стимул из серии', on_press = pp1.dismiss)
            pp1.add_widget(bb1)
            pp1.open()
            return
        print(self.rv.selected_idx)
        
        info = self.rv.data[self.rv.selected_idx]
        stimtype = info['type']
        video_duration = info['duration']
        self.anch = Popup(title = 'Предпросмотр')
        path = self.work_folder+'output/'+info['path']
        
        if (stimtype=='video'):
            #video = Video(source = path)
            #self.anch.add_widget(video)
            #video.state = 'play'
            #self.anch.open()
            #Clock.schedule_once(self.my_callback, video_duration)
            #os.system(path)
            player = MyPlayerWidget(self.anch)
            self.anch.add_widget(player)
            #player.button.on_press = self.anch.dismiss
            player.start_play(path)
            self.anch.open()
            return;
        
        else:
            image = Image(source = path)
            bshow = BoxLayout(orientation = 'vertical')
            bshow.add_widget(image)
            bshow.add_widget(Button(text =  'Закрыть', size_hint = [1.0,0.05], on_press = self.anch.dismiss))
            
            self.anch.add_widget(bshow)
            self.anch.open()
            #Clock.schedule_once(self.my_callback, video_duration)
            return
        
    def my_callback(self, dt):
        self.anch.clear_widgets()
        self.anch.dismiss()
        
    
    def play_video(self, video, image):
        cap = cv2.VideoCapture(video) 
        fps = cap.get(cv2.CAP_PROP_FPS)
        print(fps)
        # Check if camera opened successfully 
        if (cap.isOpened()== False):  
          print("Error opening video  file") 
        
        cnt = 0
        # Read until video is completed 
        while(cap.isOpened()): 
          cnt
          # Capture frame-by-frame 
          ret, frame = cap.read() 
          if ret == True: 
           
            # Display the resulting frame 
            #cv2.imshow('Frame', frame) 
           
            buf = frame.tostring()
            texture = Texture.create(size=(frame.shape[1], frame.shape[0]), colorfmt='bgr')
            texture.blit_buffer(buf, colorfmt='bgr', bufferfmt='ubyte')
    
            image.texture = texture
            
            
            
            # Press Q on keyboard to  exit 
            if cv2.waitKey(int(1000 / fps)):
              break
           
          # Break the loop 
          else:  
            break
         
        # When everything done, release  
        # the video capture object 
        cap.release() 
           
        # Closes all the frames 
        cv2.destroyAllWindows() 
    
    
    def gen_series_name(self):
        
        number = 0
        succ = False
        while not succ:
            name = 'series#'+str(number)
            filename = self.work_folder+'output/'+name+'.meta_s'
            if os.path.exists(filename):
                number = number+1
            else:
                return name
    
    def press_add(self, instance):
        if len(self.files.selection)==0:
            pp1 = Popup(title = 'Ошибка', size_hint = [0.3,0.3])
            bb1 = Button(text = 'Пожалуйста, выберите стимул', on_press = pp1.dismiss)
            pp1.add_widget(bb1)
            pp1.open()
            return
        
        extention = self.files.selection[0].split('.')[-1]
        
        if extention == 'meta':
        
            name = ''.join(self.files.selection[0].split('\\')[-1].split('.')[:-1])
            
            info = None
            with open(self.files.selection[0]) as json_file:
                info = json.load(json_file)
                
            path = info['name'];
            name = path[:-4]
            stimtype = info['type']
            shown_label = name+'   ['+stimtype+']'
            
            
            
            data = {}
            
            data['name'] = name
            data['path'] = path
            data['type'] = stimtype
            data['duration'] = info['duration']
            
            data['text'] = shown_label+'['+str(info['duration'])+' sec]'
            
            info = self.files.selection[0].split('\\')[-1]
            self.rv.data.append(data)
        
        elif extention == 'meta_s':
            info = None
            with open(self.files.selection[0]) as json_file:
                info = json.load(json_file)
            self.rv.data = info
        
        
        pass
        
    
    def press_double_click(self, instance, selection, touch):
        self.press_add(None)
    
    def press_setduration(self, instance):
        
        if self.rv.selected_idx == None:
            pp1 = Popup(title = 'Ошибка', size_hint = [0.3,0.3])
            bb1 = Button(text = 'Пожалуйста, выберите стимул из серии', on_press = pp1.dismiss)
            pp1.add_widget(bb1)
            pp1.open()
            return
        print(self.rv.selected_idx)
        
        if self.rv.data[self.rv.selected_idx]['type']=='video':
            pp1 = Popup(title = 'Ошибка', size_hint = [0.3,0.3])
            bb1 = Button(text = 'Вы не можете установить длительность для видео', on_press = pp1.dismiss)
            pp1.add_widget(bb1)
            pp1.open()
            return
        
        currtime = self.rv.data[self.rv.selected_idx]['duration']
        pp2 = Popup(title = 'Введите желаемую длительность в секундах', size_hint = [0.3,0.2])
        blay = BoxLayout(orientation = 'vertical')
        dur_text = TextInput(input_filter = 'float', text = str(currtime))
        blay.add_widget(dur_text)
        
        func = partial(self.set_duration, pp2, dur_text, self.rv.selected_idx)
        blay.add_widget(Button(text =  'Установить', on_press = func, size_hint = [1.0,0.2]))
        pp2.add_widget(blay)
        pp2.open();
        
    def set_duration(self, pp, dur_text, index_sel, instance):
        duration = float(dur_text.text)
        self.rv.data[index_sel]['duration'] = duration
        shownname = self.rv.data[index_sel]['name']+'   ['+self.rv.data[index_sel]['type']+']['+str(duration)+' sec]'
        data = self.rv.data[index_sel]
        data['text']=shownname
        print(data)
        self.rv.data[index_sel] = data
        pp.dismiss()
        
    def press_moveUp(self, instance):
        if self.rv.selected_idx == None:
            pp1 = Popup(title = 'Ошибка', size_hint = [0.3,0.3])
            bb1 = Button(text = 'Пожалуйста, выберите стимул из серии', on_press = pp1.dismiss)
            pp1.add_widget(bb1)
            pp1.open()
            return
        
        
        if self.rv.selected_idx == 0:
            pp1 = Popup(title = 'Ошибка', size_hint = [0.3,0.3])
            bb1 = Button(text = 'Стимул стоит на первом месте', on_press = pp1.dismiss)
            pp1.add_widget(bb1)
            pp1.open()
            return
        
        data_tmp = copy.deepcopy(self.rv.data[self.rv.selected_idx-1])
        self.rv.data[self.rv.selected_idx-1] = self.rv.data[self.rv.selected_idx]
        self.rv.data[self.rv.selected_idx] = data_tmp
        
        pass
        
    def press_moveDown(self, instance):
        if self.rv.selected_idx == None:
            pp1 = Popup(title = 'Ошибка', size_hint = [0.3,0.3])
            bb1 = Button(text = 'Пожалуйста, выберите стимул из серии', on_press = pp1.dismiss)
            pp1.add_widget(bb1)
            pp1.open()
            return
        
        if self.rv.selected_idx == len(self.rv.data)-1:
            pp1 = Popup(title = 'Ошибка', size_hint = [0.3,0.3])
            bb1 = Button(text = 'Стимул стоит на последнем месте', on_press = pp1.dismiss)
            pp1.add_widget(bb1)
            pp1.open()
            return
        
        data_tmp = copy.deepcopy(self.rv.data[self.rv.selected_idx+1])
        self.rv.data[self.rv.selected_idx+1] = self.rv.data[self.rv.selected_idx]
        self.rv.data[self.rv.selected_idx] = data_tmp
            
        pass
        
    def press_moveOut(self, instance):
        if self.rv.selected_idx == None:
            pp1 = Popup(title = 'Ошибка', size_hint = [0.3,0.3])
            bb1 = Button(text = 'Пожалуйста, выберите стимул из серии', on_press = pp1.dismiss)
            pp1.add_widget(bb1)
            pp1.open()
            return
        
        idx = self.rv.selected_idx
        self.rv.data = self.rv.data[:idx]+self.rv.data[idx+1:]
        self.rv.selected_idx = None
        
        
        pass
    
    def press_Save(self, instance):
        if self.rv.data == []:
            
            pp1 = Popup(title = 'Ошибка', size_hint = [0.3,0.3])
            bb1 = Button(text = 'В серии нет стимулов!', on_press = pp1.dismiss)
            pp1.add_widget(bb1)
            pp1.open()
            return
        
        
        with open(self.work_folder+'output/'+self.series_name.text+'.meta_s', 'w') as f:
                    json.dump(self.rv.data, f)
        self.files.selection = []
        self.files._update_files() 
        self.series_name.text = self.gen_series_name()
        pass
    
    def press_Clear(self, instance):
        self.rv.data = []
        self.rv.selected_idx = None







#=========================SELECTION MAGIC DO NOT TOUCH!==========================================
Builder.load_string('''
<SelectableLabel>:
    # Draw a background to indicate selection
    canvas.before:
        Color:
            rgba: (.0, 0.9, .1, .3) if self.selected else (0, 0, 0, 1)
        Rectangle:
            pos: self.pos
            size: self.size
<RV>:
    viewclass: 'SelectableLabel'
    SelectableRecycleBoxLayout:
        default_size: None, dp(25)
        default_size_hint: 1, None
        size_hint_y: None
        height: self.minimum_height
        orientation: 'vertical'
        multiselect: False
        touch_multiselect: False
''')

import datetime
class SelectableRecycleBoxLayout(FocusBehavior, LayoutSelectionBehavior,
                                 RecycleBoxLayout):
    ''' Adds selection and focus behaviour to the view. '''


class SelectableLabel(RecycleDataViewBehavior, Label):
    ''' Add selection support to the Label '''
    index = None
    selected = BooleanProperty(False)
    selectable = BooleanProperty(True)
    dt_double_click = datetime.timedelta(milliseconds = 300)
    def refresh_view_attrs(self, rv, index, data):
        ''' Catch and handle the view changes '''
        self.index = index
        return super(SelectableLabel, self).refresh_view_attrs(
            rv, index, data)

    def on_touch_down(self, touch):
        ''' Add selection on touch down '''
        if super(SelectableLabel, self).on_touch_down(touch):
            return True
        if self.collide_point(*touch.pos) and self.selectable:
            return self.parent.select_with_touch(self.index, touch)

    def apply_selection(self, rv, index, is_selected):
        ''' Respond to the selection of items in the view. '''
 
        if (is_selected):
            press_time = datetime.datetime.now()
            double_click = ((press_time-rv.last_sel_time)<self.dt_double_click)
            #print('time:',(press_time-rv.last_sel_time))
            #print('dt:', self.dt_double_click)
            #print('sel:', self.selected)
            if(rv.selected_idx == index)and(double_click):
                rv.last_sel_time = press_time
                #self.press_setduration(rv)
                self.press_contextMenu(rv)
                
                
                
                
                
                
            else:
                rv.last_sel_time = press_time
        
        self.selected = is_selected
         
        if is_selected:
            rv.selected_idx = index
            #print("selection changed to {0}".format(rv.data[index]))
        else:
            pass
           # print("selection removed for {0}".format(rv.data[index]))
        
    pp1 = Popup(title = 'Контекстное меню', size_hint = [0.3,0.3])   
    menu_loaded = False
    
    
    def press_contextMenu(self, rv):
        
        
        self.pp1 = Popup(title = 'Контекстное меню', size_hint = [0.3,0.3])
        blay = BoxLayout(orientation = 'vertical')
        
        func = partial(self.press_setduration, rv)
        
        
        
        blay.add_widget(Button(text = 'Показ стимула', on_press = self.press_preview))
        blay.add_widget(Button(text = 'Длительность', on_press = func))
        
        
        func_del = partial(self.press_moveOut, rv)
        blay.add_widget(Button(text = 'Удалить', on_press = func_del))
        blay.add_widget(Button(text = 'Закрыть меню', on_press = self.pp1.dismiss))
               
        self.pp1.add_widget(blay)
        self.menu_loaded = True
        
        self.pp1.open()
    
    
    
    
    def press_setduration(self, rv, instance):
        
        if rv.selected_idx == None:
            pp1 = Popup(title = 'Ошибка', size_hint = [0.3,0.3])
            bb1 = Button(text = 'Пожалуйста, выберите стимул из серии', on_press = pp1.dismiss)
            pp1.add_widget(bb1)
            pp1.open()
            return
        print(rv.selected_idx)
        
        if rv.data[rv.selected_idx]['type']=='video':
            pp1 = Popup(title = 'Ошибка', size_hint = [0.3,0.3])
            bb1 = Button(text = 'Вы не можете установить длительность для видео', on_press = pp1.dismiss)
            pp1.add_widget(bb1)
            pp1.open()
            return
        
        
        currtime = rv.data[rv.selected_idx]['duration']
        pp2 = Popup(title = 'Введите желаемую длительность в секундах', size_hint = [0.3,0.2])
        blay = BoxLayout(orientation = 'vertical')
        dur_text = TextInput(input_filter = 'float', text = str(currtime))
        blay.add_widget(dur_text)
        
        func = partial(self.set_duration, pp2, dur_text, rv.selected_idx, rv)
        blay.add_widget(Button(text =  'Установить', on_press = func, size_hint = [1.0,0.2]))
        pp2.add_widget(blay)
        pp2.open();
        self.pp1.dismiss()
        
    def set_duration(self, pp, dur_text, index_sel, rv, instance):
        duration = float(dur_text.text)
        rv.data[index_sel]['duration'] = duration
        shownname = rv.data[index_sel]['name']+'   ['+rv.data[index_sel]['type']+']['+str(duration)+' sec]'
        data = rv.data[index_sel]
        data['text']=shownname
        print(data)
        rv.data[index_sel] = data
        pp.dismiss()
        
        
    def press_preview(self, instance):
        global play_func
        self.pp1.dismiss()
        play_func(instance)
        
        
        
    def press_moveOut(self, rv, instance):
        if rv.selected_idx == None:
            pp1 = Popup(title = 'Ошибка', size_hint = [0.3,0.3])
            bb1 = Button(text = 'Пожалуйста, выберите стимул из серии', on_press = pp1.dismiss)
            pp1.add_widget(bb1)
            pp1.open()
            return
        
        idx = rv.selected_idx
        rv.data = rv.data[:idx]+rv.data[idx+1:]
        rv.selected_idx = None
        self.pp1.dismiss()


class RV(RecycleView):
    def __init__(self, **kwargs):
        super(RV, self).__init__(**kwargs)
        self.data = []
        self.selected_idx = None
        self.last_sel_time = datetime.datetime.now()

class main(App):
    def build(self):
        ps = gen_SERIES()
        return ps
    
            
  
if __name__ == '__main__':
    main().run()
    
