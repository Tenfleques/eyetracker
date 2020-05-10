#include "pch.h" // use stdafx.h in Visual Studio 2017 and earlier

#include <string.h>
#include <limits.h>
#include <thread>
#include <chrono>
#include "TobiEyeLib.h"
//#include <windows.h>


#include <tobii/tobii.h>
#include <tobii/tobii_streams.h>
#include <stdio.h>
#include <assert.h>
#include <map>
#include <iostream>
#include <chrono>
#include <thread>
#include <deque>
#include <utility>
#include <fstream>
#include <sstream>

// the tobii-tracker callbacks
void gaze_point_callback(tobii_gaze_point_t const* gaze_point, void* /* user_data */);

void gaze_origin_callback(tobii_gaze_origin_t const* gaze_origin, void* user_data);

void eye_position_callback(tobii_eye_position_normalized_t const* eye_pos, void* user_data);


double timeInSeconds() {
    auto current_time = std::chrono::system_clock::now();
    auto duration_in_seconds = std::chrono::duration<double>(current_time.time_since_epoch());
    return duration_in_seconds.count();
}

std::string process_inject(std::string inject) {
    if (!inject.empty()) {
        if (inject.front() != ',') {
            inject = "," + inject;
        }
    }
    return inject;
}

struct Point2D {
    Point2D(const float x, const float y) : x(x), y(y) {};
    Point2D(const float l[2]) : x(l[0]), y(l[1]) {};
    Point2D() : x(.0), y(.0) {};
    void setX(const float xx) {
        x = xx;
    }
    void setY(const float yy) {
        y = yy;
    }
    void setXY(const float xx, const float yy) {
        y = yy;
        x = xx;
    }

    virtual std::string to_string(const std::string& inject) {
        std::stringstream ss;
        ss << "{\"x\": " << std::fixed << x
            << ",\"y\": " << std::fixed << y << process_inject(inject) << "}";
        return ss.str();
    }
    float x = .0, y = .0;
};

struct Gaze : Point2D {
    bool valid;
    double timestamp;
    int64_t timestamp_us = 0;

    Gaze() : valid(false), timestamp(.0) {};
    Gaze(const float l[2], bool v, int64_t t) {
        valid = v;
        timestamp = timeInSeconds();
        timestamp_us = t;
        this->setXY(l[0], l[1]);
    }
    Gaze(const float l, const float r, bool v, int64_t t) {
        valid = v;
        timestamp = timeInSeconds();
        timestamp_us = t;
        this->setXY(l, r);
    }
    std::string to_json() {
        std::stringstream ss;
        ss << ",\"valid\": " << valid << ",\"timestamp_us\": " << timestamp_us
            << ",\"timestamp\": " << std::fixed << timestamp;
        return to_string(ss.str());
    }
};

struct Point3D : Point2D {
    Point3D(const float x, const float y, const float zz) {
        z = zz;
        this->setX(x);
        this->setY(y);
    };
    explicit Point3D(const float l[3]) {
        this->setX(l[0]);
        this->setY(l[1]);
        z = l[2];
    };
    Point3D() {
        z = .0;
    };
    void setZ(const float zz) {
        z = zz;
    }
    void setXYZ(const float xx, const float yy, const float zz) {
        y = yy;
        x = xx;
        z = zz;
    }
    std::string to_string(const std::string& inject) override {
        std::stringstream ss;
        ss << "{\"x\": " << std::fixed << x << ", \"y\": "
            << std::fixed << y << ", \"z\": " << z << process_inject(inject) << "}";
        return ss.str();
    }
    float z;
};

struct Eyes {
    Eyes(Point3D l, Point3D r) : left(std::move(l)), right(std::move(r)) {};
    Eyes(const float l[3], const float r[3]) : left(Point3D(l)), right(Point3D(r)) {};
    Eyes() : left(Point3D()), right(Point3D()) {};

    void setLeft(Point3D l, bool v) {
        left = std::move(l);
        v_l = v;
    }
    void setRight(Point3D r, bool v) {
        right = std::move(r);
        v_r = v;
    }
    Point3D left, right;
    bool v_l = false, v_r = false;
};

struct Pos3D : Eyes {
    double timestamp;
    int64_t timestamp_us = 0;

    Pos3D() : timestamp(.0) {};
    Pos3D(const float l[3], const float r[3], const bool v[2], const int64_t t) {
        timestamp = timeInSeconds();
        timestamp_us = t;
        this->setLeft(Point3D(l), v[0]);
        this->setRight(Point3D(r), v[1]);
    }
    std::string to_json() {
        std::stringstream ss;
        std::stringstream sv_l;
        std::stringstream sv_r;
        sv_l << ",\"valid\": " << v_l;

        sv_r << ",\"valid\": " << v_r;

        ss << "{\"timestamp\": " << std::fixed << timestamp
            << ",\"timestamp_us\": " << timestamp_us
            << ",\"left\": " << left.to_string(sv_l.str())
            << ",\"right\": " << right.to_string(sv_r.str()) << "}";
        return ss.str();
    }
};



