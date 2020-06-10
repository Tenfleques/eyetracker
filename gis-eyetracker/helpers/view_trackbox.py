from kivy.app import App
import numpy as np
import matplotlib
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection, Line3DCollection
import matplotlib.pyplot as plt
matplotlib.use("module://kivy.garden.matplotlib.backend_kivy")
from kivy.garden.matplotlib import FigureCanvasKivyAgg

trackbox =  {
        "front": {
            "bottom": {
                "left": {
                    "x": -150.000000,
                    "y": -100.000000,
                    "z": 450.000000
                },
                "right": {
                    "x": 150.000000,
                    "y": -100.000000,
                    "z": 450.000000
                }
            },
            "top": {
                "left": {
                    "x": -150.000000,
                    "y": 100.000000,
                    "z": 450.000000
                },
                "right": {
                    "x": 150.000000,
                    "y": 100.000000,
                    "z": 450.000000
                }
            }
        },
        "back": {
            "bottom": {
                "left": {
                    "x": -275.000000,
                    "y": -200.000000,
                    "z": 900.000000
                },
                "right": {
                    "x": 275.000000,
                    "y": -200.000000,
                    "z": 900.000000
                }
            },
            "top": {
                "left": {
                    "x": -275.000000,
                    "y": 200.000000,
                    "z": 900.000000
                },
                "right": {
                    "x": 275.000000,
                    "y": 200.000000,
                    "z": 900.000000
                }
            }
        }
    }



fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')

get_vertices_array = lambda f,h,s : [trackbox[f][h][s]["x"],
                                     trackbox[f][h][s]["y"],
                                     trackbox[f][h][s]["z"]]
# vertices of the track field
v = np.array([
              get_vertices_array("front", "bottom", "left"),
              get_vertices_array("front", "bottom", "right"),
              get_vertices_array("front", "top", "left"),
              get_vertices_array("front", "top", "right"),
              get_vertices_array("back", "bottom", "right"),
              get_vertices_array("back", "bottom", "left"),
              get_vertices_array("back", "top", "left"),
              get_vertices_array("back", "top", "right")
              ])



ax.scatter3D(v[:, 0], v[:, 1], v[:, 2])
#
# generate list of sides' polygons of the volume
verts = [
             [
                  v[0],
                  v[1],
                  v[3],
                  v[2]
             ],
             [
                  v[6],
                  v[7],
                  v[3],
                  v[2]
              ]
        ]

## plot sides
ax.add_collection3d(Poly3DCollection(verts,
                                     facecolors='cyan', linewidths=1, edgecolors='r', alpha=.25))

ax.set_xlabel('X')
ax.set_ylabel('Y')
ax.set_zlabel('Z')

# plt.show()


class ChartApp(App):

    def build(self):
        self.ids["chart_area"].add_widget(FigureCanvasKivyAgg(plt.gcf()))
        pass

    def on_pause(self):
        return True


if __name__ == '__main__':
    ChartApp().run()
