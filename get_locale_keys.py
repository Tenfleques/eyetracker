import json
import os

locale = "_locale.json"

def get_all_eys():
    dire = "./"
    files = [f for f in os.listdir(dire) if f not in [locale, __file__]
             and ".dll" not in f and "._" not in f and os.path.isfile(f)]
    keys = {}
    func_str = "get_local_str("
    for file in files:
        file_name = os.path.join(dire, file)
        # print(file_name)
        with open(file_name, "r") as fp:
            for i in fp.readlines():
                if func_str in i:
                    f_spli = i.split(func_str)
                    for j in f_spli:
                        if ")" in j:
                            fin_key = j.strip().split(")")[0]
                            if fin_key[1] == "_" :
                                keys[fin_key] = {
                                    "en" : fin_key,
                                    "ru" : fin_key
                                }
            fp.close()

    return keys


def get_current_keys():
    keys = {}
    with open(locale, "r") as fp:
        keys = json.load(fp)
    return keys


if __name__ == "__main__":
    cur_keys = get_current_keys()
    all_keys = get_all_eys()
    for k,v in all_keys
