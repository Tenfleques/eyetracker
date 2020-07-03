from kivy.app import App
from kivy.lang import Builder
from kivy.uix.camera import Camera
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock

from kivy.graphics.texture import Texture
from kivy.properties import ObjectProperty

import time
import cv2 

import numpy as np
import os
import glob
import itertools


#==========================================
###########################################

class Calibrator:
    def __init__(self, img_format = 'jpg', CHECKERBOARD = (6,9), verbose = False, main_folder = './' ):
        self.img_format = img_format
        self.CHECKERBOARD = CHECKERBOARD # size of Chess board
        self.verbose = verbose # algorithm Versatility
        self.main_folder = main_folder # Directory where all transformation matrices are stored. By default, the location is next to the module.
        
    #####################################################
        
    def fit_calibrator_from_folder(self, path_dir):
        '''
		A function that uses photos from a directory to build a transformation matrix.
    	'''
        subpix_criteria = (cv2.TERM_CRITERIA_EPS+cv2.TERM_CRITERIA_MAX_ITER, 30, 0.1)
        calibration_flags = cv2.fisheye.CALIB_RECOMPUTE_EXTRINSIC+cv2.fisheye.CALIB_CHECK_COND+cv2.fisheye.CALIB_FIX_SKEW

        objp = np.zeros((1, self.CHECKERBOARD[0]*self.CHECKERBOARD[1], 3), np.float32)
        objp[0,:,:2] = np.mgrid[0:self.CHECKERBOARD[0], 0:self.CHECKERBOARD[1]].T.reshape(-1, 2)

        _img_shape = None
        objpoints = [] # 3d point in real world space
        imgpoints = [] # 2d points in image plane.
        print("imgs path: "+path_dir+'*.'+self.img_format)
        images = glob.glob(path_dir+'*.'+self.img_format)

        for fname in images:
            print(fname)
            img = cv2.imread(fname)
            if _img_shape == None:
                _img_shape = img.shape[:2]
            else:
                assert _img_shape == img.shape[:2], "All images must share the same size."
            gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
            # Find the chess board corners
            ret, corners = cv2.findChessboardCorners(gray, self.CHECKERBOARD, cv2.CALIB_CB_ADAPTIVE_THRESH+cv2.CALIB_CB_FAST_CHECK+cv2.CALIB_CB_NORMALIZE_IMAGE)
            # If found, add object points, image points (after refining them)
            if ret == True:
                objpoints.append(objp)
                cv2.cornerSubPix(gray,corners,(3,3),(-1,-1),subpix_criteria)
                imgpoints.append(corners)
                
            #------------------------------------------------
            if (ret == True) and (self.verbose == True):
                # Draw and display the corners
                corners2 = cv2.cornerSubPix(gray,corners,(11,11),(-1,-1),subpix_criteria)
                img = cv2.drawChessboardCorners(img, (7,6), corners2,ret)
                
                h, w = img.shape[0:2]
                neww = 800
                newh = int(neww*(h/w))
                img = cv2.resize(img, (neww, newh))
                
                cv2.imshow(str(fname),img)
                cv2.waitKey(0)
                cv2.destroyAllWindows()
                
            #------------------------------------------------

        N_OK = len(objpoints)
        K = np.zeros((3, 3))
        D = np.zeros((4, 1))
        rvecs = [np.zeros((1, 1, 3), dtype=np.float64) for i in range(N_OK)]
        tvecs = [np.zeros((1, 1, 3), dtype=np.float64) for i in range(N_OK)]
        rms, _, _, _, _ = \
            cv2.fisheye.calibrate(
                objpoints,
                imgpoints,
                gray.shape[::-1],
                K,
                D,
                rvecs,
                tvecs,
                calibration_flags,
                (cv2.TERM_CRITERIA_EPS+cv2.TERM_CRITERIA_MAX_ITER, 30, 1e-6)
            )

        print("Found " + str(N_OK) + " valid images for calibration")
        print("DIM=" + str(_img_shape[::-1]))
        print("K=np.array(" + str(K.tolist()) + ")")
        print("D=np.array(" + str(D.tolist()) + ")")
        
        self.K = K
        self.D = D
        self.DIM = _img_shape[::-1]
        
    #####################################################

    def fit_calibrator_from_stream(self, img_, camera_index = 0, new_calibration = False):
        '''
		A function that uses photos from a stream to build a transformation matrix.
    	'''

        subpix_criteria = (cv2.TERM_CRITERIA_EPS+cv2.TERM_CRITERIA_MAX_ITER, 30, 0.1)
        calibration_flags = cv2.fisheye.CALIB_RECOMPUTE_EXTRINSIC+cv2.fisheye.CALIB_CHECK_COND+cv2.fisheye.CALIB_FIX_SKEW

        objp = np.zeros((1, self.CHECKERBOARD[0]*self.CHECKERBOARD[1], 3), np.float32)
        objp[0,:,:2] = np.mgrid[0:self.CHECKERBOARD[0], 0:self.CHECKERBOARD[1]].T.reshape(-1, 2)

        _img_shape = None
        objpoints = [] # 3d point in real world space
        imgpoints = [] # 2d points in image plane.

        img = img_
        
        if _img_shape == None:
            _img_shape = img.shape[:2]
        else:
            assert _img_shape == img.shape[:2], "All images must share the same size."
        gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
        # Find the chess board corners
        ret, corners = cv2.findChessboardCorners(gray, self.CHECKERBOARD, cv2.CALIB_CB_ADAPTIVE_THRESH+cv2.CALIB_CB_FAST_CHECK+cv2.CALIB_CB_NORMALIZE_IMAGE)
        # If found, add object points, image points (after refining them)
        if ret == True:
            objpoints.append(objp)
            cv2.cornerSubPix(gray,corners,(3,3),(-1,-1),subpix_criteria)
            imgpoints.append(corners)
            
        #------------------------------------------------
        if (ret == True) and (self.verbose == True):
            # Draw and display the corners
            corners2 = cv2.cornerSubPix(gray,corners,(11,11),(-1,-1),subpix_criteria)
            img = cv2.drawChessboardCorners(img, (7,6), corners2,ret)
            
            h, w = img.shape[0:2]
            neww = 800
            newh = int(neww*(h/w))
            img = cv2.resize(img, (neww, newh))
            
            cv2.imshow(str(img),img)
            cv2.waitKey(0)
            cv2.destroyAllWindows()
            
        #------------------------------------------------

        N_OK = len(objpoints)
        
        #print(os.listdir(self.main_folder))
        if (new_calibration == True) or (str(camera_index)+'K.npy' not in os.listdir(self.main_folder)) or (str(camera_index)+'D.npy' not in os.listdir(self.main_folder)):
            K = np.zeros((3, 3))
            D = np.zeros((4, 1))
        else:
            K = np.load(self.main_folder+str(camera_index)+'K.npy')
            D = np.load(self.main_folder+str(camera_index)+'D.npy')
            
        #print(K)

        rvecs = [np.zeros((1, 1, 3), dtype=np.float64) for i in range(N_OK)]
        tvecs = [np.zeros((1, 1, 3), dtype=np.float64) for i in range(N_OK)]
        try:
            rms, _, _, _, _ = \
                cv2.fisheye.calibrate(
                    objpoints,
                    imgpoints,
                    gray.shape[::-1],
                    K,
                    D,
                    rvecs,
                    tvecs,
                    calibration_flags,
                    (cv2.TERM_CRITERIA_EPS+cv2.TERM_CRITERIA_MAX_ITER, 30, 1e-6)
                )

            print("DIM=" + str(_img_shape[::-1]))
            print("K=np.array(" + str(K.tolist()) + ")")
            print("D=np.array(" + str(D.tolist()) + ")")

            print(self.main_folder+str(camera_index)+'K')
            np.save(self.main_folder+str(camera_index)+'K', K)
            np.save(self.main_folder+str(camera_index)+'D', D)

        except cv2.error:
            print("BAD IMAGE! Please take the other photo.")

        
    #####################################################

        
    def transform_img_from_folder(self, path_dir, camera_index = 0, balance=0.0, dim2=None, dim3=None):
        '''
        A function that converts photos taken from a directory based on an existing matrix.
        '''

        images = glob.glob(path_dir+'*.'+self.img_format)
        
        imgs = {}
        k=0
        
        #--------------
        
        if (str(camera_index)+'K.npy' not in os.listdir(self.main_folder)) or (str(camera_index)+'D.npy' not in os.listdir(self.main_folder)):
            print("This camera did not calibrate!")
            new_img = img
            
        else:
            K = np.load(self.main_folder+str(camera_index)+'K.npy')
            D = np.load(self.main_folder+str(camera_index)+'D.npy')
            
        #--------------
        
        for img_ in images:
            
            img = cv2.imread(img_)
            dim1 = img.shape[:2][::-1]  #dim1 is the dimension of input image to un-distort

            if not dim2:
                dim2 = dim1
            if not dim3:
                dim3 = dim1

            scaled_K = K
            scaled_K[2][2] = 1.0  # Except that K[2][2] is always 1.0

            # This is how scaled_K, dim2 and balance are used to determine the final K used to un-distort image. OpenCV document failed to make this clear!
            new_K = cv2.fisheye.estimateNewCameraMatrixForUndistortRectify(scaled_K, D, dim2, np.eye(3), balance=balance)
            map1, map2 = cv2.fisheye.initUndistortRectifyMap(scaled_K, D, np.eye(3), new_K, dim3, cv2.CV_16SC2)
            undistorted_img = cv2.remap(img, map1, map2, interpolation=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
            
            imgs[k] = undistorted_img
            k+=1
            
        return imgs
    
    ####################################################
    
    def transform_img_from_stream(self, img, camera_index = 0, balance=0.0, dim2=None, dim3=None):
        '''
    	A function that converts photos taken from a camera stream based on an existing matrix.
    	'''
        
        if (str(camera_index)+'K.npy' not in os.listdir(self.main_folder)) or (str(camera_index)+'D.npy' not in os.listdir(self.main_folder)):
            print("This camera did not calibrate!")
            new_img = img
            
        else:
            K = np.load(self.main_folder+str(camera_index)+'K.npy')
            D = np.load(self.main_folder+str(camera_index)+'D.npy')
            
            dim1 = img.shape[:2][::-1]  #dim1 is the dimension of input image to un-distort


            if not dim2:
                dim2 = dim1
            if not dim3:
                dim3 = dim1

            K[2][2] = 1.0  # Except that K[2][2] is always 1.0

            # This is how scaled_K, dim2 and balance are used to determine the final K used to un-distort image. OpenCV document failed to make this clear!
            new_K = cv2.fisheye.estimateNewCameraMatrixForUndistortRectify(K, D, dim2, np.eye(3), balance=balance)
            map1, map2 = cv2.fisheye.initUndistortRectifyMap(K, D, np.eye(3), new_K, dim3, cv2.CV_16SC2)
            new_img = cv2.remap(img, map1, map2, interpolation=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
            
            
        return new_img

###########################################
#==========================================

Builder.load_string('''
<MultipleCameras>:
    orientation: 'horizontal'
<CameraClick>:
    orientation: 'vertical'
    index: 0
    Image:
        id: camera
        size_hint_y: 1
    ToggleButton:
        text: 'Play'
        on_press: root.is_playing = not root.is_playing
        size_hint_y: None
        height: '48dp'
    Button:
        text: 'Capture'
        size_hint_y: None
        height: '48dp'
        on_press: root.capture()
''')

#============================================

class CameraClick(BoxLayout):
    is_playing = False
    video_cap = None
    video_interval = None
    index = ObjectProperty(None)

    def build(self):
        pass

    def on_stop(self):
        self.stop_interval()

    def start_interval(self):
        self.video_cap = cv2.VideoCapture(self.index)
        fps = self.video_cap.get(cv2.CAP_PROP_FPS)
        interval = max(fps, 5)/1000
        self.update_image(None)
        self.video_interval = Clock.schedule_interval(self.update_image, interval)

    def stop_interval(self):
        if self.video_interval is not None:
            self.video_interval.cancel()
        
        if self.video_cap is not None:
            self.video_cap.release()

    def update_image(self, dt):
        if not self.is_playing:
            return 0

        if self.video_cap is None:
            self.stop_interval()
            return 0
        
        ret, frame = self.video_cap.read()
        if not ret:
            self.stop_interval()
            return 0

        frame = cv2.flip(frame, 0)

        buf = frame.tostring()
        texture = Texture.create(size=(frame.shape[1], frame.shape[0]), colorfmt='bgr')
        texture.blit_buffer(buf, colorfmt='bgr', bufferfmt='ubyte')

        self.ids['camera'].texture = texture

    #---------------------------------------------------------------------------

    def capture(self):
        '''
    	Take a photo when you push "capture"
    	'''

        CAL = Calibrator()
        
        camera = self.ids['camera']

        nparr = np.fromstring(self.ids['camera'].texture.pixels, dtype=np.uint8)
        a = np.reshape(nparr, (480,640,4))

        CAL.fit_calibrator_from_stream(a, camera_index = self.index)
        
        #delete this block if you do not need saved photos-->
        timestr = time.strftime("%Y%m%d_%H%M%S")
        camera.export_to_png("IMG_{0}_ind_camera_{1}.png".format(timestr, self.index))
        ##################################################-->

        print("Captured")

#=================================================================================

def discover_cameras():

    for i in itertools.count(start=0):
        try:
            cammm = Camera(play=False, resolution=(640, 480), index = i)
        except AttributeError:
            nums_ind = [j for j in range(i)]
            break

    return nums_ind

class MultipleCameras(BoxLayout):

    def start_all(self):
        ids = discover_cameras()

        for cam_index in ids:
            
            widget = CameraClick(index=cam_index)
            widget.start_interval()
            self.add_widget(widget)


class TestCamera(App):
    def build(self):
        mcs = MultipleCameras()
        mcs.start_all()
        return mcs
