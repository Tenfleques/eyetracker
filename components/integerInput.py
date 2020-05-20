from kivy.uix.textinput import TextInput
import re

class IntegerInput(TextInput):
    pat = re.compile('[^0-9]')

    def insert_text(self, substring, from_undo=False):
        pat = self.pat
        s = ''.join([re.sub(pat, '', s) for s in substring.split('.', 1)])
        return super(IntegerInput, self).insert_text(s, from_undo=from_undo)
