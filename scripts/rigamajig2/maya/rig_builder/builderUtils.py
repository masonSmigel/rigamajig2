#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: scripts.py
    author: masonsmigel
    date: 07/2022
    discription: This module contains utilities for the builder

"""
# PYTHON
import os
import shutil
import logging
import inspect

# MAYA
import maya.cmds as cmds

# RIGAMAJIG
from rigamajig2.shared.logger import Logger
from rigamajig2.shared import common
from rigamajig2.shared import path as rig_path
from rigamajig2.shared import runScript
from rigamajig2.maya.data import abstract_data as abstract_data

logger = logging.getLogger(__name__)


def _lookForComponents(path, excludedFolders, excludedFiles):
    res = os.listdir(path)
    toReturn = list()
    for r in res:
        full_path = os.path.join(path, r)
        if r not in excludedFolders and os.path.isdir(path + '/' + r) == True:
            _lookForComponents(full_path, excludedFolders, excludedFiles)
        if r.find('.py') != -1 and r.find('.pyc') == -1 and r not in excludedFiles:
            if r.find('reload') == -1:

                # find classes in the file path
                module_file = r.split('.')[0]
                modulesPath = 'rigamajig2.maya.cmpts.{}'
                module_name = modulesPath.format(module_file)
                module_object = __import__(module_name, globals(), locals(), ["*"], 0)
                for cls in inspect.getmembers(module_object, inspect.isclass):
                    toReturn.append("{}.{}".format(module_file, cls[0]))

    return toReturn


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


def get_available_archetypes():
    """
    get a list of avaible archetypes. Archetypes are defined as a folder containng a .rig file.
    :return: list of archetypes
    """
    archetype_list = list()

    path_contents = os.listdir(common.ARCHETYPES_PATH)
    for archetype in path_contents:
        archetype_path = os.path.join(common.ARCHETYPES_PATH, archetype)
        if archetype.startswith("."):
            continue
        if find_rig_file(archetype_path):
            archetype_list.append(archetype)
    return archetype_list


def find_rig_file(path):
    """ find a rig file within the path"""
    if rig_path.isFile(path):
        return False

    path_contents = os.listdir(path)
    for f in path_contents:
        if f.startswith("."):
            continue
        if not rig_path.isDir(path):
            continue
        file_name, file_ext = os.path.splitext(os.path.join(path, f))
        if not file_ext == '.rig':
            continue
        return os.path.join(path, f)
    return False


def new_rigenv_from_archetype(new_env, archetype, rig_name=None):
    """
    Create a new rig envirnment from and archetype
    :param new_env: target driectory for the new rig enviornment
    :param rig_name: name of the new rig enviornment
    :param archetype: archetype to copy
    :return:
    """
    if archetype not in get_available_archetypes():
        raise RuntimeError("{} is not a valid archetype".format(archetype))

    archetype_path = os.path.join(common.ARCHETYPES_PATH, archetype)
    return create_rig_env(src_env=archetype_path, tgt_env=new_env, rig_name=rig_name)


def create_rig_env(src_env, tgt_env, rig_name):
    """
    create a new rig enviornment
    :param src_env: source rig enviornment
    :param tgt_env: target rig direction
    :param rig_name: new name of the rig enviornment and .rig file
    :return:
    """

    tgt_env_path = os.path.join(tgt_env, rig_name)
    shutil.copytree(src_env, tgt_env_path)

    src_rig_file = find_rig_file(tgt_env_path)
    rig_file = os.path.join(tgt_env_path, "{}.rig".format(rig_name))

    # rename the .rig file and the rig_name within the .rig file
    os.rename(src_rig_file, rig_file)

    data = abstract_data.AbstractData()
    data.read(rig_file)

    new_data = data.getData()
    new_data['rig_name'] = rig_name
    data.setData(new_data)
    data.write(rig_file)

    logger.info("New rig environment created: {}".format(tgt_env_path))
    return os.path.join(tgt_env_path, rig_file)
