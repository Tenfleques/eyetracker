from pydrive.drive import GoogleDrive 
from pydrive.auth import GoogleAuth 
import argparse

import os 
ap = argparse.ArgumentParser()
ap.add_argument("-p", "--path", required=True, type=str,
    help="path to the file to upload")

args = vars(ap.parse_args())

# Below code does the authentication 
# part of the code 
gauth = GoogleAuth() 

# Creates local webserver and auto 
# handles authentication. 
gauth.LocalWebserverAuth()	 
drive = GoogleDrive(gauth) 

# replace the value of this variable 
# with the absolute path of the directory 

path = os.path.abspath(args["path"])
name = path.split(os.sep)[-1]

f = drive.CreateFile({'title': name, 'parents': [{'id': '19hDrP7U7ChThVpxspUiiXnMFEnzLJSI5'}]}) 
f.SetContentFile(path) 
res = f.Upload()
print(f["id"])
# f = None

