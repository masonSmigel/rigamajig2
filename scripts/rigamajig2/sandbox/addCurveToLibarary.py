#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: addCurveToLibarary.py
    author: masonsmigel
    date: 11/2022
    discription: 

"""

import maya.cmds as cmds 

from rigamajig2.maya.data import curve_data



CURVE_DATA_PATH = '/Users/masonsmigel/Documents/dev/maya/rigamajig2/scripts/rigamajig2/maya/rig/controlShapes.data'

cdata = curve_data.CurveData()
cdata.read(CURVE_DATA_PATH)


sel = cmds.ls(sl=True)

cdata.gatherDataIterate(sel)


print cdata.getData()

cdata.write(CURVE_DATA_PATH)