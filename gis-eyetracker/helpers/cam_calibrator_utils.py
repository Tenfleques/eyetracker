import time
import cv2 

import numpy as np
import os
import sys
import shutil
import glob
import itertools
import sys
import shutil
import glob
import itertools
import copy

import platform
if platform.system() == 'Linux':
    import pyscreenshot as ImageGrab
else:
    from PIL import ImageGrab

from helpers import get_app_dir, file_log, get_local_str_util

APP_PATH = get_app_dir()

def ui_log(text="", level=0):
    print(text)

class Calibrator:
    

    def __init__(self, img_format = 'png', CHECKERBOARD = (6,9), verbose = False, ui_log_user=ui_log, calibration_folder = os.path.join(APP_PATH, "user", "configs", "camera"), subpix_criteria = (cv2.TERM_CRITERIA_EPS+cv2.TERM_CRITERIA_MAX_ITER, 100, 1e-7), \
                    calibration_flags = cv2.fisheye.CALIB_RECOMPUTE_EXTRINSIC+cv2.fisheye.CALIB_CHECK_COND+cv2.fisheye.CALIB_FIX_SKEW ):
        self.ui_log = ui_log_user
        self.img_format = img_format
        self.CHECKERBOARD = CHECKERBOARD # size of Chess board
        self.verbose = verbose # algorithm Versatility
        self.subpix_criteria = subpix_criteria
        self.calibration_flags = calibration_flags

        objp = np.zeros((1, self.CHECKERBOARD[0]*self.CHECKERBOARD[1], 3), np.float32)
        objp[0,:,:2] = np.mgrid[0:self.CHECKERBOARD[0], 0:self.CHECKERBOARD[1]].T.reshape(-1, 2)
        self.objp = objp

        if calibration_folder[-1] != '/':
            self.calibration_folder = calibration_folder+'/'
        else:
            self.calibration_folder = calibration_folder # Directory where all transformation matrices are stored. By default, the location is next to the module.

    #################################################################################################################################################

    def reset_calibration(self, camera_index=0):
        interesting_folder = os.path.join(self.calibration_folder, "data_calib_camera_"+str(camera_index))
        try:
            shutil.rmtree(interesting_folder)
        except OSError : 
            ...

    #################################################################################################################################################

    def control_photo(self, img_):

        img = copy.deepcopy(img_)
        objpoints = [] # 3d point in real world space
        imgpoints = [] # 2d points in image plane.

        gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)

        # Find the chess board corners
        ret, corners = cv2.findChessboardCorners(gray, self.CHECKERBOARD, cv2.CALIB_CB_ADAPTIVE_THRESH+cv2.CALIB_CB_FAST_CHECK+cv2.CALIB_CB_NORMALIZE_IMAGE)

        # If found, add object points, image points (after refining them)
        if ret == True:
            objpoints.append(self.objp)
            cv2.cornerSubPix(gray, corners, (3,3), (-1,-1), self.subpix_criteria)
            imgpoints.append(corners)
        else:
            file_log("BAD IMAGE: The chessboard is not visible in the photo! Please take the other photo.")
            CHESSBOARD_NOT_VISIBLE = get_local_str_util("_the_chessboard_is_not_visible_in_the_photo_please_take_the_other_photo")
            self.ui_log(text=CHESSBOARD_NOT_VISIBLE, level=1)
            
            #<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
            return False

        K = np.zeros((3, 3))
        D = np.zeros((4, 1))
        rvecs = [np.zeros((1, 1, 3), dtype=np.float64)]
        tvecs = [np.zeros((1, 1, 3), dtype=np.float64)]

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
                    self.calibration_flags,
                    self.subpix_criteria#(cv2.TERM_CRITERIA_EPS+cv2.TERM_CRITERIA_MAX_ITER, 30, 1e-6)
                )

            file_log("The image passed the initial selection.")
            INITIAL_SELECTION = get_local_str_util("_The_image_passed_the_initial selection")
            self.ui_log(text=INITIAL_SELECTION, level=0)
             # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
            return True

        except cv2.error:
            file_log("BAD IMAGE: The chessboard is not visible in the photo! Please take the other photo.")
            CHESSBOARD_NOT_VISIBLE = get_local_str_util("_BAD_IMAGE_The_chessboard_is_not_visible_in_the_photo_Please_take_the_other_photo.")
            self.ui_log(text=CHESSBOARD_NOT_VISIBLE, level=1)
            # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<    
            return False    

    #################################################################################################################################################

    def data_calib_saver(self, img, camera_index = 0):
        interesting_folder = os.path.join(self.calibration_folder, "data_calib_camera_"+str(camera_index))+'/'
        CONTROL_PHOTOS = self.control_photo(img)

        if not os.path.isdir(interesting_folder) and CONTROL_PHOTOS:
            file_log("No data for this camera! I create an empty template!")
            NO_DATA_FOR_CAMERA = get_local_str_util("_No_data_for_this_camera_I_create_an_empty_template")
            self.ui_log(text=NO_DATA_FOR_CAMERA, level=1)
             # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
            os.mkdir(interesting_folder)
            #np.save(interesting_folder+'K', np.zeros((3, 3)))
            #np.save(interesting_folder+'D', np.zeros((4, 1)))

        if CONTROL_PHOTOS:
            timestr = time.strftime("%Y%m%d_%H%M%S")
            cv2.imwrite(interesting_folder+"IMG_{0}.{1}".format(timestr, self.img_format), img)
            return True

        return False

    #################################################################################################################################################

    def fit_calibrator(self, img, camera_index = 0):
        '''
        A function that uses photos from a stream to build a transformation matrix.
        '''

        if not self.data_calib_saver(img, camera_index = camera_index): # It is expected that if it worked, then the photo was saved.
            return

        interesting_folder = os.path.join(self.calibration_folder, "data_calib_camera_"+str(camera_index))+'/'

        _img_shape = None
        objpoints = [] # 3d point in real world space
        imgpoints = [] # 2d points in image plane.

        file_log(interesting_folder+'*.'+self.img_format)
        images = glob.glob(interesting_folder+'*.'+self.img_format)

        for fname in images:
            file_log(fname)
            img = cv2.imread(fname)

            if _img_shape == None:
                _img_shape = img.shape[:2]
            else:
                assert _img_shape == img.shape[:2], "All images must share the same size."

            gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
            ret, corners = cv2.findChessboardCorners(gray, self.CHECKERBOARD, cv2.CALIB_CB_ADAPTIVE_THRESH+cv2.CALIB_CB_FAST_CHECK+cv2.CALIB_CB_NORMALIZE_IMAGE)
            
            if ret == True:
                objpoints.append(self.objp)
                cv2.cornerSubPix(gray,corners,(3,3),(-1,-1),self.subpix_criteria)
                imgpoints.append(corners)

        N_OK = len(objpoints)
        K = np.zeros((3, 3))
        D = np.zeros((4, 1))
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
                    self.calibration_flags,
                    self.subpix_criteria#(cv2.TERM_CRITERIA_EPS+cv2.TERM_CRITERIA_MAX_ITER, 30, 1e-6)
                )

            file_log("SUCCESS: New conversion matrix counted successfully.")
            SUCCESS_COUNT_MATRIX = get_local_str_util("_SUCCESS_New_conversion_matrix_counted_successfully")
            self.ui_log(text=SUCCESS_COUNT_MATRIX, level=0)
            #<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

            np.save(interesting_folder+'K', K)
            np.save(interesting_folder+'D', D)

            file_log("SUCCESS: New conversion matrix saved successfully.")
            SUCCESS_SAVE_MATRIX = get_local_str_util("_SUCCESS_New_conversion_matrix_saved_successfully")
            self.ui_log(SUCCESS_SAVE_MATRIX)
            #<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

        except cv2.error:
            file_log("Something wrong. Please try to reset the calibration and repeat all the steps again.")
            SOMETHING_WRONG = get_local_str_util("_Something_is_wrong_please_try_to_reset_the_calibration_and_repeat_all_the_steps_again")
            self.ui_log(text=SOMETHING_WRONG, level=1)
            #<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<


    def transform_img_from_stream(self, img, camera_index = 0, balance=0.0, dim2=None, dim3=None):
        '''
        A function that converts photos taken from a camera stream based on an existing matrix.
        '''

        interesting_folder = os.path.join(self.calibration_folder, "data_calib_camera_"+str(camera_index))+'/'
        
        if ("data_calib_camera_"+str(camera_index) not in os.listdir(self.calibration_folder)) or (('K.npy' not in os.listdir(interesting_folder)) or ('D.npy' not in os.listdir(interesting_folder))):
            CAMERA_NOT_CALIB = get_local_str_util("_This_camera_was_not_calibrated")
            self.ui_log(text=CAMERA_NOT_CALIB, level=1)
            #<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
            file_log("This camera was not calibrated!")
            
            new_img = img
            
        else:
            K = np.load(interesting_folder+'K.npy')
            D = np.load(interesting_folder+'D.npy')
            
            dim1 = img.shape[:2][::-1]  #dim1 is the dimension of input image to un-distort


            if not dim2:
                dim2 = dim1
            if not dim3:
                dim3 = dim1

            K[2][2] = 1.0  # Except that K[2][2] is always 1.0

            # This is how scaled_K, dim2 and balance are used to determine the final K used to un-distort image. OpenCV document failed to make this clear!
            new_K = cv2.fisheye.estimateNewCameraMatrixForUndistortRectify(K, D, dim2, np.eye(3), balance=balance)
            file_log("K = ", K, "new_K = ", new_K)
            map1, map2 = cv2.fisheye.initUndistortRectifyMap(K, D, np.eye(3), new_K, dim3, cv2.CV_16SC2)
            new_img = cv2.remap(img, map1, map2, interpolation=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)

            timestr = time.strftime("%Y%m%d_%H%M%S")
            cv2.imwrite("IMG_TRANSFORM_{0}.{1}".format(timestr, self.img_format), new_img)
            
        return new_img
