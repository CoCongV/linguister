import os
import platform
from collections import UserDict

import toml

unix_path = os.path.join(os.path.expanduser('~'), '.config/linguister/')
conf_toml = os.path.join(unix_path, 'config.toml')


class Config(UserDict):
    data = {
        'SDKS': ['Iciba', 'Youdao'],
        'DEBUG': False
    }

    def __getattr__(self, key):
        return super().__getitem__(key)

    def load_toml(self, path=conf_toml):
        try:
            with open(conf_toml, 'r') as f:
                conf = toml.load(f)
        except FileNotFoundError as e:
            if self.DEBUG:
                raise e
            else:
                return
        else:
            self.update(conf)
            return conf

    def dump_toml(self, path=conf_toml):
        with open(path, 'w') as f:
            conf = toml.dump(self.data, f)
        return path
