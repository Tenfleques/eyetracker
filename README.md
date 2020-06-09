# eye-tracker
`python main.py` starts a GUI of the tracking experiment 

Choose the output directory: 
    
    In this directory, the output files wil be stored:
        
            1. `video_camera.json` camera and video timeline in the tracking session 
            2. tracker.json  - tracker frames timeline in the tracking session 
            3. out-video.avi - camera frames taken during the tracking session 
            4. deomstration-video.avi shows the stimuli, human gaze and camera frames synchronized in a single video 

To use the tracker library the class TrackerCtrl in the file tracker_ctrl.py binds the control functions in TobiiEyeLib.dll so that they can be called in python environment 


Eye Tracker bindings that can be called from Python using cdll module. 

The functions in the library should be executed in order for optimal performance:
    
        `int start()` fires up the tracker device, reset previous session if exists and start recording 

        `void stop()` stops the recording session
        
        `void save_json(char* path)` save the tracker results to the path given 
         
        `size_t get_json(char* buffer, size_t buffer_size)` designed so that it
        can be called twice, the first time returns the size of required bufer 
        if buffer is a null pointer. 
        when buffer is not nullpointer then the resultig json is copied to the buffer.
        
        `void kill()` stops the connection to the device altogether
        
        
     
  
The python interface connects the above defined lib to the other recording threads. 

i.e 
   1. Camera frames 
   2. Video frames
   
 The camera frames can be controlled by the CameraCtrl class in `camera_feed_ctrl.py` 

 The video frames are controlled by the video_feed_ctrl module
 
 To process translations, between english and russian languages literals edit the _locale.json
 

### Requirements 
kivy

numpy

opencv

Pillow

json

ctypes

### Setup 
   Setting up kivy for the GUI app
   
`python -m pip install kivy_examples==1.11.1`

`python -m pip install docutils pygments pypiwin32 kivy_deps.sdl2==0.1.* kivy_deps.glew==0.1.*`

`python -m pip install kivy_deps.gstreamer==0.1.*`

`python -m pip install kivy_deps.angle==0.1.*`

`python -m pip install kivy==1.11.1`


### Binaries

https://drive.google.com/drive/folders/19hDrP7U7ChThVpxspUiiXnMFEnzLJSI5?usp=sharing 

# Changelog

### v1.0.0 June 1 2020
[gis-eye-tracker-mipt.v1.0.0](https://drive.google.com/file/d/19qfBZYu1MFLIm-piw-WG4E_Tnr5Q8SvG/view?usp=sharing) 
1. Records Tracker data, Video frames, Camera frames 
2. Exports timeline
3. Replays recorded session 

### v1.0.1 June 4 2020
[gis-eye-tracker-mipt.v1.0.1](https://drive.google.com/file/d/19tVGFxqfCK-UdPXCM71L3b1jpx3iVzz5/view?usp=sharing  )
1. Improvements to UI
2. Stimuli source can be JSON with description of duration to support image input 
3. User can choose which data streams to view during playback
4. Faster playback, video and camera frames are preloaded to memory 

### v1.0.2 June 6 2020
[gis-eye-tracker-mipt.v1.0.1](https://drive.google.com/file/d/19ttTYVzQAse1i7ebikz2DqthzJWXP3pN/view?usp=sharing )
1. Add combined video export on user demand
2. Bugfix incompatibility of frame sizes when replaying sessions recorded on different machines
3. User can type/paste path to source directory in the load dialog

### v1.0.3 June 8 2020
[gis-eye-tracker-mipt.v1.0.3](https://drive.google.com/file/d/19vT2oSnrzUhL4xwNMhqAWNygRoYWc55A/view?usp=sharing)
1. Add frame skipping 
2. Add optimal frame skipping 
3. Frame skipping is controlled on empirical level by the user

### v1.0.4 June 9 2020
[gis-eye-tracker-mipt.v1.0.4](https://drive.google.com/file/d/19yH-E4Uqyq0JXOkhoIgW3TLmi0g85k2T/view?usp=sharing)
1. Add user playback speed by select
2. Remove the empirical controls from v1.0.3
3. Memory efficient. No longer preload video frames to memory
4. Add video FPS controller together with speed multiplier




