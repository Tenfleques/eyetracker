#!/usr/bin/python
import os
import cv2
import wget
import json
import zipfile
import requests
from helpers import get_app_dir, file_log
import platform
from distutils.dir_util import copy_tree

APP_DIR = get_app_dir()

def download_file_from_google_drive(id, destination):
    URL = "https://docs.google.com/uc?export=download"

    session = requests.Session()

    response = session.get(URL, params = { 'id' : id }, stream = True)
    token = get_confirm_token(response)

    if token:
        params = { 'id' : id, 'confirm' : token }
        response = session.get(URL, params = params, stream = True)

    save_response_content(response, destination)    

def get_confirm_token(response):
    for key, value in response.cookies.items():
        if key.startswith('download_warning'):
            return value

    return None

def save_response_content(response, destination):
    CHUNK_SIZE = 32768

    with open(destination, "wb") as f:
        for chunk in response.iter_content(CHUNK_SIZE):
            if chunk: # filter out keep-alive new chunks
                f.write(chunk)


class UpdateCtrl():
    update_fname = None
    update_id = None
    update_name = None
    update_version = None 

    def get_update_details(self):
        return {
            "name": self.update_name,
            "version" : self.update_version
        }

    def check_updates(self, target="main"):
        
        # if updates available tell and change button to click to update
        with open(os.path.join(APP_DIR, "assets", "updates.json")) as fp:
            updates_links = json.load(fp)
            fp.close()
        
        # get current version
        with open(os.path.join(APP_DIR, "assets", "version.json")) as fp:
            current_version_inf = json.load(fp)
            fp.close()
            current_version = current_version_inf.get(target, {})

            self.update_name = current_version.get("name", None)
            major, minor, patch = current_version.get("version", [0, 0, 0])


        resource_details = updates_links.get(target, {})
        file_log("[INFO] {}".format(resource_details))
        
        if resource_details.get("url", None):
            user_tmp_folder = os.path.join(APP_DIR, "user", "tmp")
            os.makedirs(user_tmp_folder, exist_ok=True)
            user_tmp_file = os.path.join(user_tmp_folder, "releases.changelog") 

            try:
                if os.path.isfile(user_tmp_file):
                    os.remove(user_tmp_file)

                filename = wget.download(resource_details.get("url"), user_tmp_file)

                with open(filename) as rfp:
                    # get the list of updates
                    lines = rfp.readlines()
                    rfp.close()
                    if len(lines) < 3:
                        file_log("[INFO] no update available")
                        return 1

                    latest = lines[-1]
                    if latest:
                        try:
                            latest_arr = [int(i.strip()) for i in latest.split(".")]
                        except Exception as cast_err:
                            file_log("[ERROR] failed to cast new update version numbers")
                            return -1

                        if len(latest_arr) == 3:
                            if major != latest_arr[0] or minor != latest_arr[1] or patch != latest_arr[2]:
                                # we have an update
                                self.update_version = "v{}.{}.{}".format(latest_arr[0], latest_arr[1], latest_arr[2] )
                                latest_str = lines[-2]
                                if len(latest_str) > 5:
                                    self.update_id = latest_str
                                    self.update_fname = "v{}.{}.{}.zip".format(latest_arr[0], latest_arr[1], latest_arr[2])
                                else: 
                                    file_log("[ERROR] failed to parse new update link")
                                    return -1
                            else:
                                file_log("[INFO] currently using the latest build") 
                                return 1
                        else: 
                            file_log("[ERROR] failed to parse new update version string")
                            return -1

            except Exception as err:
                print("[ERROR] error looking up updates")
                file_log("[ERROR] {}".format(err))
            if self.update_id:
                return 0
            return -1

    def update_app(self, cb):
        try:
            if self.update_id is not None:
                target = os.path.dirname(APP_DIR)

                dir_target = "{}.{}".format(os.path.join(target, self.update_name), self.update_version)
                # short_cut_name = os.path.join(target, "GIS Eyetracker MIPT.lnk")
                
                target = os.path.join(target, self.update_fname)

                file_log("[INFO] downloading {}".format(self.update_id))
                download_file_from_google_drive(self.update_id, target)
                file_log("[INFO] expanding {}".format(dir_target))

                with zipfile.ZipFile(target, 'r') as zip_ref:
                    zip_ref.extractall(dir_target)
                    zip_ref.close()

                if os.path.isfile(target):
                    os.remove(target)

                dir_list = os.listdir(dir_target)
                
                extracted_dir = None
                for extracted_dir in dir_list:
                    extracted_dir = os.path.join(dir_target, extracted_dir)
                    if os.path.isdir(extracted_dir):
                        if self.update_name in extracted_dir:
                            break

                if extracted_dir is not None:
                    fromDirectory = os.path.join(APP_DIR, "user")
                    toDirectory = os.path.join(extracted_dir, "user")

                    copy_tree(fromDirectory, toDirectory)

                cb()

                file_log("[INFO] finished downloading and extracting update")
        except Exception as err:
            print(err)


if __name__ == "__main__":
    settings = UpdateCtrl()
    settings.check_updates()
    settings.update_app()