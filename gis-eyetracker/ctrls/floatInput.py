from kivy.uix.textinput import TextInput
import re


class FloatInput(TextInput):
    pat = re.compile('[^0-9]')
    max_val = None
    
    def set_max_value(self, v):
        self.max_val = v

    def insert_text(self, substring, from_undo=False):
        pat = self.pat
        if '.' in self.text:
            s = re.sub(pat, '', substring)
        else:
            s = '.'.join([re.sub(pat, '', s) for s in substring.split('.', 1)])
        
        if self.max_val is not None:
            s = str(min(float(s), self.max_val))

        return super(FloatInput, self).insert_text(s, from_undo=from_undo)
