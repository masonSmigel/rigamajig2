#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    This is the json for abstract data

    project: rigamajig2
    file: __init__.py
    author: masonsmigel
    date: 01/2021
"""

import getpass
import json
import os
import sys
from collections import OrderedDict
from time import gmtime, strftime
import rigamajig2.shared.common as common
import logging

logger = logging.getLogger(__name__)


class AbstractData(object):
    """ This class is a template for any data we need to save."""

    def __init__(self):
        """
        constructor for the abstract class. Abstract Class is used as  template for all data classes
        """
        self._data = OrderedDict()
        self._filepath = None

    def __add__(self, other):
        """
        Add data from one data object to another.

        :param other: The other object you want to add data to.
        :type other: AbstractData
        """
        if not isinstance(other, AbstractData):
            raise TypeError('{0} is of type {1}. It must be of type AbstractData'
                            'or inherit from it.'.format(other, type(other)))

        # Copy the data and comp the two dictionares
        data = OrderedDict(**self._data)
        data.update(other.getData())
        # Make a new data Object

        dataObject = other.__class__()
        dataObject.setData(data)
        # return to data object
        return dataObject

    def __sub__(self, other):
        """
        Subtract data from one data object to another.

        :param other: The other object you want to add data to.
        :type other: AbstractData
        """
        if not isinstance(other, AbstractData):
            raise TypeError('{0} is of type {1}. It must be of type AbstractData'
                            'or inherit from it.'.format(other, type(other)))

        # Copy the data and comp the two dictionares
        data = OrderedDict(**self._data)
        for key in other.getData():
            data.pop(key)
        # Make a new data Object
        dataObject = other.__class__()
        dataObject.setData(data)
        # return to data object
        return dataObject

    def gatherData(self, item):
        """
        This method will gather data from the item passed as an argument.
        It stores the data on the self._data attribute
        """
        pass

    def gatherDataIterate(self, items):
        """
        This method will iterate through the list of items and use the gatherData method to store the
        data on the self._data attribute
        """
        for item in items:
            self.gatherData(item)

    def getData(self):
        """
        This will return the self._data attribute
        """
        return self._data

    def getKeys(self):
        """
        This will return a list of all the keys
        :return:
        """
        return list(self._data.keys())

    def setData(self, value):
        """
        This should only be used for setting the self._data attribute to a dictionary.

        :param value: the data you're trying to set.
        :type value: dict
        """
        if not isinstance(value, dict):
            raise TypeError("The data must be passed in as a dictionary.")

        self._data = value

    def applyData(self, attributes=None):
        """
        Holder method for inherited classes to determine data use
        """
        pass

    def write(self, filepath, createDirectory=True):
        """
        This will write the dictionary information to disc in .json format

        :param filepath: The path to the file you wish to write.
        :type filepath: str
        :param createDirectory: Create file path if needed
        :type createDirectory: bool
        """

        if not isinstance(self._data, (dict, OrderedDict)):
            raise TypeError("The data must be passed in as a dictionary.")
        writeData = OrderedDict(user=getpass.getuser(),
                                type=self.__class__.__name__,
                                time=strftime("%Y-%m-%d %H:%M:%S", gmtime()))
        writeData['data'] = self._data
        data = json.dumps(writeData, indent=4, ensure_ascii=False)

        # Create path if needed
        directory = os.path.dirname(filepath)
        if createDirectory:
            if not os.path.isdir(directory):
                logger.info('making path{0}'.format(directory))
                os.makedirs(directory)

        # Write Data
        f = open(filepath, 'w')
        f.write(data)
        f.close()

        self._filepath = filepath

    def read(self, filepath):
        """
        This will read a .json file and return the data in the file.

        :param filepath: the path of the file to read
        :type filepath: str
        :return: Data from the filepath given.
        :rtype: dict
        """
        if not os.path.isfile(filepath):
            raise RuntimeError("The file {0} does not exists.".format(filepath))

        f = open(filepath, 'r')
        if sys.version_info.major == 3:
            data = json.loads(f.read(), object_pairs_hook=OrderedDict)
        else:
            data = json.loads(f.read().decode('utf-8'), object_pairs_hook=OrderedDict)
        f.close()

        # Set the new filepath on the class
        self._filepath = filepath
        self._data = common.convertDictKeys(data['data'])
        return self._data

    @classmethod
    def getDataType(cls, filepath):
        """
        Read a given data file and return the data type of that file

         :param filepath: the path of the file to read
        :type filepath: str
        :return: datatype of the given file
        :rtype: str
        """
        f = open(filepath, 'r')
        if sys.version_info.major == 3:
            data = json.loads(f.read(), object_pairs_hook=OrderedDict)
        else:
            data = json.loads(f.read().decode('utf-8'), object_pairs_hook=OrderedDict)
        f.close()

        datatype = data['type']
        return datatype
