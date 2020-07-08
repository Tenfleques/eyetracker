import time
import cv2 

import numpy as np
import os
import glob
import itertools

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
            
        print(K)

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
