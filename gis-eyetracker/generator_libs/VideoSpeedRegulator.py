from kivy.app import App
from kivy.uix.widget import Widget
from kivy.graphics import Color, Ellipse, Line, Rectangle
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.button import Button



class MyPaintWidget(AnchorLayout):
    Coordinates = {}
    NewCoordinates = {}
    
    fixpoints = []
    
    lastX = 0    
    points = 500
    d =3
    lenX = 800
    keylist = []
    offset = 10
    def Loc2Glob(self,coord):
        x = coord[0]+self.pos[0]
        y = coord[1]+self.pos[1]
        return(x,y)
    
    def IsTouchInside(self,t):
        print(self.pos)
        print(self.pos)
        print(t.x, t.y)
        if t.x>(self.pos[0]+self.size[0]): 
            return False
        if t.x<(self.pos[0]):
            return False
        if t.y>(self.pos[1]+self.size[1]):
            return False
        if t.y<(self.pos[1]):
            return False
        
        return True
    

    def __init__(self, **kwargs):
        super(MyPaintWidget, self).__init__(**kwargs)
        print('Painter:',self.pos, self.size)

    def reinit(self):
        self.Coordinates = {}
        dx = (self.size[0]-self.offset)/self.points
        for i in range(self.points):
               coord = (self.offset+i*dx, self.size[1]/2)
               coord2 = self.Loc2Glob(coord)
               self.Coordinates[coord2[0]]=coord2[1]
               self.fixpoints.append(coord2[0])
                
    def redraw(self):
        
        with self.canvas:
            Color(0, 0, 0)
            Rectangle(pos = self.pos, size = self.size)
            Color(1, 1, 0)
            
            for k in self.Coordinates.keys():
                coord2 = (k, self.Coordinates[k])
                Ellipse(pos=(coord2[0] - self.d / 2, coord2[1] - self.d / 2), size=(self.d, self.d))
                
    
    def on_touch_down(self, touch):
        if not self.IsTouchInside(touch):
            return
        self.NewCoordinates = {}
        self.lastX = touch.x
        print(self.pos, self.size)
        
    def on_touch_move(self, touch):
        if not self.IsTouchInside(touch):
            print('not inside')
            return
        
        self.NewCoordinates[touch.x] = touch.y
        with self.canvas:
            Color(1, 1, 0)
            Ellipse(pos=(touch.x - self.d / 2, touch.y - self.d / 2), size=(self.d, self.d))
            for k in self.Coordinates.keys():
                Color(0, 0, 0)
                if (k<touch.x)and(k>self.lastX):
                    #print('itis')
                    Ellipse(pos=(k - self.d / 2, self.Coordinates[k] - self.d / 2), size=(self.d, self.d))
                    
            Color(1, 1, 0)
            if self.keylist != []:
                if (self.keylist[-1]!=touch.x)and(self.keylist[-1]<touch.x):
                    Ellipse(pos=(touch.x - self.d / 2, touch.y - self.d / 2), size=(self.d, self.d))
                    self.keylist.append(touch.x)
            else:
                Ellipse(pos=(touch.x - self.d / 2, touch.y - self.d / 2), size=(self.d, self.d))
                self.keylist.append(touch.x)
             
        

    def on_touch_up(self, touch):
        if not self.IsTouchInside(touch):
            return
        
        with self.canvas:
            d = 6
            
            for i in range(1,len(self.keylist)):
                x1 = self.keylist[i-1]
                x2 = self.keylist[i]
                
                y1 = self.NewCoordinates[x1]
                y2 = self.NewCoordinates[x2]
                
                Color(0, 0, 0)
                Ellipse(pos=(x1 - d / 2, y1 - d / 2), size=(d, d))
                Ellipse(pos=(x2 - d / 2, y2 - d / 2), size=(d, d))
            
            d = 5
            for i in range(1,len(self.keylist)):
                x1 = self.keylist[i-1]
                x2 = self.keylist[i]
                
                y1 = self.NewCoordinates[x1]
                y2 = self.NewCoordinates[x2]
                
                Color(0, 0, 0)
                print('up')
                K = (y2-y1)/(x2-x1)
                
                Color(1, 1, 0)
                for k in self.Coordinates.keys():
                    if (x1<=k)and(k<=x2):
                        y_new = (k-x1)*K+y1
                        self.Coordinates[k] = y_new
                        coord2 = (k, y_new)
                        Ellipse(pos=(coord2[0] - self.d / 2, coord2[1] - self.d / 2), size=(self.d, self.d))
                
            
        self.keylist = []
        self.NewCoordinates = {}
        
    def get_speed_vector(self, min_speed, max_speed):
        start = min(self.fixpoints)
        end = max(self.fixpoints)
        
        low = self.pos[1]
        high = self.pos[1]+self.size[1]
        
        dspeed = max_speed-min_speed
        
        
        speed_list = []
        
        for i in range(1,len(self.fixpoints)):
            k = self.fixpoints[i]
            val = self.Coordinates[k]
            
            k = 1-(end-k)/(end-start)
            
            #print(((high-val)/(high-low)), min_speed, max_speed, dspeed)
            val = min_speed + (1-(high-val)/(high-low))*dspeed
            print(k,val)
            speed_list.append((k,val))
            
        return speed_list

class MyPaintApp(App):

    def build(self):
        return MyPaintWidget()


if __name__ == '__main__':
    MyPaintApp().run()