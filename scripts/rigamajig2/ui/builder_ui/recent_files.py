#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: recent_files.py.py
    author: masonsmigel
    date: 04/2023
    description: 

"""
import os

import maya.cmds as cmds

from rigamajig2.maya.data import abstract_data

RECENT_FILE_NAME = "rigamajig2_recentfiles.json"

RECENT_FILES_KEY = "recentfiles"
MAX_FILES_KEY = "maxfiles"

MAX_RECENT_FILES = 5


def getRecentFilePrefsPath():
    """return the directory to store the file within"""
    userPrefsPath = cmds.internalVar(upd=True)
    path = os.path.join(userPrefsPath, RECENT_FILE_NAME)
    return path


def addRecentFile(newFile):
    """ Add a new file to the list of recent files """
    dataObj = abstract_data.AbstractData()

    # read any existing data from the prefs file
    if os.path.exists(getRecentFilePrefsPath()):
        dataObj.read(getRecentFilePrefsPath())

    data = dataObj.getData()

    # get any recent files or create an empty list
    listOfRecentFiles = data.get(RECENT_FILES_KEY) or list()

    # if the rig file is already in the list of files than we can remove it since we'll re-add it to the top
    if newFile in listOfRecentFiles:
        listOfRecentFiles.remove(newFile)
    # insert the new file into the list
    listOfRecentFiles.insert(0, newFile)

    # check if there is a limit to the number of files to store.
    if not data.get(MAX_FILES_KEY):
        data[MAX_FILES_KEY] = MAX_RECENT_FILES

    maxFiles = data.get(MAX_FILES_KEY)
    # remove files that are past the max limit of files to remember
    if len(listOfRecentFiles) > maxFiles:
        listOfRecentFiles = listOfRecentFiles[:maxFiles]

    # write this data back to the prefs file
    data[RECENT_FILES_KEY] = listOfRecentFiles
    dataObj.write(getRecentFilePrefsPath())


def getRecentFileList():
    """
    Get a list of all recent files
    :return: a list of all recent files
    """
    if os.path.exists(getRecentFilePrefsPath()):
        dataObj = abstract_data.AbstractData()
        dataObj.read(getRecentFilePrefsPath())

        return dataObj.getData()[RECENT_FILES_KEY]
    return list()


def getMostRecentFile():
    """
    Get the MOST recent file opened
    :return: a single file path
    """
    if getRecentFileList():
        return getRecentFileList()[0]


if __name__ == '__main__':
    addRecentFile("test7")

    print (getRecentFileList())
