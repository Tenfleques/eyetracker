#include <iostream>
#include "TobiEyeLib.h"
#include <chrono>
#include <sstream>


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
    float x = .0, y = .0;
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
    std::string to_string() {
        std::stringstream ss;
        ss << "{\"x\": " << std::fixed << x << ", \"y\": "
            << std::fixed << y << ", \"z\": " << std::fixed << z << "}";
        return std::string(ss.str());
    }
    float z;
};

struct TrackBox {

    TrackBox() {
        back_bottom_right = Point3D();
        back_bottom_left = Point3D();
        back_top_right = Point3D();
        back_top_left = Point3D();

        front_bottom_right = Point3D();
        front_bottom_left = Point3D();
        front_top_right = Point3D();
        front_top_left = Point3D();
    }

    std::string to_json() {
        std::stringstream ss;

        ss << "{"
            << "\"front\": {"
            << "\"bottom\": {"
            << "\"left\": " << front_bottom_left.to_string()
            << ",\"right\": " << front_bottom_right.to_string()
            << "},"
            << "\"top\": {"
            << "\"left\": " << front_top_left.to_string()
            << ",\"right\": " << front_top_right.to_string()
            << "}"
            << "},"
            << "\"back\": {"
            << "\"bottom\": {"
            << "\"left\": " << back_bottom_left.to_string()
            << ",\"right\": " << back_bottom_right.to_string()
            << "},"
            << "\"top\": {"
            << "\"left\": " << back_top_left.to_string()
            << ",\"right\": " << back_top_right.to_string()
            << "}"
            << "},"
            << "}";

        return ss.str();
    }

    Point3D back_bottom_right, back_bottom_left, back_top_right, back_top_left;
    Point3D front_bottom_right, front_bottom_left, front_top_right, front_top_left;
};
int main() {
    start();
    int v;
    
    stop();
    
    /*size_t required_size = get_json(nullptr, 0);
    std::cout << "[INFO] required buffer size " << required_size << std::endl;
    char* x = new char[required_size];
    size_t confirm = get_json(x, required_size);
    std::cout << "[INFO] confirmed buffer size " << confirm << std::endl;
    std::cout << x << std::endl;
    std::string s = "./results.json";

    char* path = new char[s.size()];
    int i = 0;
    for (auto c : s) {
        path[i] = c;
        i++;
    }*/

    // save_json(path);
    TrackBox *trackbox = get_trackbox();

    std::cout << trackbox[0].to_json();

    std::cin >> v;

    kill();
    exit(0);
    return 0;
}