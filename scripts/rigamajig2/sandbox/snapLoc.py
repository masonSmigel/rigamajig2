#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajgi2
    file: locSnapUtil.py
    author: masonsmigel
    date: 07/2022
    discription: locator snapping utility tool

"""

import math
import maya.cmds as cmds
import maya.api.OpenMaya as om2


def createNode(name=None, type='locator'):
    """create a node of a given type"""

    # determine the created node type
    if type == 'locator':
        loc = cmds.spaceLocator(name='loc_0')
    elif type == 'joint':
        loc = cmds.createNode('joint', name='joint_0')

    elif type == 'null':
        loc = cmds.createNode("transform", name="null_0")
    else:
        raise Exception("{} is not a valid type. Please choose from: ['locator', 'joint', 'null']")

    if name:
        cmds.rename(loc, name)
    return loc


def matchRotate(source, target):
    """
    Match the rotation of one object to another rotation.
    This matching method is awesome. It works across regardless of mismatched rotation orders or transforms who's
    parents have different rotation orders.

    duplicate from rigamajig2.maya.transform to keep module isolated.

    :param source: Source transfrom
    :type source: str
    :param target:  Target transform to match
    :type target: str
    """
    rotOrder = cmds.getAttr('{}.rotateOrder'.format(source))
    matrixList = cmds.getAttr('{}.worldMatrix'.format(source))

    # Create an empty MMatrix from the world space matrix:
    mMatrix = om2.MMatrix(matrixList)  # MMatrix
    mTransformMtx = om2.MTransformationMatrix(mMatrix)
    eulerRot = mTransformMtx.rotation()  # MEulerRotation

    # Update rotate order to match original object
    eulerRot.reorderIt(rotOrder)

    angles = [math.degrees(angle) for angle in (eulerRot.x, eulerRot.y, eulerRot.z)]
    cmds.xform(target, ws=True, rotation=angles)


def createAtSelection(selection=None, mode='single', type='locator'):
    """
    create a locator at the current selection.

    when the mode is set to single it will create a locator centered around each selected object.
    or at the the center of the selected components on each object.

    When the mode is set to multiple it will place a locator at every selected transform or componen

    :param selection:
    :param mode:
    :param type:
    :return:


    filterExpand constants
    28 - nurbs Cvs
    32 - polygon edges
    """

    if selection is None:
        selection = cmds.ls(sl=True, fl=True)

    if len(selection) < 1:
        return createNode(type=type)

    nodeType = cmds.nodeType(selection[0])
    locators = list()
    # if a nurbs curve place one locator at each selected CV
    if nodeType == 'nurbsCurve':
        selection = cmds.filterExpand(selection, selectionMask=28)

        for s in selection:
            pos = cmds.pointPosition(s, world=True)
            loc = createNode(type=type)
            cmds.xform(loc, ws=True, t=pos)
            locators.append(loc)

    # if the selection is a nurbs surface get the average position.
    elif nodeType == 'nurbsSurface':

        if '.cv[' in selection[0]:
            cvs = cmds.filterExpand(selection, expand=True, selectionMask=28)
        elif '.sf[' in selection[0]:
            pass

        posSum = om2.MVector()
        for cv in cvs:
            pos = cmds.pointPosition(cv, world=True)
            posVector = om2.MVector(pos)
            posSum += posVector

        avgPos = posSum / len(cvs)
        loc = createNode(type=type)
        cmds.xform(loc, ws=True, t=avgPos)
        locators.append(loc)

    elif nodeType == 'mesh':

        # get the type of component selection vert or edge
        if '.vtx[' in selection[0]:
            verticies = cmds.filterExpand(selection, selectionMask=31)

        elif '.e[' in selection[0]:
            edges = cmds.filterExpand(selection, selectionMask=32)
            verticies = list()
            for edge in edges:
                vertsFromEdge = cmds.polyListComponentConversion(edge, fromEdge=True, toVertex=True)
                vertsFlattened = cmds.ls(vertsFromEdge, fl=True)
                verticies += vertsFlattened

        # create the locators
        if mode == 'single':
            posSum = om2.MVector()
            for vertex in verticies:
                pos = cmds.pointPosition(vertex, world=True)
                posVector = om2.MVector(pos)
                posSum += posVector

            avgPos = posSum / len(verticies)
            loc = createNode(type=type)
            cmds.xform(loc, ws=True, t=avgPos)
            locators.append(loc)

        elif mode == 'many':
            for vertex in verticies:
                loc = createNode(type=type)
                pos = cmds.pointPosition(vertex, world=True)
                cmds.xform(loc, ws=True, t=pos)
                locators.append(loc)

    # if not a component selection use the transform of the selection.
    else:
        for s in selection:
            if cmds.nodeType(s) in ['transform', 'joint']:
                loc = createNode(type=type)
                pos = cmds.xform(s, q=True, ws=True, rp=True)
                cmds.xform(loc, ws=True, t=pos)
                matchRotate(s, loc)
                locators.append(loc)

    return locators


if __name__ == '__main__':
    selection = cmds.ls(sl=True)
    createAtSelection(selection, mode='single')
