#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    Rigamjig2 modular rigging system

    project: rigamajig2
    file: __init__.py
    author: masonsmigel
    date: 01/2021

"""
import sys

from . import configureLoggers

VERSION_MAJOR = 1
VERSION_MINOR = 3
VERSION_PATCH = 1

# pylint: disable = invalid-name
version_info = (VERSION_MAJOR, VERSION_MINOR, VERSION_PATCH)
version = '%i.%i.%i' % version_info
__version__ = version

__all__ = ['version', 'version_info', '__version__']

# setup the loggers
configureLoggers.configureLoggers()


def reloadModule(name='rigamajig2', log=True):
    """
    Reload a module
    :param name: name of tha module to reload
    :param log: log the modules reloaded
    :return:
    """
    allModules = sys.modules.copy()
    for module in allModules:
        if module.startswith(name):
            if log:
                print("Reloaded module: {}".format(module))
            del sys.modules[module]
