from kivy.uix.dropdown import DropDown
from kivy.uix.button import Button
from helpers import get_local_str_util


def select_box_inline(label, options):
    dropdown = DropDown()
    for text, cb in options:
        btn = Button(text=text, size_hint_y=None, height=30)

        # for each button, attach a callback that will call the select() method
        # on the dropdown. We'll pass the text of the button as the data of the
        # selection.
        btn.bind(on_release=lambda bt: btn_release_cb(dropdown, bt, cb))

        dropdown.add_widget(btn)

        # create a big main button
    main_button = Button(text=label, size_hint=(None, None), height=30)
    main_button.bind(on_release=dropdown.open)

    dropdown.bind(on_select=lambda instance, x: setattr(main_button, 'text', x))

    return main_button

def btn_release_cb(dropdown, btn, cb):
    dropdown.select(btn.text)
    cb()


class SelectBox(Button):
    options = []

    @staticmethod
    def btn_release_cb(dropdown, btn, cb):
        dropdown.select(btn.text)
        cb()

    def set_options(self, options):
        self.options = options
        dropdown = DropDown()
        for text, cb in self.options:
            btn = Button(text=text, size_hint_y=None, height=30)

            # for each button, attach a callback that will call the select() method
            # on the dropdown. We'll pass the text of the button as the data of the
            # selection.
            btn.bind(on_release=lambda bt: self.btn_release_cb(dropdown, bt, cb))

            dropdown.add_widget(btn)

        self.bind(on_release=dropdown.open)

        dropdown.bind(on_select=lambda instance, x: setattr(self, 'text', x))

    def build(self):
        self.set_options(self.options)