struct SessionRecord {
    std::deque<Gaze> gazes;
    std::deque<Pos3D> poses;
    std::deque<Pos3D> origins;
    bool record_tracker = false;

    ~SessionRecord() {
        gazes.clear();
        poses.clear();
        origins.clear();

        gazes.~deque();
        poses.~deque();
        origins.~deque();

        this->stop();
    }
    void start() {
        gazes.clear();
        poses.clear();
        origins.clear();
        record_tracker = true;
    }

    void stop() {
        record_tracker = false;
    }

    void update(Gaze g) {
        if (!this->is_recording_tracker())
            return;
        gazes.push_back(g);
    }

    void update(Pos3D pg, bool is_pos = true) {
        if (!this->is_recording_tracker())
            return;

        if (is_pos) {
            poses.push_back(pg);
        }
        else {
            origins.push_back(pg);
        }
    }

    static std::string pos3d_json(const std::deque<Pos3D>& f) {
        std::string frames;
        for (auto s : f) {
            if (frames.empty()) {
                frames += s.to_json();
            }
            else {
                frames += ", " + s.to_json();
            }
        }
        frames = "[" + frames + "]";
        return  frames;
    }

    static std::string g_json(const std::deque<Gaze>& f) {
        std::string frames;
        for (auto s : f) {
            if (frames.empty()) {
                frames += s.to_json();
            }
            else {
                frames += ", " + s.to_json();
            }
        }
        frames = "[" + frames + "]";
        return  frames;
    }

    std::string to_json() const {
        std::string pos_frames = pos3d_json(poses);
        std::string origin_frames = pos3d_json(origins);
        std::string gaze_frames = g_json(gazes);

        std::string json = "{";
        json += "\"pos\": " + pos_frames;
        json += ",\"origin\" : " + origin_frames;
        json += ",\"gaze\": " + gaze_frames;
        json += "}";
        return json;
    }

    bool is_recording_tracker() const {
        return record_tracker;
    }
}sessionRecord;

// the tobii-tracker callbacks
void gaze_point_callback(tobii_gaze_point_t const* gaze_point, void* /* user_data */) {
    // update gaze
    sessionRecord.update(Gaze(gaze_point->position_xy,
        gaze_point->validity == TOBII_VALIDITY_VALID,
        gaze_point->timestamp_us));
}
void gaze_origin_callback(tobii_gaze_origin_t const* gaze_origin, void* user_data) {
    bool valid[2] = { gaze_origin->left_validity == TOBII_VALIDITY_VALID,
                     gaze_origin->right_validity == TOBII_VALIDITY_VALID };

    sessionRecord.update(Pos3D(gaze_origin->left_xyz,
        gaze_origin->right_xyz,
        valid, gaze_origin->timestamp_us), false);
}
void eye_position_callback(tobii_eye_position_normalized_t const* eye_pos, void* user_data) {
    bool valid[2] = { eye_pos->left_validity == TOBII_VALIDITY_VALID,
                     eye_pos->right_validity == TOBII_VALIDITY_VALID };

    sessionRecord.update(Pos3D(eye_pos->left_xyz,
        eye_pos->right_xyz,
        valid, eye_pos->timestamp_us), true);
}


bool assert_tobii_error(const tobii_error_t result, const char* msg = "error") {
    if (result != TOBII_ERROR_NO_ERROR) {
        std::cerr << "[ERROR] " << tobii_error_message(result) << " " << msg;
        return true;
    }
    return false;
}

void url_receiver(char const* url, void* user_data) {
    char* buffer = (char*)user_data;
    if (*buffer != '\0') return; // only keep first value

    std::string ur_s = url;
    const char* ur_ss = ur_s.c_str();

    if (strlen(url) < 256)
        strcpy(buffer, ur_ss);
}

struct TobiiCtrl {
    // Create API
    tobii_api_t* api = NULL;
    // Connect to the first tracker found
    tobii_device_t* device = NULL;
    // status flag
    tobii_error_t result = tobii_api_create(&api, NULL, NULL);
    // updates thread 
    bool continue_updating = false;
    
    ~TobiiCtrl() {
        stop();
    }

    bool get_continue_updating() {
        return continue_updating;
    }

    void stop_updating() {
        continue_updating = false;
    }

