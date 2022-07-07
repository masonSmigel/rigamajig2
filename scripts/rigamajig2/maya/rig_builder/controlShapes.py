#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: controlShapes.py
    author: masonsmigel
    date: 07/2022

"""
# PYTHON
import os

# MAYA
import maya.cmds as cmds

# RIGAMAJIG
import rigamajig2.maya.meta as meta
import rigamajig2.maya.data.curve_data as curve_data


def load_controlShapes(path=None, applyColor=True):
    """
    Load the control shapes
    :param path: path to control shape
    :param applyColor: Apply the control colors.
    :return:
    """
    if not os.path.exists(path):
        raise Exception("Path does no exist {}".format(path))

    cd = curve_data.CurveData()
    cd.read(path)

    controls = [ctl for ctl in cd.getKeys() if cmds.objExists(ctl)]
    cd.applyData(controls, create=True, applyColor=applyColor)


def save_controlShapes(path=None):
    """save the control shapes"""
    cd = curve_data.CurveData()
    cd.gatherDataIterate(meta.getTagged("control"))
    cd.write(path)
