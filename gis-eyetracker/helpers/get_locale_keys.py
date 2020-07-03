import json
import os

locale = "_locale.json"


def get_all_eys():
    dire = ["./", "./screens", "./settings/screens", "./settings/subscreens", "./ctrls", "./generator_libs"]
    files = []

    for i in dire:
        all_fs = os.listdir(i)
        # print(all_fs)
        fs = [os.path.join(i,f) for f in all_fs if f not in [locale, __file__]
             and (".kv" in f or ".py" in f) and os.path.isfile(os.path.join(i,f))]
        files.extend(fs)

    keys = {}
    func_str = "get_local_str("
    func_str_2 = "get_local_str_util("
    
    for file_name in files:
        with open(file_name, "r", encoding='raw_unicode_escape') as fp:
            for i in fp.readlines():
                f_spli = None
                x = None
                if func_str in i:
                    f_spli = i.split(func_str)
                if func_str_2 in i:
                    x= True
                    f_spli = i.split(func_str_2)

                if f_spli is not None:
                    for j in f_spli:
                        if ")" in j:
                            fin_key = j.strip().split(")")[0]

                            if fin_key[1] == "_":
                                fin_key = fin_key.replace("\"", "").replace("'", "")

                                keys[fin_key] = {
                                    "en": fin_key,
                                    "ru": fin_key
                                }
            fp.close()

    return keys


def get_current_keys():
    with open(locale, "r", encoding='utf-8') as f:
        keys = json.loads(f.read().encode('utf-8').decode())
        f.close()
    return keys


if __name__ == "__main__":
    cur_keys = get_current_keys()
    all_keys = get_all_eys()

    for k, v in cur_keys.items():
        all_keys[k] = v

    with open(locale, "w") as fp:
        json.dump(all_keys, fp, ensure_ascii=False)
        fp.close()

