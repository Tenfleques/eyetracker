# eye-tracker
Eye Tracker bindings that can be called from Python using cdll module. 

The functions in the library are executed in order:
    
        `int start()` fires up the tracker device

        `void stop()` stops the recording session 
        
        `size_t get_json(char* buffer, size_t buffer_size)` designed so that it
        can be called twice, the first time returns the size of required bufer 
        if buffer is a null pointer. 
        when buffer is not nullpointer then the resultig json is copied to the buffer.
        
        SessionRecord * get_session() returns a session record object.
     
   
        
The python interface connects the above defined lib to the other recording threads. 

i.e 
   1. Camera frames
   2. Video frames

From async the methods  exposed are: 
    
    1. start, 
    2. stop, 
    3. meta, 
    4. results 


### Requirements 
kivy
numpy
opencv

### Setup 
   Setting up kivy for the GUI app
   
`python -m pip install kivy_examples==1.11.1`

`python -m pip install docutils pygments pypiwin32 kivy_deps.sdl2==0.1.* kivy_deps.glew==0.1.*`

`python -m pip install kivy_deps.gstreamer==0.1.*`

`python -m pip install kivy_deps.angle==0.1.*`

`python -m pip install kivy==1.11.1`



