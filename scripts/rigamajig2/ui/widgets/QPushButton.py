#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: QPushButton.py
    author: Xingyu Lei
    date: 08/2023
    discription: implemented from: https://www.xingyulei.com/post/qt-detect-click/index.html

"""
from PySide2 import QtCore
from PySide2 import QtWidgets


class RightClickableButton(QtWidgets.QPushButton):
    rightClicked = QtCore.Signal()
    leftClicked = QtCore.Signal()
    doubleClicked = QtCore.Signal()

    def __init__(self, *args, **kwargs):
        super(RightClickableButton, self).__init__(*args, **kwargs)

        self.timer = QtCore.QTimer()
        self.timer.setSingleShot(True)
        self.timer.setInterval(250)
        self.timer.timeout.connect(self.timeout)

        self.is_double = False
        self.is_left_click = True

        self.installEventFilter(self)

    def eventFilter(self, obj, event):
        if event.type() == QtCore.QEvent.MouseButtonPress:
            if not self.timer.isActive():
                self.timer.start()

            self.is_left_click = False
            if event.button() == QtCore.Qt.LeftButton:
                self.is_left_click = True

            return True

        elif event.type() == QtCore.QEvent.MouseButtonDblClick:
            self.is_double = True
            return True

        return False

    def timeout(self):
        if self.is_double:
            self.doubleClicked.emit()
        else:
            if self.is_left_click:
                self.leftClicked.emit()
            else:
                self.rightClicked.emit()

        self.is_double = False
