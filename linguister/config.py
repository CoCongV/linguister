import json
import os
import platform
from collections import UserDict

unix_path = os.path.join(os.path.expanduser('~'), '.config/linguister/')
conf_file = os.path.join(unix_path, 'config.json')


class Config(UserDict):
    def __init__(self, *args, **kwargs):
        super().__init__(self, *args, **kwargs)
        self.data.update({'SDKS': ['Iciba', 'Youdao'], 'DEBUG': False})

    def __getattr__(self, key):
        return super().__getitem__(key)

    def load_conf(self, path=conf_file):
        try:
            with open(conf_file, 'r') as f:
                conf = json.load(f)
        except FileNotFoundError as e:
            if self.DEBUG:
                raise e
            else:
                return
        else:
            self.update(conf)
            return conf

    def dump_conf(self, path=conf_file):
        with open(path, 'w') as f:
            conf = json.dump(self.data, f)
        return path
