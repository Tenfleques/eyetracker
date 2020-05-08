from ctypes import cdll, c_float, c_bool, c_double, c_int, c_int64, Structure, POINTER
import time

class Point2D(Structure): 
    _fields_ = [('x', c_float), ('y', c_float)]
    @classmethod
    def from_param(cls, self):
        if not isinstance(self, cls):
            raise TypeError
        return self

class Gaze(Point2D):
    _fields_ = [('valid', c_bool), ('timestamp',c_double), ('timestamp_us', c_int64)]
    @classmethod
    def from_param(cls, self):
        if not isinstance(self, cls):
            raise TypeError
        return self
    

class Point3D(Point2D):
    _fields_ = [('z', c_float)]
    @classmethod
    def from_param(cls, self):
        if not isinstance(self, cls):
            raise TypeError
        return self

class Eyes(Structure):
    _fields_ = [('left', Point3D), ('right', Point3D), ('v_l', c_bool), ('v_r', c_bool)]
    @classmethod
    def from_param(cls, self):
        if not isinstance(self, cls):
            raise TypeError
        return self

class Pos3D(Eyes):
    _fields_ = [('timestamp',c_double), ('timestamp_us', c_int64)]
    @classmethod
    def from_param(cls, self):
        if not isinstance(self, cls):
            raise TypeError
        return self



class SessionRecord(Structure):
    _fields_ = [('gazes', POINTER(Gaze)),
        ('origins', POINTER(Pos3D)),
        ('record_tracker', c_bool),
        ('poses', POINTER(Pos3D))]
    
    def toString(self):
        pass


if __name__ == "__main__":
    tobii_dll_path = "./TobiiEyeLib.dll"
    lib = cdll.LoadLibrary(tobii_dll_path)

    lib.start.restype = c_int
    lib.get_session.restype = POINTER(SessionRecord)

    lib.start()
    i = 0
    while i < 3:
        time.sleep(1)
        i += 1

    lib.stop()
    output = lib.get_session()
    print()
