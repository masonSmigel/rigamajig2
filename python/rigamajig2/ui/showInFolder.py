#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: openFolder.py
    author: masonsmigel
    date: 08/2022
    description:
"""
import platform

from PySide2 import QtCore
from PySide2 import QtGui


def showInFolder(filePath):
    """ Show the selected file in the enclosing folder """

    if platform.system() == 'Windows':
        if openInExplorer(filePath):
            return
    elif platform.system() == 'Darwin':
        if openInFinder(filePath):
            return

    fileInfo = QtCore.QFileInfo(filePath)
    if fileInfo.exists():
        if fileInfo.isDir():
            QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(filePath))
        else:
            QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(fileInfo.path()))
    else:
        raise FileNotFoundError("Invalid Directory path")


def openInExplorer(filePath):
    """ Open a file in in the file explorer"""
    fileInfo = QtCore.QFileInfo(filePath)
    args = []
    if not fileInfo.isDir():
        args.append("/select,")
    args.append(QtCore.QDir.toNativeSeparators(filePath))

    if QtCore.QProcess.startDetached("explorer", args):
        return True
    return False


def openInFinder(filePath):
    """ Open a file in in the finder"""
    args = ['-e', 'tell application "Finder"', '-e', 'activate', '-e', 'select POSIX file "{0}"'.format(filePath),
            '-e', 'end tell', '-e', 'return']

    if QtCore.QProcess.startDetached("/usr/bin/osascript", args):
        return True
    return False
