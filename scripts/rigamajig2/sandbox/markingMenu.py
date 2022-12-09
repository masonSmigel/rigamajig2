#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: markingMenu.py.py
    author: masonsmigel
    date: 12/2022
    discription: 

"""
import maya.cmds as cmds


import rigamajig2.maya.joint
import rigamajig2.maya.curve


def mirrorJointSelection(mode="translate"):
    """ Mirror the selection"""
    selection = cmds.ls(sl=True)
    for joint in selection:
        joints = cmds.listRelatives(cmds.ls(sl=True, type='joint'), ad=True, type='joint') or []
        rigamajig2.maya.joint.mirror(joints + [joint], axis='x', mode=mode)


# --------------------------------------------------------------------------------
# functions to use in the marking menu
# they need to be able to be called without arguments since we must call them from a mel command
# --------------------------------------------------------------------------------

def mirrorJointTranslate():
    mirrorJointSelection(mode="translate")


def mirrorJointRotate():
    mirrorJointSelection(mode="rotate")


def mirrorCurveSelection():
    rigamajig2.maya.curve.mirror(cmds.ls(sl=True, type='transform'), axis='x', mode='replace')
