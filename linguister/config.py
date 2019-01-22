import os
import platform

import toml

unix_path = os.path.join(os.path.expanduser('~'), '.config/linguister/')
conf_toml = os.path.join(unix_path, 'config.toml')


class Config:
    SDKS = ['iciba', 'youdao']
    DEBUG = False

    def __init__(self, SDKS=None, DEBUG=False):
        self._init(SDKS, DEBUG)

    def _init(self, SDKS=None, DEBUG=False):
        self.SDKS = SDKS or self.SDKS
        self.DEBUG = DEBUG or self.DEBUG

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
            self._init(**conf)
            return conf
    
    def dump_toml(self, path=conf_toml):
        conf_attr = {}
        for k, v in self.__dict__.items():
            if k.isupper():
                conf_attr[k] = v
        with open(path, 'w') as f:
            conf = toml.dump(conf_attr, f)
        return path
