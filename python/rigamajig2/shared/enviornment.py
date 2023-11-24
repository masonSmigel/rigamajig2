#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: enviornment.py.py
    author: masonsmigel
    date: 11/2023
    description: 

"""
import os
import platform
import sys

RIGAMJIG_ROOT_DIR = os.path.normpath(
    os.path.join(os.path.dirname(os.path.realpath(__file__)), "../../../")
)


def isInMaya() -> bool:
    """Check if the current running environment is Maya"""
    executable = sys.executable
    if executable.endswith("Maya"):
        return True
    return False


def isInMayaPy() -> bool:
    """Check if the current running environment is mayapy"""
    executable = sys.executable
    if executable.endswith("mayapy"):
        return True
    return False


def isInMayaBatch() -> bool:
    """Check if the current running environment is mayabatch"""
    executable = sys.executable
    if executable.endswith("mayabatch"):
        return True
    return False


def getMayaLocation(mayaVersion):
    """
    Get the location of maya install
    :param mayaVersion: version of maya
    :return: path to where maya is installed
    """
    if "MAYA_LOCATION" in os.environ.keys():
        return os.environ["MAYA_LOCATION"]
    if platform.system() == "Windows":
        return "C:/Program Files/Autodesk/Maya{0}".format(mayaVersion)
    elif platform.system() == "Darwin":
        return "/Applications/Autodesk/maya{0}/Maya.app/Contents".format(mayaVersion)
    else:
        location = "/usr/autodesk/maya{0}".format(mayaVersion)
        if mayaVersion < 2016:
            # Starting Maya 2016, the default install directory name changed.
            location += "-x64"
        return location


def mayapy(mayaVersion):
    """
    Get the mayapy executable path
    :param mayaVersion: version of maya
    :return: path to where maya is installed
    """
    python_exe = "{}/bin/mayapy".format(getMayaLocation(mayaVersion))
    if platform.system() == "Windows":
        python_exe += ".exe"
    return python_exe
