#pragma once

#ifdef TOBIEYELIB_EXPORTS
#define TOBIEYELIB_API __declspec(dllexport)
#else
#define TOBIEYELIB_API __declspec(dllimport)
#endif

struct SessionRecord;

extern "C" TOBIEYELIB_API void stop();

extern "C" TOBIEYELIB_API int start();

extern "C" TOBIEYELIB_API size_t get_json(char* buffer, size_t buffer_size);

extern "C" TOBIEYELIB_API size_t save_json(char* path);

extern "C" TOBIEYELIB_API SessionRecord * get_session();