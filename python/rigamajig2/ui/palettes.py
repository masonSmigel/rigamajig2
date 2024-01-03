#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: darkPalette.py
    author: masonsmigel
    date: 01/2024
    description: 

"""

from PySide2.QtGui import QPalette, QColor

DEFAULT_PALETTE = None


class RigamajigPalette:
    palette = QPalette()

    # base
    palette.setColor(QPalette.WindowText, QColor(220, 220, 220))
    palette.setColor(QPalette.Button, QColor(68, 68, 70))
    palette.setColor(QPalette.Light, QColor(180, 180, 180))
    palette.setColor(QPalette.Midlight, QColor(43, 43, 45))
    palette.setColor(QPalette.Dark, QColor(35, 35, 37))
    palette.setColor(QPalette.Text, QColor(180, 180, 180))
    palette.setColor(QPalette.BrightText, QColor(220, 220, 220))
    palette.setColor(QPalette.ButtonText, QColor(220, 220, 220))
    palette.setColor(QPalette.Base, QColor(38, 38, 41))
    palette.setColor(QPalette.AlternateBase, QColor(44, 44, 48))
    palette.setColor(QPalette.Mid, QColor(63, 63, 65))
    palette.setColor(QPalette.Shadow, QColor(20, 20, 22))
    palette.setColor(QPalette.Link, QColor(56, 252, 196))
    palette.setColor(QPalette.ToolTipBase, QColor(42, 42, 44))
    palette.setColor(QPalette.ToolTipText, QColor(180, 180, 180))
    palette.setColor(QPalette.LinkVisited, QColor(80, 80, 80))
    palette.setColor(QPalette.Background, QColor(56, 56, 58))
    palette.setColor(QPalette.Window, QColor(56, 56, 58))

    # disabled
    palette.setColor(QPalette.Disabled, QPalette.WindowText, QColor(127, 127, 127))
    palette.setColor(QPalette.Disabled, QPalette.Text, QColor(127, 127, 127))
    palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(127, 127, 127))
    palette.setColor(QPalette.Disabled, QPalette.Highlight, QColor(80, 80, 80))
    palette.setColor(QPalette.Disabled, QPalette.HighlightedText, QColor(127, 127, 127))



class DarkPalette:
    palette = QPalette()

    # base
    palette.setColor(QPalette.WindowText, QColor(180, 180, 180))
    palette.setColor(QPalette.Button, QColor(66, 66, 66))
    palette.setColor(QPalette.Light, QColor(180, 180, 180))
    palette.setColor(QPalette.Midlight, QColor(90, 90, 90))
    palette.setColor(QPalette.Dark, QColor(35, 35, 35))
    palette.setColor(QPalette.Text, QColor(180, 180, 180))
    palette.setColor(QPalette.BrightText, QColor(180, 180, 180))
    palette.setColor(QPalette.ButtonText, QColor(180, 180, 180))
    palette.setColor(QPalette.Base, QColor(42, 42, 42))
    palette.setColor(QPalette.Window, QColor(53, 53, 53))
    palette.setColor(QPalette.Shadow, QColor(20, 20, 20))
    palette.setColor(QPalette.Link, QColor(56, 252, 196))
    palette.setColor(QPalette.AlternateBase, QColor(72, 72, 72))
    palette.setColor(QPalette.ToolTipBase, QColor(53, 53, 53))
    palette.setColor(QPalette.ToolTipText, QColor(180, 180, 180))
    palette.setColor(QPalette.LinkVisited, QColor(80, 80, 80))

    # disabled
    palette.setColor(QPalette.Disabled, QPalette.WindowText, QColor(127, 127, 127))
    palette.setColor(QPalette.Disabled, QPalette.Text, QColor(127, 127, 127))
    palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(127, 127, 127))
    palette.setColor(QPalette.Disabled, QPalette.Highlight, QColor(80, 80, 80))
    palette.setColor(QPalette.Disabled, QPalette.HighlightedText, QColor(127, 127, 127))
