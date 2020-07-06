from pydrive.drive import GoogleDrive 
from pydrive.auth import GoogleAuth 
import argparse

import os 
ap = argparse.ArgumentParser()
ap.add_argument("-p", "--path", required=True, type=str,
    help="path to the file to upload")
ap.add_argument("--parent", required=False, type=str,
    help="parent folder to the file to upload")
ap.add_argument("--result", required=False, type=str,
    help="result file to write upload id")


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

if args["parent"]:
    f = drive.CreateFile({'title': name, 'parents': [{'id': args["parent"]}]}) 
else:
    f = drive.CreateFile({'title': name}) 

f.SetContentFile(path) 
res = f.Upload()

with open(args["result"], "a") as fp:
    fp.write("{}\n".format(f["id"]))
    fp.close()
# f = None

