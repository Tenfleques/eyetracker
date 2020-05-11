import pickle
import logging
import logging.handlers
import socketserver
import struct
import select
import time
from threading import Thread
import sys
import json

from collections import deque
from eye_utilities.helpers import check_talon_directory

check_talon_directory()


class LogRecordStreamHandler(socketserver.StreamRequestHandler):
    """Handler for a streaming logging request.
    """
    def handle(self):
        """
        Handle multiple requests - each expected to be a 4-byte length,
        followed by the LogRecord in pickle format.
        """
        while self.server.play:
            chunk = self.connection.recv(4)

            if len(chunk) < 4:
                break

            slen = struct.unpack(">L", chunk)[0]
            chunk = self.connection.recv(slen)

            while len(chunk) < slen:
                if not self.server.play:
                    break
                chunk = chunk + self.connection.recv(slen - len(chunk))
            obj = self.un_pickle(chunk)

            record = logging.makeLogRecord(obj)

            self.handle_log_record(record)

    @staticmethod
    def un_pickle(data):
        return pickle.loads(data)

    def handle_log_record(self, record):
        if record.name == self.server.log_name:
            row = json.loads(record.getMessage())
            self.server.TrackerLOG["gaze"].append(row["gaze"])
            self.server.TrackerLOG["pos"].append(row["pos"])
            self.server.TrackerLOG["origin"].append(row["origin"])

        # logger = logging.getLogger(name)
        # logger.handle(record)


class LogRecordSocketReceiver(socketserver.ThreadingTCPServer):
    """
        simple TCP socket-based logging receiver.
    """

    allow_reuse_address = 1
    timeout = 3
    TrackerLOG = {
        "pos": deque(),
        "gaze": deque(),
        "origin": deque()
    }

    play = 0
    recording = 0

    def __init__(self, host='localhost',
                 port=logging.handlers.DEFAULT_TCP_LOGGING_PORT,
                 handler=LogRecordStreamHandler):

        self.handler = handler
        socketserver.ThreadingTCPServer.__init__(self, (host, port), self.handler)
        self.log_name = "gaze_logger"

    def __clear_tracker_log(self):
        for i, v in self.TrackerLOG.items():
            self.TrackerLOG[i].clear()

    def init(self):
        self.play = 1
        self.serve_until_stopped()

    def start(self):
        self.__clear_tracker_log()
        self.recording = 1
        return self.__is_recording()

    def stop(self):
        self.recording = 0

    def kill(self):
        self.recording = 0
        self.play = 0
        self.__clear_tracker_log()
        # self.shutdown()
        # self.server_close()

    def __is_recording(self):
        return self.recording

    def __is_listening(self):
        return self.play

    def save_json(self, path):
        with open(path, "w") as fp:
            fp.write(json.dumps(self.__make_json()))

    def __make_json(self):
        data = {}
        for i, v in self.TrackerLOG.items():
            data[i] = list(self.TrackerLOG[i])

        return data

    def get_json(self):
        return self.__make_json()

    def serve_until_stopped(self):
        while self.__is_listening():
            rd, wr, ex = select.select([self.socket.fileno()],
                                       [], [],
                                       self.timeout)

            if rd:
                if self.__is_recording():
                    self.handle_request()


def talon_gaze_listener():

    tcp_server = LogRecordSocketReceiver()
    socket_thread = Thread(target=tcp_server.init,)
    try:
        # Start the thread
        socket_thread.start()
        tcp_server.start()
        tracker_log = tcp_server.get_json()
        for i in range(10):
            tracker_log = tcp_server.get_json()
            time.sleep(1)

        times = [i["timestamp"] for i in tracker_log["gaze"] if "timestamp" in i]

        if len(times) > 0:
            frame_rate = len(times)/(max(times) - min(times))
            print("[INFO] frame rate of the tracker {} ".format(frame_rate))
        else:
            print("[INFO] nothing recorded")

        # print(tcp_server.get_json())

        tcp_server.stop()
        tcp_server.kill()
        sys.exit(0)

    # When ctrl+c is received
    except KeyboardInterrupt as e:
        # Set the alive attribute to false
        tcp_server.stop()
        tcp_server.kill()
        print("Done")
        # Exit with error code
        sys.exit(e)
    except Exception as ex:
        print("Exception ", ex)
        tcp_server.stop()
        tcp_server.kill()
        print("Done")
        # Exit with error code
        sys.exit(ex)


if __name__ == "__main__":
    talon_gaze_listener()
