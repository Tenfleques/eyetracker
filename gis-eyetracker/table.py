from kivy.uix.gridlayout import GridLayout
from kivy.lang.builder import Builder
from kivy.uix.button import Button
import os
import json
import math
from helpers import get_local_str_util
import logging
logging.basicConfig(filename='./logs/view_trackbox.log',level=logging.DEBUG)

widget = Builder.load_file(os.path.join(os.path.dirname(__file__), "table.kv"))


class Table(GridLayout):

    def build(self):
        return widget

    def get_local_str(self, key):
        return get_local_str_util(key)

    def load_session_results(self, session_timeline=None):

        output_dir = self.__get_session_directory()
        if session_timeline is None:
            timeline_path = None
            for fl in os.listdir(output_dir):
                if "-timeline.json" in fl:
                    timeline_path = fl
                    break

            if timeline_path is not None:
                timeline_path = os.path.join(output_dir, timeline_path)
                with open(timeline_path, "r") as fp:
                    session_timeline = json.load(fp)
            else:
                return

        if session_timeline is None:
            return

        range_of_values = 10
        self.__create_pagination_panel(range_of_values, session_timeline)
        self.__load_main_view_rows(session_timeline, 0, range_of_values)

    def __create_pagination_panel(self, range_of_values, st):
        pagination_buttons_count = math.ceil(len(st.keys()) /
                                             (range_of_values * 1.0))
        print("[INFO] pagination count {} ".format(pagination_buttons_count))

        self.ids["pagination_zone"].clear_widgets()

        for i in range(pagination_buttons_count):
            button = Button(text=str(i),
                            size_hint=(None, None), width='40dp', height='25dp',
                            padding=(5, 5),
                            halign='center', font_size=13)

            if i == 0:
                button.state = 'down'

            button_callback = lambda btn: self.__load_main_view_rows(st,
                                                                     start_index=i * range_of_values,
                                                                     max_elements=range_of_values, btn=btn)

            button.bind(on_release=button_callback)
            self.ids["pagination_zone"].add_widget(button)

    def __load_main_view_rows(self, st, start_index=0, max_elements=10, btn=None):
        k = -1
        self.ids["view_stage"].bind(minimum_height=self.ids["view_stage"].setter('height'))
        if btn is not None:
            btn.state = 'down'
            # find the current active button and deactivate it
            # self.ids["pagination_zone"].children
            # self.active_page
            start_index = int(btn.text) * max_elements
        rows = GridLayout(cols=1)
        self.ids["view_stage"].clear_widgets()

        for key, record in st.items():
            k += 1
            if k < start_index:
                continue

            if k > max_elements + start_index:
                break

            gaze = "-"
            cam = "-"
            vid = "-"
            if record["gaze"] is not None:
                gaze = "({:.4}, {:.4}) ".format(record["gaze"].get("x", "-"), record["gaze"].get("y", "-"))
            if record["camera"] is not None:
                cam = record["camera"].get("frame_id", "-")
            if record["video"] is not None:
                vid = record["video"].get("frame_id", "-")

            row = GridLayout(size_hint_y=None, height=50, cols=4)
            l_ts = Label(text="{}".format(key), font_size='12sp', color=(0, 0, 0, 1))
            row.add_widget(l_ts)

            l_gz = Label(text=gaze, font_size='12sp', color=(0, 0, 0, 1))
            row.add_widget(l_gz)

            l_cam = Label(text=str(cam), font_size='12sp', color=(0, 0, 0, 1))
            row.add_widget(l_cam)

            l_v = Label(text=str(vid), font_size='12sp', color=(0, 0, 0, 1))
            row.add_widget(l_v)

            rows.add_widget(row)

        self.ids["view_stage"].add_widget(rows)
