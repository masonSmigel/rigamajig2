#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: loadPlugins.py.py
    author: masonsmigel
    date: 11/2023
    description: load required plugins

"""
import maya.cmds as cmds

REQUIRED_PLUGINS = ["quatNodes", "matrixNodes"]


def loadRequiredPlugins():
    """
    loadSettings required plugins
    NOTE: There are plugins REQUIRED for rigamajig such as matrix and quat nodes.
          loading other plug-ins needed in production should be added into a pre-script file
    """
    loadedPlugins = cmds.pluginInfo(query=True, listPlugins=True)

    for plugin in REQUIRED_PLUGINS:
        if plugin not in loadedPlugins:
            cmds.loadPlugin(plugin)

loadRequiredPlugins()