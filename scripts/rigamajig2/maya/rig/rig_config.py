"""Settings"""
import os
from collections import OrderedDict
import rigamajig2.maya.data.abstract_data as abstract_data

MODEL_FILE = 'model_file'
SKELETON_FILE = 'skeleton_file'
SKELETON_POS = 'skeleton_pos'

PRE_SCRIPT = 'pre_script'
POST_SCRIPT = 'post_script'
PUB_SCRIPT = 'pub_script'

L_COLOR = 'l_color'
R_COLOR = 'r_color'
C_COLOR = 'c_color'

USE_PROXY_ATTRS = 'use_proxy_attrs'


class Settings(object):
    def __init__(self, path, asset):
        self.path = path
        self._data = OrderedDict()

        self.file = os.path.join(self.path, '{}.rig'.format(asset))

    def get_rel_path(self, path):
        """
        get the path relative to the
        :param path:
        :return:
        """
        return os.path.relpath(path, self.path)

    def write(self):
        """write the file"""
        data = abstract_data.AbstractData()
        data.setData(self._data)
        data.write(self.file)

    def read(self):
        """read the file"""
        data = abstract_data.AbstractData()
        data_ = data.read(self.file)
        self._data = data_

    def append(self, data):
        """append data"""
        self.read()
        for key in data:
            self._data[key] = data[key]
        self.write()

    def set(self, key, data):
        """Set the data of a specific key"""
        self.read()
        self._data[key] = data
        self.write()

    def get(self, variable):
        """get a specific key"""
        return self._data[variable]