    void updateRecords() {
        while (this->get_continue_updating()) {
            // Optionally block this thread until data is available. Especially useful if running in a separate thread.
            result = tobii_wait_for_callbacks(1, &device);

            if (result != TOBII_ERROR_TIMED_OUT) {
                //std::cerr << "[ERROR] session recording timed out" << std::endl;
                //break;
            }

            // Process callbacks on this thread if data is available
            result = tobii_device_process_callbacks(device);
            if (result != TOBII_ERROR_NO_ERROR) {
                std::cerr << "[ERROR] session recording stopped" << std::endl;
                break;
            }
        }
    }
    int start() {
        continue_updating = true;

        if (api != NULL && device != NULL) {
            // device has started already
            return 0;
        }

        if (assert_tobii_error(result))
            return -1;

        // Enumerate devices to find connected eye trackers, keep the first
        char url[256] = { 0 };
        result = tobii_enumerate_local_device_urls(api, url_receiver, url);

        if (assert_tobii_error(result))
            return -1;

        if (*url == '\0') {
            std::cerr << "[ERROR] No device found\n";
            return -1;
        }

        result = tobii_device_create(api, url, TOBII_FIELD_OF_USE_INTERACTIVE, &device);

        if (assert_tobii_error(result, "device"))
            return -1;

        // Subscribe to gaze data
        result = tobii_gaze_point_subscribe(device, gaze_point_callback, 0);
        result = tobii_gaze_origin_subscribe(device, gaze_origin_callback, 0);
        result = tobii_eye_position_normalized_subscribe(device, eye_position_callback, 0);

        if (assert_tobii_error(result, "subscription"))
            return -1;

        return 0;
    }


    int stop() {
        this->stop_updating();
        if (device != NULL) {
            result = tobii_gaze_point_unsubscribe(device);
            if (assert_tobii_error(result, "unsubscribed"))
                return result;
            

            result = tobii_device_destroy(device);
            if (assert_tobii_error(result, "dev destroy "))
                return result;

            device = NULL;
        }
        if (api != NULL) {
            result = tobii_api_destroy(api);
            if (assert_tobii_error(result, "api destroy "))
                return result;
            api = NULL;
        }
        return 0;
    }
}tobiiCtrl;

void tobii_thread() {
    tobiiCtrl.updateRecords();
}

// thread controller 
std::thread update_thread;
std::map<size_t, const char*> map_results;
// exports 

void stop() {
    sessionRecord.stop();
    tobiiCtrl.stop_updating();

    if (update_thread.joinable()) {
        update_thread.join();
    }
    std::cout << "[INFO] stopped recording, device connection still alive" << std::endl;
}

void kill() {
    sessionRecord.stop();
    std::cout << "[INFO] stopping the device..." << std::endl;
    int tobii_stop = tobiiCtrl.stop();

    if (tobii_stop == 0) {
        std::cout << "[INFO] successfully stopped the device..." << std::endl;
    }
    else {
        std::cout << "[INFO] an error occured while trying to stop the device..." << std::endl;
    }

    if (update_thread.joinable()) {
        update_thread.join();
    }
    std::cout << "[INFO] stopped the device connection" << std::endl;
}

int start() {
    if (update_thread.joinable()) {
        // clean a double start
        std::cout << "[INFO] Cleaning the previous run ..." << std::endl;
        stop();
        update_thread.join();
    }
    std::cout << "[INFO] Starting new session ..." << std::endl;

    sessionRecord.start();
    int tobii_started = -1;
    tobii_started = tobiiCtrl.start();

    if (tobii_started == 0) {
        update_thread = std::thread(tobii_thread);
        std::cout << "[INFO] tracker device initialised and returns status code : "
            << tobii_started << std::endl;
    }
    else {
        std::cerr << "[ERROR] tracker device failed to initialise and returns status code : "
            << tobii_started << std::endl;
        sessionRecord.stop();
        return -1;
    }
    return 0;
}

size_t get_json(char *buffer, size_t buffer_size) {
    std::map<size_t, const char*>::iterator it;

    for (auto i : map_results) {
        std::cout << i.first << " " << buffer_size << std::endl;
    }
    it = map_results.find(buffer_size);
    if (it != map_results.end()) {
        std::cout << "[INFO] using results in map " << std::endl;
        std::strncpy(buffer, map_results[buffer_size] /* const char* */, buffer_size);
        //map_results.erase(it);

        return buffer_size;
    }

    std::string ss = sessionRecord.to_json();
    std::string cp = std::string(ss);

    size_t sz = ss.size();

   // map_results[buffer_size] = cp.data();
    try {
        std::strncpy(buffer, ss.data() /* const char* */, buffer_size);
    }
    catch (std::exception ex) {
        std::cerr << "[ERROR] an error has occured copying the json result " << ex.what() << std::endl;
    }
    

    if (buffer == nullptr) {
        if (buffer_size == -1) {
            //debug purpose preview
            std::cout << ss.data();
        }
        return sz;
    }  

    return sz;
}

size_t save_json(char* path = nullptr) {
    std::string ss = sessionRecord.to_json();

    if (path != nullptr) {
        std::ofstream f;
        f.open(path);
        f << ss;
        f.close();
    }

    return ss.size();
}

SessionRecord* get_session() {
    return &sessionRecord;
}