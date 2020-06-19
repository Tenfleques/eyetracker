from mpl_toolkits import mplot3d
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
import cv2

# from helpers import fig2data, fig2img

def fig2img ( fig ):
    """
    @brief Convert a Matplotlib figure to a PIL Image in RGBA format and return it
    @param fig a matplotlib figure
    @return a Python Imaging Library ( PIL ) image
    """
    # put the figure pixmap into a np array
    buf = fig2data ( fig )
    w, h, d = buf.shape
    return Image.fromstring( "RGBA", ( w ,h ), buf.tostring( ) )


def fig2data ( fig ):
    """
    @brief Convert a Matplotlib figure to a 4D numpy array with RGBA channels and return it
    @param fig a matplotlib figure
    @return a numpy 3D array of RGBA values
    """
    # draw the renderer
    canvas = FigureCanvas(fig)
    canvas.draw()
 
    # Get the RGBA buffer from the figure
    w,h = canvas.get_width_height()
    buf = numpy.frombuffer ( fig.canvas.tostring_argb(), dtype=numpy.uint8 )
    buf.shape = ( w, h, 4 )
 
    # canvas.tostring_argb give pixmap in ARGB mode. Roll the ALPHA channel to have it in RGBA mode
    buf = numpy.roll ( buf, 3, axis = 2 )
    return buf


def props(cls):
    return [i for i in cls.__dict__.keys() if i[:1] != '_']

fig = Figure(figsize=(5, 4), dpi=200)
# fig.add_subplot ( 111 )

fig.add_axes(projection='3d')

canvas = FigureCanvas(fig)
# ax = fig.gca()

# ax.text(0.0,0.0,"Test", fontsize=45)
# ax.axis('off')
# plt.show()

canvas.draw()       # draw the canvas, cache the renderer

image = np.frombuffer(canvas.tostring_rgb(), dtype='uint8')

cv2.imshow("image", image)
key = cv2.waitKey(0)

if key == ord('q'):
    cv2.destroyAllWindows()