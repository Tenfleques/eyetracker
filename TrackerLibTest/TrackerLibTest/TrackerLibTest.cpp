#include <iostream>
#include "TobiEyeLib.h"
#include <chrono>



int main() {
    start();
    int v;
    std::cin >> v;
    stop();
    
    size_t required_size = get_json(nullptr, 0);
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
    }
    save_json(path);

    exit(0);
    return 0;
}