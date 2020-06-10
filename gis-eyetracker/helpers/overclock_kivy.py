
from kivy.app import App
from kivy.lang import Builder
from kivy.factory import Factory
from kivy.clock import Clock
from kivy import properties as P
from kivy.config import Config

Config.set('graphics', 'maxfps', 100)

KV = '''
#:import Clock kivy.clock.Clock

BoxLayout:
    orientation: 'vertical'
    Label:
        text: str(app.counter)
    Label:
        text: str(app.age)
    Label:
        text: str((app.counter / max(app.age, 1), Clock.get_fps()))
'''

class Application(App):
    counter = P.NumericProperty()
    age = P.NumericProperty()

    def build(self):
        Clock.schedule_interval(self.update_counter, 0)
        return Builder.load_string(KV)

    def update_counter(self, dt):
        self.counter += 1
        self.age += dt


if __name__ == "__main__":
    Application().run()