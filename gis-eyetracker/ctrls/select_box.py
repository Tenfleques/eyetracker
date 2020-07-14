from kivy.uix.dropdown import DropDown
from kivy.uix.button import Button
from helpers import get_local_str_util, file_log


class SelectBox(Button):
    options = []

    @staticmethod
    def btn_release_cb(dropdown, btn, cb):
        dropdown.select(btn.text)
        dropdown.dismiss()
        try:
            cb()
        except Exception as err:
            file_log("[ERROR] callback after selecting {}", err)
        return 
    
    def this_btn_on_release(self, ctrl, dropdown):
        dropdown.open(ctrl)
        

    def set_options(self, options):
        self.options = options
        dropdown = DropDown()
        bg = [(.7,.7,.7,1), (.65,.65,.65,1)]
        k = 0
        for text, cb in self.options:
            btn = Button(text=text, size_hint_y=None, height=30, background_normal='', background_color = bg[k%2], color =(0,0,0,1))
            k += 1
            # for each button, attach a callback that will call the select() method
            # on the dropdown. We'll pass the text of the button as the data of the
            # selection.
            btn.bind(on_release=lambda bt: self.btn_release_cb(dropdown, bt, cb))

            dropdown.add_widget(btn)

        self.bind(on_release=lambda ctrl: self.this_btn_on_release(ctrl, dropdown))

        dropdown.bind(on_select=lambda instance, x: setattr(self, 'text', x))

    def build(self):
        self.set_options(self.options)

