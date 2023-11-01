#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: model.py
    author: masonsmigel
    date: 07/2022

"""
# PYTHON
import os

import maya.api.OpenMaya as om
# MAYA
import maya.cmds as cmds

# RIGAMAJIG
import rigamajig2.maya.file as file
import rigamajig2.maya.mesh as mesh
import rigamajig2.maya.meta as meta


def importModel(path=None):
    """
    import the model into the scene.
    :param path: path to model
    :return:
    """
    nodes = list()
    if path and os.path.exists(path):
        nodes = file.import_(path, useNamespace=False)

    # get top level nodes in the skeleton
    if nodes:
        for node in cmds.ls(nodes, l=True, type='transform'):
            if not len(node.split('|')) > 2:
                meta.tag(node, 'model_root')

    # Once we have loaded the model lets frame in on it
    if not om.MGlobal.mayaState():
        cmds.viewFit(all=True)


def getModelGeo():
    """
    Look for all mesh geometry under the nodes tagged as a 'model_root'
    :return:
    """

    modelRoots = meta.getTagged('model_root')

    modelList = list()
    for modelRoot in modelRoots:
        # get a list of all children of the model
        modelChildren = cmds.listRelatives(modelRoot, ad=True, shapes=False, ni=True)

        # filter out any shapes or intermediates then filter out plain transforms
        transformsList = cmds.ls(modelChildren, type="transform")  # filter out any shapes or intermediates
        meshes = [m for m in transformsList if mesh.isMesh(m)]

        # add the meshes list to the model list
        modelList += meshes

    return modelList