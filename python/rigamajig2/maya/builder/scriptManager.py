#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: scripts.py
    author: masonsmigel
    date: 11/2023
    description: 

"""
import os
import pathlib

from rigamajig2.maya.builder import constants
from rigamajig2.maya.builder.core import getRigData, getAvailableArchetypes, findRigFile
from rigamajig2.shared import common, runScript


def validateScriptList(scriptsList=None):
    """
    Validate the script list.
    This will filter all the items in the script into a script type.
    If the item is a directory then get scripts within the directory.

    :param scriptsList: list of directories and/or scripts to check and add to the list
    :return:
    """
    resultList = list()

    scriptsList = common.toList(scriptsList)

    # add all scripts and directories in the script list to the builder
    for filePath in scriptsList:
        filePath = pathlib.Path(filePath)
        if not filePath.exists():
            continue

        if filePath.is_file():
            resultList.insert(0, str(filePath))

        if filePath.is_dir():
            for script in runScript.findScripts(str(filePath)):
                resultList.insert(0, script)

    return resultList


def runAllScripts(scripts=None):
    """
    Run pre scripts. You can add scripts by path, but the main use is through the PRE SCRIPT path
    :param scripts: path to scripts to run
    """
    if scripts is None:
        scripts = list()

    fileScripts = validateScriptList(scripts)

    fileScripts.reverse()
    for script in fileScripts:
        runScript.runScript(script)


class GetCompleteScriptList(object):
    """
    This class will get a list of all scripts for a given rig file and return them in a dictionary
    """

    scriptDict = dict()
    scriptList = list()
    fileRecursionDict = dict()

    @classmethod
    def getScriptList(cls, rigFile, scriptType=None):
        """
        This function will get a list of all scripts for a given rigfile including any upstream archetype parents.

        :param rigFile: rig file to get scripts for
        :param scriptType: key of scripts to get. Typical values are pre_script, post_script or pub_script.
        :return: list of scripts
        """
        cls.scriptDict = dict()
        cls.scriptList = list()

        cls.findScripts(rigFile=rigFile, scriptType=scriptType)

        return cls.scriptDict

    @classmethod
    def findScripts(cls, rigFile, scriptType, recursionLevel=0):
        """
        :param rigFile: directories at the current rig file level of the rig
        :param scriptType: key of scripts to get. Typical values are pre_script, post_script or pub_script.
        :param recursionLevel: the recursion level of the script to store as the dictionary key.
        """
        scriptType = scriptType or constants.PRE_SCRIPT
        localScriptPaths = getRigData(rigFile, scriptType)
        rigEnvironmentPath = os.path.abspath(os.path.join(rigFile, "../"))

        if recursionLevel not in cls.scriptDict:
            cls.scriptDict[recursionLevel] = []

        # for each item in the script path append the scripts
        for localScriptPath in localScriptPaths:
            fullScriptPath = os.path.join(rigEnvironmentPath, localScriptPath)
            builderScripts = validateScriptList(fullScriptPath)

            # make a temp script list
            _scriptList = list()

            for script in builderScripts:
                if script not in cls.scriptList:
                    _scriptList.insert(0, script)
                    cls.scriptList.insert(0, script)

            cls.scriptDict[recursionLevel].extend(_scriptList)

        # now we can look at the parent archetypes and iterate through them too.
        baseArchetype = getRigData(rigFile, constants.BASE_ARCHETYPE)
        archetypeList = common.toList(baseArchetype)
        for baseArchetype in archetypeList:
            if baseArchetype and baseArchetype in getAvailableArchetypes():
                archetypePath = os.sep.join([common.ARCHETYPES_PATH, baseArchetype])
                archetypeRigFile = findRigFile(archetypePath)

                cls.findScripts(
                    archetypeRigFile,
                    scriptType=scriptType,
                    recursionLevel=recursionLevel + 1,
                )
