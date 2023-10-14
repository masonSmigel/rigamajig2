#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: clean.py
    author: masonsmigel
    date: 01/2021
    discription: functions to clean up scenes
"""
# PYTHON
import logging

# MAYA
import maya.mel as mel
from maya import cmds as cmds

from rigamajig2.maya import mesh
from rigamajig2.shared import common as common

EVIL_METHOD_NAMES = ['DCF_updateViewportList', 'CgAbBlastPanelOptChangeCallback', 'onModelChange3dc']

logger = logging.getLogger(__name__)


def cleanNodes():
    """
    Clean up unused nodes
    """
    # source the new MLdeleteUnused to solve a bug deleting the default aiStandard shader in Maya2020
    ovMLdeleteUnusedPath = '/'.join(__file__.split('/')[:-1]) + '/MLdeleteUnused.mel'
    mel.eval('source "{}"'.format(ovMLdeleteUnusedPath))

    mel.eval("MLdeleteUnused")
    nodes = cmds.ls(typ=['groupId', 'nodeGraphEditorInfo', 'nodeGraphEditorBookmarkInfo', 'unknown'])
    if nodes:
        for node in nodes:
            nodeType = cmds.nodeType(node)
            isConnected = cmds.listHistory(node, f=True, il=True)
            if ("GraphEditor" in nodeType) or ("unknown" in nodeType) or not isConnected:
                try:
                    cmds.lockNode(node, l=False)
                    cmds.delete('node')
                    logger.info("Cleaned Node: '{}'".format(node))
                except:
                    pass


def cleanPlugins():
    """
    Clean unknown plugins
    """
    plugins = cmds.unknownPlugin(q=True, l=True)
    if plugins:
        for plugin in plugins:
            try:
                cmds.unknownPlugin(plugin, r=True)
                logger.info("Cleaned Plugin: '{}'".format(plugin))
            except:
                pass


def cleanScriptNodes(excludedScriptNodes=None, excludePrefix='rigamajig2'):
    """
    Clean all scriptnodes in the scene

    :param list excludedScriptNodes: list of script nodes to be kept
    :param str excludePrefix: prefix used to filter script nodes. All nodes with the prefix are kept.
    """
    excludedScriptNodes = excludedScriptNodes or list()

    allScriptNodes = cmds.ls(type='script')
    for scriptNode in allScriptNodes:
        if scriptNode.startswith(excludePrefix):
            continue
        if scriptNode in excludedScriptNodes:
            continue

        cmds.delete(scriptNode)
        logger.info("Cleaned Script Node: '{}'".format(scriptNode))


def cleanRougePanels(panels=None):
    """
    cleanup rouge procedures from all modelPanels
    It will remove errors like:
        // Error: line 1: Cannot find procedure "CgAbBlastPanelOptChangeCallback". //
        // Error: line 1: Cannot find procedure "DCF_updateViewportList". //
    """
    panels = panels or list()

    if not isinstance(panels, (list, tuple)):
        panels = [panels]

    evilMethodNodes = EVIL_METHOD_NAMES + panels
    capitalEvilMethodNames = [name.upper() for name in evilMethodNodes]
    modelPanelLabel = mel.eval('localizedPanelLabel("ModelPanel")')
    processedPanelNames = []
    panelName = cmds.sceneUIReplacement(getNextPanel=('modelPanel', modelPanelLabel))
    while panelName and panelName not in processedPanelNames:
        editorChangedValue = cmds.modelEditor(panelName, query=True, editorChanged=True)
        parts = editorChangedValue.split(';')
        newParts = []
        changed = False
        for part in parts:
            for evilMethodName in capitalEvilMethodNames:
                if evilMethodName in part.upper():
                    changed = True
                    logger.info("removed callback '{}' from pannel '{}'".format(part, panelName))
                    break
            else:
                newParts.append(part)
        if changed:
            cmds.modelEditor(panelName, edit=True, editorChanged=';'.join(newParts))
        processedPanelNames.append(panelName)
        panelName = cmds.sceneUIReplacement(getNextPanel=('modelPanel', modelPanelLabel)) or None


def cleanScene():
    """
    Cleanup maya scene.

    This will run cleanNodes(), cleanPlugins() and cleanRougePanels()
    """
    print('\n{}\n \tCLEAN MAYA SCENE'.format('-' * 80))

    print('{}\n\tClean Nodes: '.format('-' * 80))
    cleanNodes()

    print('{}\n\tClean Plugins: '.format('-' * 80))
    cleanPlugins()

    print('{}\n\tClean RougePanels: '.format('-' * 80))
    cleanRougePanels()
    print('-' * 80)


def cleanShapes(nodes):
    """
    Cleanup a shape nodes. removes all intermediate shapes on the given nodes

    :param list nodes: a list of nodes to clean
    """
    nodes = common.toList(nodes)
    for node in nodes:
        if cmds.nodeType(node) in ['nurbsSurface', 'mesh', 'nurbsCurve']:
            node = cmds.listRelatives(node, p=True)
        shapes = cmds.listRelatives(node, s=True, ni=False, pa=True) or []

        if len(shapes) == 1:
            return shapes[0]
        else:
            intermidiateShapes = [x for x in shapes if cmds.getAttr('{}.intermediateObject'.format(x))]
            if intermidiateShapes:
                cmds.delete(intermidiateShapes)
                logger.info("Deleted Intermeidate Shapes: {}".format(intermidiateShapes))


def cleanModel(nodes=None):
    """
    Clean up a model. This is especially useful to prep a model for rigging.
    It will:
    - delete the construction history
    - freeze the transformations
    - set the mesh pivot to the origin
    - clean the mesh shapes. (delete intermediete shapes)

    :param nodes: meshes to clean
    """
    if not nodes:
        nodes = cmds.ls(sl=True)
    nodes = common.toList(nodes)

    for node in nodes:
        cmds.delete(node, ch=True)
        cmds.makeIdentity(node, apply=True, t=True, r=True, s=True, n=0, pn=1)
        cmds.xform(node, a=True, ws=True, rp=(0, 0, 0), sp=(0, 0, 0))
        if mesh.isMesh(node):
            cleanShapes(node)
            logger.info('Cleaned Mesh: {}'.format(node))


def cleanColorSets(meshes):
    """
    Remove all color set and vertex color data from a model. Theese can appear from things like transfering UVs or
    using sculptiing tools.
    """
    for mesh in meshes:
        colorSets = cmds.polyColorSet(mesh, q=True, allColorSets=True) or list()
        for colorSet in colorSets:
            cmds.polyColorSet(mesh, delete=True, colorSet=colorSet)
            logger.info("Deleted colorSet: {}".format(colorSet))
