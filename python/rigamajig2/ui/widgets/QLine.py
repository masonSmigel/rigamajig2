#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: QLine.py
    author: masonsmigel
    date: 07/2023
    description: 

"""

from PySide2 import QtWidgets


class QLine(QtWidgets.QFrame):

    def __init__(self, horizontal=True):
        super(QLine, self).__init__()

        if horizontal:
            self.setFrameShape(QtWidgets.QFrame.HLine)
        else:
            self.setFrameShape(QtWidgets.QFrame.VLine)

        self.setFrameShadow(QtWidgets.QFrame.Sunken)
