#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: ue.py
    author: masonsmigel
    date: 02/2023
    discription: Functions for working with rigamajig and unreal within maya

"""
from collections import OrderedDict
import maya.cmds as cmds
import maya.mel as mel
from rigamajig2.maya import meta
from rigamajig2.maya import decorators

try:
    if "fbxmaya" not in cmds.pluginInfo(q=True, ls=True):
        cmds.loadPlugin("fbxmaya")
except:
    raise Exception("Failed to load maya FBX plugin")


def formatFBXOptions(options):
    """
    Format a dictonary of keywords and values into a string to be used as the 'options' argument in the file comman
    :param options: dictionary of keywords and values to set in the string formatting
    :return: string of options
    """

    resultString = str()
    for option in options:
        value = options[option]
        if value == True or value == False:
            value = 1 if value == True else 0

        resultString += "{}={};".format(option, value)
    return resultString


@decorators.preserveSelection
def exportSkeletalMesh(mainNode, outputPath=None):
    """
    Export the selected rig as an FBX without animation. This is used to make the Skeletal mesh for unreal
    :param mainNode: main node of the rig. This is the highest node or 'rig_root' of the rig.
    :param outputPath: path to save the output file to.

    :return:
    """

    if not cmds.objExists(mainNode):
        raise Exception("The main node {} does not exist in the scene".format(mainNode))

    bind = meta.getMessageConnection("{}.bind".format(mainNode))
    model = meta.getMessageConnection("{}.model".format(mainNode))

    # TODO: add some stuff to build the file path

    # in order to export only the right nodes we need to select them.
    # using the preserve selection decorator will help to ensure we keep the selction we started with
    cmds.select(bind, model)

    # before exporting it we need to setup the export options
    options = OrderedDict(FBXExportSkins=True,
                          FBXExportShapes=True,
                          FBXExportCameras=False,
                          FBXExportSmoothMesh=True,
                          FBXExportSmoothingGroups=True,
                          FBXExportLights=False,
                          FBXExportAnimation=False,
                          FBXExportBakeComplexAnimation=False,
                          FBXExportBakeResampleAll=False,
                          FBXExportConstraints=False,
                          FBXExportInputConnections=False
                          )

    # finally we can do the export. Here we also want to pass in kwargs to allow the user to add any additional options
    cmds.file(outputPath,
              exportSelected=True,
              force=True,
              type="FBX export",
              preserveReferences=True,
              options=formatFBXOptions(options=options))


@decorators.preserveSelection
def exportAnimationClip(mainNode, outputPath=None):
    """
    Export the selected rig as an FBX without animation. This is used to make the Skeletal mesh for unreal
    :param mainNode: main node of the rig. This is the highest node or 'rig_root' of the rig.
    :param outputPath: path to save the output file to.

    :return:
    """

    if not cmds.objExists(mainNode):
        raise Exception("The main node {} does not exist in the scene".format(mainNode))

    bind = meta.getMessageConnection("{}.bind".format(mainNode))
    model = meta.getMessageConnection("{}.model".format(mainNode))

    # TODO: add some stuff to build the file path

    # in order to export only the right nodes we need to select them.
    # using the preserve selection decorator will help to ensure we keep the selction we started with
    cmds.select(bind, model)

    # before exporting it we need to setup the export options
    minFrame = cmds.playbackOptions(q=True, min=True)
    maxFrame = cmds.playbackOptions(q=True, max=True)

    options = OrderedDict(FBXExportSkins=True,
                          FBXExportShapes=True,
                          FBXExportCameras=False,
                          FBXExportSmoothMesh=True,
                          FBXExportSmoothingGroups=True,
                          FBXExportLights=False,
                          FBXExportAnimation=True,
                          FBXExportBakeComplexAnimation=True,
                          FBXExportBakeResampleAll=True,
                          FBXExportBakeComplexStart=int(minFrame),
                          FBXExportBakeComplexEnd=int(maxFrame),
                          FBXExportConstraints=False,
                          )

    # finally we can do the export. Here we also want to pass in kwargs to allow the user to add any additional options
    cmds.file(outputPath,
              exportSelected=True,
              force=True,
              type="FBX export",
              preserveReferences=True,
              options=formatFBXOptions(options=options))


if __name__ == '__main__':
    exportSkeletalMesh("main", outputPath="/Users/masonsmigel/Desktop/test_v01_mesh.fbx")
    # exportAnimationClip("main", outputPath="/Users/masonsmigel/Desktop/test_v005_anim.fbx")
