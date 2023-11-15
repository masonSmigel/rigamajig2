#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: resources.py.py
    author: masonsmigel
    date: 11/2023
    description: 

"""
from typing import Tuple

from PySide2.QtCore import QSize
from PySide2.QtGui import QIcon, QPixmap


class Resources:
    @classmethod
    def getIcon(cls, iconPath: str) -> QIcon:
        """
        Get a QIcon from a path.
        :param iconPath: path to the icon
        :return:
        """

        icon = QIcon(iconPath)
        return icon

    @classmethod
    def iconToPixmap(cls, icon: QIcon, size: Tuple[int, int] = None) -> QPixmap:
        """
        Convert an Icon to a pixmap
        :param icon: QIcon to convert to a pixmap
        :param size: new size to set the icon to. If none the default size of the Icon will be used
        """
        if not size:
            size = icon.actualSize(QSize())

        pixmap = QIcon(icon).pixmap(QSize(*size))
        return pixmap
