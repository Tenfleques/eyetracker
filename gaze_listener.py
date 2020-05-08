import pickle
import logging
import logging.handlers
import socketserver
import struct
import select
import time
from threading import Thread, current_thread
import sys
import socket
from tracker_record import Record

from ctypes import cdll, c_int, POINTER

from collections import deque

QUEUE_SIZE = 10 

def props(cls):   
  return [i for i in cls.__dict__.keys() if i[:1] != '_']

tobii_dll_path = "TobiiEyeLib\\x64\\Debug\\TobiiEyeLib.dll"
tobiiEyeLib = cdll.LoadLibrary(tobii_dll_path)
class TobiiWinGazeWatcher():
    """
        simple API to the gaze watcher on windows platforms
    """
    recent_gazes = deque(QUEUE_SIZE*"", QUEUE_SIZE)
    
    def __init__(self):
        self.tobiiEyeLib = tobiiEyeLib
        self.tobiiEyeLib.stop.restype = c_int
        self.tobiiEyeLib.start.restype = c_int
        self.tobiiEyeLib.getLatest.restype = POINTER(Record)
        self.tobiiEyeLib.start()
        

    def getTopRecords(self):
        return self.recent_gazes

    def server_close(self):
        stopped = self.tobiiEyeLib.stop()
        print("listener stopped", stopped)
        self.play = 0

    def serve_until_stopped(self, stop):
        while not stop():
            try :
                output = self.tobiiEyeLib.getLatest()
                self.recent_gazes.appendleft(output.contents)
                del output
            except OSError as msg:
                print(msg)
                continue
            self.play = not stop()



class WindowsRecordSocketReceiver(socketserver.ThreadingTCPServer):
    """
        simple TCP socket-based logging receiver.
    """
    allow_reuse_address = 1
    timeout = 3
    recent_gazes = deque(QUEUE_SIZE*"", QUEUE_SIZE)
    
    def __init__(self,host = 'localhost',    # The remote host
                      port = 11000):   
        self.s = None
        self.update_thread = None
        self.stop = lambda : False

        for res in socket.getaddrinfo(host, port, socket.AF_UNSPEC, socket.SOCK_STREAM):
            af, socktype, proto, canonname, sa = res
            try:
                self.s = socket.socket(af, socktype, proto)
            except OSError as msg:
                self.s = None
                print(msg)
                continue
            try:
                self.s.connect(sa)
            except OSError as msg:
                self.s.close()
                self.s = None
                continue
            break
     
    def getTopRecords(self):
        return self.recent_gazes

    def server_close(self):
        if self.update_thread:
            self.update_thread._stop()
        self.s.close()
        self.s = None

    def continuousUpdate(self, stop):
        while (not stop()) and self.s:
            data = self.s.recv(1024)
            print(data, " received")
            record = repr(data)
            self.recent_gazes.append(record)
            self.play = not stop()

    def serve_until_stopped(self, stop):
         if self.s is None:
            print('could not open socket')
            return
         self.stop = stop

         with self.s:
            self.s.sendall(b'stream')
            self.update_thread = Thread(self.continuousUpdate)
            self.update_thread.start()


def winEyeGazeListener():
    tcpserver = TobiiWinGazeWatcher()
    print("About to start TCP server...")
    socket_thread_alive = True
    socket_thread = Thread(target=tcpserver.serve_until_stopped, args=(lambda : not socket_thread_alive, ))
    try:
        # Start the thread
        socket_thread.start()
        for i in range(120):
            RECENT_GAZES = tcpserver.getTopRecords()
            if len(RECENT_GAZES):
                print(RECENT_GAZES[0].toString())

            print("sleeping {}".format(i))
            
            time.sleep(1)

        socket_thread_alive = False
        tcpserver.server_close()
        print("waiting to close")
        sys.exit(0)
        print("should be closed now")
    # When ctrl+c is received
    except KeyboardInterrupt as e:
        # Set the alive attribute to false
        socket_thread_alive = False
        # Exit with error code
        sys.exit(e)

if __name__ == '__main__':
    winEyeGazeListener()
