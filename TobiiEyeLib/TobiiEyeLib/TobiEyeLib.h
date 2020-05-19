#pragma once

#ifdef TOBIEYELIB_EXPORTS
#define TOBIEYELIB_API __declspec(dllexport)
#else
#define TOBIEYELIB_API __declspec(dllimport)
#endif

extern "C" struct SessionRecord;
extern "C" struct TrackBox;

extern "C" TOBIEYELIB_API void stop();

extern "C" TOBIEYELIB_API void kill();

extern "C" TOBIEYELIB_API int start();

extern "C" TOBIEYELIB_API size_t get_json(char* buffer, size_t buffer_size);

extern "C" TOBIEYELIB_API size_t get_meta_json(char* buffer, size_t buffer_size);

extern "C" TOBIEYELIB_API size_t save_json(char* path);

extern "C" TOBIEYELIB_API SessionRecord * get_session();

extern "C" TOBIEYELIB_API TrackBox * get_trackbox();