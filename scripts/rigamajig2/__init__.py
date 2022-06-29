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

VERSION_MAJOR = 1
VERSION_MINOR = 0
VERSION_PATCH = 0

version_info = (VERSION_MAJOR, VERSION_MINOR, VERSION_PATCH)
version = '%i.%i.%i' % version_info
__version__ = version

__all__ = ['version', 'version_info', '__version__']

logger = logging.getLogger(__name__)


def reloadModule(name='rigamajig2', log=True):
    """
    Reload a module
    :param name: name of tha module to reload
    :param log: log the modules reloaded
    :return:
    """
    keys_list = sys.modules.copy()
    for mod in keys_list:
        if mod.startswith(name):
            if log:
                logger.info("Reloaded module: {}".format(mod))
            del sys.modules[mod]