#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: scripts.py
    author: masonsmigel
    date: 07/2022
    discription: 

"""
# PYTHON
import logging

# MAYA
import maya.cmds as cmds

# RIGAMAJIG
import rigamajig2.shared.path as rig_path
import rigamajig2.shared.runScript as runScript
import rigamajig2.shared.common as common

logger = logging.getLogger(__name__)


def load_required_plugins():
    """
    loadSettings required plugins
    NOTE: There are plugins REQUIRED for rigamajig such as matrix and quat nodes.
          loading other plug-ins needed in production should be added into a pre-script file
    """
    loaded_plugins = cmds.pluginInfo(query=True, listPlugins=True)

    for plugin in common.REQUIRED_PLUGINS:
        if plugin not in loaded_plugins:
            cmds.loadPlugin(plugin)


def validate_script_list(scripts_list=None):
    res_list = list()

    scripts_list = common.toList(scripts_list)

    for item in scripts_list:
        if not item:
            continue

        if rig_path.isFile(item):
            res_list.append(item)

        if rig_path.isDir(item):
            for script in runScript.find_scripts(item):
                res_list.append(script)
    return res_list


def runAllScripts(scripts=[]):
    """
    Run pre scripts. You can add scripts by path, but the main use is through the PRE SCRIPT path
    :param scripts: path to scripts to run
    """
    file_scripts = validate_script_list(scripts)
    for script in file_scripts:
        runScript.run_script(script)
