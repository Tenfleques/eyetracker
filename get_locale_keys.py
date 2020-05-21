import json
import os

locale = "_locale.json"


def get_all_eys():
    dire = "./"
    files = [f for f in os.listdir(dire) if f not in [locale, __file__]
             and (".kv" in f or ".py" in f) and "._" not in f and os.path.isfile(f)]

    components = dire + "components"

    more_files = [components + "/" + f for f in os.listdir(components)
                  if f not in [locale, __file__]
                  and (".kv" in f or ".py" in f)
                  and "._" not in f
                  # and os.path.isfile(f)
                  ]

    files.extend(more_files)

    keys = {}
    func_str = "get_local_str("
    for file in files:
        file_name = os.path.join(dire, file)
        # print(file_name)
        with open(file_name, "r", encoding='raw_unicode_escape') as fp:
            for i in fp.readlines():
                if func_str in i:
                    f_spli = i.split(func_str)
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

