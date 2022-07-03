#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: builder_new.py
    author: masonsmigel
    date: 07/2022

"""
import os
import inspect
import pkgutil

from rigamajig2.shared.logger import Logger

CMPT_PATH = os.path.abspath(os.path.join(__file__, '../cmpts'))
_EXCLUDED_FOLDERS = ['base']
_EXCLUDED_FILES = ['__init__.py']


class ComponentManager(object):
    def getAvailableComponents(self, path):
        res = os.listdir(path)
        toReturn = list()
        for r in res:
            full_path = os.path.join(path, r)
            if r not in _EXCLUDED_FOLDERS and os.path.isdir(path + '/' + r) is True:
                res = os.listdir(full_path)

                if "build.py" in res:
                    toReturn.append(r)
                else:
                    getAvailableComponents(full_path)
        return toReturn

    def getComponentObjects(self, component=None):
        """
        get the component object
        :param component: name of the component to return the guide and build module for.
        :return: guide module object and a build module object for the given component
        :rtype: tuple
        """

        module_file = ".".join(component.rsplit('.', 1)[:-1])
        modulesPath = 'rigamajig2.sandbox.cmpts.{}.{}'
        guideModuleName = modulesPath.format(component, "guide")
        buildModuleName = modulesPath.format(component, "build")

        guideObject = __import__(guideModuleName, globals(), locals(), ["*"], 0)
        buildObject = __import__(buildModuleName, globals(), locals(), ["*"], 0)

        return guideObject, buildObject






if __name__ == '__main__':
    getAvailableComponents(CMPT_PATH)
