#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: SHAPES_data.py
    author: masonsmigel
    date: 03/2023
    discription: 

"""
import os.path
from collections import OrderedDict
import maya.cmds as cmds
import maya.mel as mel
import linecache

from rigamajig2.shared import common
from rigamajig2.shared import path as rig_path
import rigamajig2.maya.data.maya_data as maya_data
from rigamajig2.maya import blendshape
from rigamajig2.maya import mesh

SUBFOLDER_PATH = "SHAPES"


class SHAPESData(maya_data.MayaData):
    """ Class to store maya data"""

    def __init__(self):
        super(SHAPESData, self).__init__()

        # if we could loaded SHAPES then source the required mel scripts.
        # SHAPES has a built in proc to do this so we can just source the main file and call those procs.
        if self.__validateSHAPES():
            mel.eval("source SHAPES;"
                     "shapesSourceScripts;"
                     "shapesLoadScripts;")

        self.filepath = None

    def __validateSHAPES(self):
        """validate that the SHAPES plugin is available and loaded"""
        SHAPESLoaded = False
        try:
            loadedPlugins = cmds.pluginInfo(query=True, listPlugins=True)
            if "SHAPESTools" not in loadedPlugins:
                cmds.loadPlugin("SHAPESTools")
            if cmds.pluginInfo("SHAPESTools", q=True, r=True):
                SHAPESLoaded = True
        except:
            pass

        return SHAPESLoaded

    def gatherData(self, node, useDeltas=True):
        """
        This method will gather data from the maya node passed as an argument.
        It stores the data on the self._data attribute

        :param node: blendshape node to gather data from
        :type node: str
        :param useDeltas: If True then load the deltas back. Otherwise exact shapes will be used as blendshape targets.
        :type useDeltas: bool
        """

        if not self.__validateSHAPES():
            cmds.warning(
                "SHAPES plugin is not available. SHAPES data can still be loaded, but you cannot save new data")
            return

        if cmds.nodeType(node) == 'transform':
            blendshapeNodes = blendshape.getBlendshapeNodes(node)
        else:
            blendshapeNodes = [node]

        for blendshapeNode in blendshapeNodes:
            super(SHAPESData, self).gatherData(blendshapeNode)

            # TODO: add a warning about blendshapes connected to nurbs or other geometry types than mesh.
            shape = blendshape.getBaseGeometry(blendshapeNode)
            mesh = common.getFirstIndex(cmds.listRelatives(shape, type='transform', p=True))

            # now we need to save the data we need.
            self._data[blendshapeNode]['mesh'] = mesh
            self._data[blendshapeNode]['setupFile'] = None
            self._data[blendshapeNode]['useDeltas'] = useDeltas
            self._data[blendshapeNode]['deltasFile'] = None

    def applyData(self, nodes, attributes=None, autoLocalize=True, rebuild=True):
        """
        Rebuild the SHAPES data from the given nodes.

        :param nodes: Array of nodes to apply the data to
        :param attributes: Array of attributes you want to apply the data to
        :param autoLocalize: SHAPES has some data that is hard coded into the setup.mel file. autoLocalize will try to
                            localize the data upon building.
        :param rebuild: if True this will rebuild any existing setup that exists
        :return:
        """

        if not self.filepath:
            raise RuntimeError(
                "SHAPES data needs to be written or read before you can load it. Please write or read a file")

        baseFolder = os.path.dirname(self.filepath)
        for blendshapeNode in nodes:

            # check if the blendshape node exists and delete it if we want to rebuild
            if cmds.objExists(blendshapeNode) and rebuild:
                cmds.delete(blendshapeNode)

            # get the setup path from the shapes file
            setupPath = os.sep.join([baseFolder, self._data[blendshapeNode]['setupFile']])

            if autoLocalize:
                # create a duplicate with localized paths then rebuild from that file
                tmpLocalizedFile = localizeSHAPESFile(setupPath)
                rebuildSetup(tmpLocalizedFile)

                # delete the localized version
                os.remove(tmpLocalizedFile)

            else:
                rebuildSetup(setupPath)

            # delete the temp file

            if self._data[blendshapeNode]['useDeltas']:
                deltasPath = os.sep.join([baseFolder, self._data[blendshapeNode]['deltasFile']])
                importBlendshapeDeltas(blendshapeNode, deltasPath)

    def write(self, filepath, createDirectory=True):
        """
        This will write the dictionary information to disc in .json format.

        We need to overwrite the base write method to add in the writing of external files created with SHAPES.
        This includes the shapes complete export and the deltas.
        :param filepath: The path to the file you wish to write.
        :type: str
        :param createDirectory: Create file path if needed
        :type createDirectory: bool
        :return:
        """

        baseFolder = os.path.dirname(filepath)

        for blendshapeNode in self.getKeys():
            # for each blendshape export its setup and a optionally a delta's file
            setupPath = os.sep.join([baseFolder, SUBFOLDER_PATH])
            exportCompleteSetup(mesh=self._data[blendshapeNode]['mesh'], filePath=setupPath)

            # set the setup file data to be the path to the mel file for the blendshape!
            filename = "{}.mel".format(blendshapeNode)
            print setupPath, filename
            setupRelativePath = os.path.relpath(os.path.join(setupPath, filename), baseFolder)

            self._data[blendshapeNode]['setupFile'] = setupRelativePath

            # export the deltas too
            deltasPath = os.sep.join([baseFolder, SUBFOLDER_PATH, "{}_deltas.json".format(blendshapeNode)])
            exportBlendShapeDeltas(blendshapeNode, deltasPath)

            # set the file path in the json file
            relativeDeltasPath = os.path.relpath(deltasPath, baseFolder)
            self._data[blendshapeNode]['deltasFile'] = relativeDeltasPath

        super(SHAPESData, self).write(filepath=filepath)
        self.filepath = filepath

    def read(self, filepath):
        """
        This will read a .json file and return the data in the file.

        :param filepath: the path of the file to read
        :type filepath: str
        :return: Data from the filepath given.
        :rtype: dict
        """
        super(SHAPESData, self).read(filepath)
        self.filepath = filepath


# ----------------------------------------------------------------------
# Blend shape setup export and import.
# ----------------------------------------------------------------------

def exportCompleteSetup(mesh, filePath, rebuild=False):
    """Exports all blend shape nodes from the given mesh with their
    respective setup.
    The rebuild of the setup is optional.

    :param mesh: The name of the mesh to process.
    :type mesh: str
    :param filePath: The path to export to.
    :type filePath: str
    :param rebuild: True, if the setup should be rebuilt.
    :type rebuild: bool
    """
    # query the active selection
    activeSelection = cmds.ls(sl=True)

    # Store the preference settings.
    options = {}
    options["SHAPESFileType"] = cmds.optionVar(query="SHAPESFileType")
    options["SHAPESUseCustomDataPath"] = cmds.optionVar(query="SHAPESUseCustomDataPath")
    options["SHAPESCustomDataPath"] = cmds.optionVar(query="SHAPESCustomDataPath")
    options["SHAPESUseCustomNodeDataExportPath"] = cmds.optionVar(query="SHAPESUseCustomNodeDataExportPath")
    options["SHAPESCustomNodeDataExportPath"] = cmds.optionVar(query="SHAPESCustomNodeDataExportPath")
    options["SHAPESExportOptions"] = cmds.optionVar(query="SHAPESExportOptions")

    # Set the preferences for the export.
    cmds.optionVar(intValue=("SHAPESFileType", 0))
    cmds.optionVar(intValue=("SHAPESUseCustomDataPath", 1))
    cmds.optionVar(stringValue=("SHAPESCustomDataPath", filePath))
    cmds.optionVar(intValue=("SHAPESUseCustomNodeDataExportPath", 0))
    cmds.optionVar(stringValue=("SHAPESCustomNodeDataExportPath", ""))
    # Options: export only, all targets, maya ASCII.
    cmds.optionVar(stringValue=("SHAPESExportOptions", "1,1,1"))

    # Make sure that the export path is existing.
    filePath = mel.eval("shapesUtil_getExportPath(\"\", 1)")

    # Load the SHAPES UI.
    mel.eval("SHAPES")
    # Load the selected mesh.
    cmds.select(mesh, replace=True)
    mel.eval("shapesMain_getMeshSelection 1")
    # Get the blend shape node.
    bsNode = mel.eval("string $temp = $gShapes_bsNode")
    # Get all blend shape nodes from the mesh.
    nodeList = blendshape.getBlendshapeNodes(mesh)

    for node in nodeList:
        cmds.optionMenu("shpUI_bsOption", edit=True, value=node)
        mel.eval("shapesMain_updateSelectedBsNode")
        mel.eval("shapesUI_buildExportUI 1")
        mel.eval("shapesUtil_exportShapeSetup 1 \"{}\" \"\"".format(filePath))
        if rebuild:
            mel.eval("shapesAction_deleteBlendShapeNode")

    # Set the preferences back.
    cmds.optionVar(intValue=("SHAPESFileType", options["SHAPESFileType"]))
    cmds.optionVar(intValue=("SHAPESUseCustomDataPath", options["SHAPESUseCustomDataPath"]))
    cmds.optionVar(stringValue=("SHAPESCustomDataPath", options["SHAPESCustomDataPath"]))
    cmds.optionVar(intValue=("SHAPESUseCustomNodeDataExportPath", options["SHAPESUseCustomNodeDataExportPath"]))
    cmds.optionVar(stringValue=("SHAPESCustomNodeDataExportPath", options["SHAPESCustomNodeDataExportPath"]))
    cmds.optionVar(stringValue=("SHAPESExportOptions", options["SHAPESExportOptions"]))

    # Rebuild the setup.
    if rebuild:
        for node in nodeList:
            rebuildSetup("{}/{}.mel".format(filePath, node))
        cmds.select(mesh, replace=True)
        mel.eval("shapesMain_getMeshSelection 1")

    # reselect the selected nodes
    cmds.select(activeSelection, r=True)


def rebuildSetup(filePath):
    """Rebuild the exported blend shape setup from the given file.

    :param filePath: The file path if the blend shape setup.
    :type filePath: str
    """
    cleanPath = rig_path.cleanPath(filePath)

    # format the path for mel
    melFormmatedPath = cleanPath.replace("\\", "/")
    mel.eval('source "{path}";'.format(path=melFormmatedPath))
    # mel.eval('shapesUtil_performImportShapeSetup "{}"'.format(melFormmatedPath))


# ----------------------------------------------------------------------
# Blend shape deltas export to a json file.
# ----------------------------------------------------------------------


def exportBlendShapeDeltas(bsNode, filePath):
    """
    Export the blend shape deltas to the given json file.

    :param str bsNode: The name of the blend shape node.
    :param str filePath: The full path of the json file to export the deltas
                     to, including the file extension.

    :return: True, if the export was successful.
    :rtype: bool
    """
    # Store the current blend shape node.
    temp = mel.eval("string $temp = $gShapes_bsNode")

    # Set the blend shape node for getting the targets and ids.
    mel.eval('$gShapes_bsNode = "{}"'.format(bsNode))
    # Get all target names.
    names = mel.eval("shapesData_getShapeList()")
    items = []
    for name in names:
        # Get index for each target.
        ids = mel.eval('shapesData_getShapeIds(1, {{"{}"}})'.format(name))
        items.append("-index {} -channelName {}".format(ids[0], name))

    # Build the command string.
    cmd = ["br_blendShapeExportData -delta -fileName"]
    cmd.append('"{}"'.format(filePath))
    cmd.append(" ".join(items))
    cmd.append(bsNode)

    # Execute the command.
    result = mel.eval(" ".join(cmd))

    # Restore the previous the blend shape node.
    mel.eval('$gShapes_bsNode = "{}"'.format(temp))

    # do a print with the br message to keep stuff consistant
    mel.eval('br_displayMessage -info ("Exported Deltas for \'{}\' to \'{}\' ");'.format(temp, filePath))
    return bool(result)


def importBlendshapeDeltas(bsNode, filePath):
    """
    Import the blendshape deltas
    """
    # once again mel can be silly so reformat the path to have properly facing slashes
    melFormatedFilePath = filePath.replace("\\", "/")
    mel.eval('br_blendShapeImportData -delta -fileName "{filePath}" "{blendshape}";'.format(filePath=melFormatedFilePath,
                                                                                            blendshape=bsNode))

    # do a print with the br message to keep stuff consistant
    mel.eval('br_displayMessage -info ("Imported Deltas to \'{}\' from \'{}\' ");'.format(bsNode, melFormatedFilePath))


def localizeSHAPESFile(melFile):
    """
    SHAPES setup.mel files have hard coded paths to the shapes and data files used within them.
    This can be useful in some situations but for rigamajig2 it makes it hard to transfer between users.
    To fix this we can update the paths based on the mel file which we know the location of.

    From that we can replace out the lines that are hardcoded at runtime, creating a duplicate with proper pathing.
    Once the setup is imported we can delete the temp file that has the 'proper' paths

    :param melFile: path to the mel file with paths to localize
    :type melFile: string

    :return: path to the new mel file we create
    :rtype: string
    """
    baseDirectory = os.path.dirname(melFile)
    tmpMelFilename = "tmp_{}_localized.mel".format(os.path.basename(melFile).split(".")[0])
    outputFile = os.path.join(baseDirectory, tmpMelFilename)

    lookup1 = "// import shapes"
    lookup2 = "// import data node"

    codeToReplaceWith = 'file -i -type "mayaBinary" -mnc 0 -pr "{}";\n'

    # read the existing contents into lines
    with open(melFile) as f:
        sourceLines = f.readlines()

    for lookup in [lookup1, lookup2]:
        f = open(melFile, 'r')
        line_num = 0

        # find the line above the line we want to replace.
        # Since everything is commented nicely we can easily find the right string.
        setupPathLine = 0
        for line in f.readlines():
            line_num += 1
            if line.find(lookup) >= 0:
                setupPathLine = line_num + 1

        # now we need to get the correct line and read only that line
        problemLine = linecache.getline(melFile, setupPathLine)

        # now we can get the filepath from it and get the file name
        problemFilePath = problemLine.rsplit('"', 2)[1]
        fileName = os.path.basename(problemFilePath)
        newFilePath = os.path.join(baseDirectory, fileName)

        # fix the path because mel likes to mess up the paths
        melFormmatedPath = newFilePath.replace("\\", "//")

        # build a new line of code based on the data we plug in
        newLine = codeToReplaceWith.format(melFormmatedPath)

        # set the data in the lines we setup before
        sourceLines[setupPathLine - 1] = newLine

    # write out the new lines
    outFileObj = open(outputFile, "w")
    outFileObj.writelines(sourceLines)
    outFileObj.close()

    return outputFile


if __name__ == '__main__':
    d = SHAPESData()

    d.gatherData('body_hi')

    print d.getData()
    print d.write("/Users/masonsmigel/Desktop/SHAPES_WRITE_TEST/test.json")
