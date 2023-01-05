#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: merge.py
    author: masonsmigel
    date: 01/2023
    discription: Merge two .rig files together

"""
import os
from rigamajig2.shared import path
from distutils.dir_util import copy_tree
from rigamajig2.maya.builder import constants
from rigamajig2.maya.builder import builder
from rigamajig2.maya.builder import core
from rigamajig2.maya.data import abstract_data

mergableFeilds = [constants.SKELETON_POS,
                  constants.CONTROL_SHAPES,
                  constants.GUIDES,
                  constants.COMPONENTS]


def mergeRigs(rigFile1, rigFile2, rigName, mergedPath, outputSuffix='_rig-deliver', method='game'):
    """
    Merge two rig files into a single rig file. The order of rig files in vital! the first one will be used when there
    are discrepencies!

    The archetype of the first rig file is also the one that will be copied

    For feilds such as blendshapes, skins and SHAPES only both rig files must be set to none OR a Directory,
    individual files cannot be used!

    :param rigFile1: path to the first rig file
    :param rigFile2: path to the second rig file
    :param rigName: filename of the merged rig file
    :param mergedPath: path to the rig enviornment for the output merged rig
    :param method: method which to combine skin clusters. Valid values are 'game' and 'film'.
            - 'game' will overwrite the skinfiles from rigFile1.
                It requires cleanup to combine the two but will result in a single skin cluster per mesh
            - 'film' will use deformation layers to stack deformations from rigFile2 ontop of rigFile1. This will work
                as expected out of the box but cannot be sent to a game engine because it uses stacked skin clusters.

    """

    # remove a suffix from the mergedRig file if one was added.
    rigName = rigName.split(".")[0]

    # for merged rig files the archetype is always built from base
    rigFile = core.newRigEnviornmentFromArchetype(mergedPath, 'base', rigName=rigName)
    rigEnv = os.path.dirname(rigFile)

    rigFileData = abstract_data.AbstractData()
    rigFileData.read(rigFile)

    rigFileDict = rigFileData.getData()

    file1Archetype = builder.Builder.getRigData(rigFile1, constants.BASE_ARCHETYPE)
    file2Archetype = builder.Builder.getRigData(rigFile2, constants.BASE_ARCHETYPE)

    if file1Archetype == file2Archetype:
        rigFileDict[constants.BASE_ARCHETYPE] = file1Archetype
    else:
        rigFileDict[constants.BASE_ARCHETYPE] = [file1Archetype, file2Archetype]

    # setup some important initial data!
    rigFileDict[constants.RIG_NAME] = builder.Builder.getRigData(rigFile1, constants.RIG_NAME)
    rigFileDict[constants.OUTPUT_FILE_SUFFIX] = outputSuffix
    rigFileDict[constants.OUTPUT_RIG_FILE_TYPE] = builder.Builder.getRigData(rigFile1, constants.OUTPUT_RIG_FILE_TYPE)
    rigFileDict[constants.OUTPUT_RIG] = builder.Builder.getRigData(rigFile1, constants.OUTPUT_RIG)

    # now starting from the top we'll start to merge things.

    # merge the model file
    rigFileDict[constants.MODEL_FILE] = mergeModelFile(rigFile1=rigFile1, rigFile2=rigFile2, rigEnv=rigEnv)

    # merge the json files
    rigFileDict[constants.SKELETON_POS] = mergeJsonFile(rigFile1, rigFile2, rigEnv=rigEnv, key=constants.SKELETON_POS)
    rigFileDict[constants.GUIDES] = mergeJsonFile(rigFile1, rigFile2, rigEnv=rigEnv, key=constants.GUIDES)
    rigFileDict[constants.COMPONENTS] = mergeJsonFile(rigFile1, rigFile2, rigEnv=rigEnv, key=constants.COMPONENTS)
    rigFileDict[constants.CONTROL_SHAPES] = mergeJsonFile(rigFile1, rigFile2, rigEnv=rigEnv, key=constants.CONTROL_SHAPES)
    rigFileDict[constants.PSD] = mergeJsonFile(rigFile1, rigFile2, rigEnv=rigEnv, key=constants.PSD)
    rigFileDict[constants.DEFORM_LAYERS] = mergeJsonFile(rigFile1, rigFile2, rigEnv=rigEnv, key=constants.DEFORM_LAYERS)

    # merge the skins and SHAPES
    rigFileDict[constants.SKINS] = mergeSkinWeights(rigFile1, rigFile2, rigEnv=rigEnv, method=method)
    rigFileDict[constants.SHAPES] = mergeContentBased(rigFile1, rigFile2, rigEnv=rigEnv, key=constants.SHAPES)

    # lets merge the script lists.
    copyScripts(rigFile1, rigFile2, rigFile, constants.PRE_SCRIPT)
    copyScripts(rigFile1, rigFile2, rigFile, constants.POST_SCRIPT)
    copyScripts(rigFile1, rigFile2, rigFile, constants.PUB_SCRIPT)

    # finally set all the values back to the rig file and write it out!
    rigFileData.setData(rigFileDict)
    rigFileData.write(rigFile)


def mergeModelFile(rigFile1, rigFile2, rigEnv):
    """
    Merge the model file. This is pretty straightforward, we just need to get the relative path from the new rigFile
    to the model used in rigFile. We check to make sure the two files are the same but it doesnt matter.
    we'll always use the file from rigFile1.
    """

    # get the absolute paths of both models.
    rigFile1Model = builder.Builder.getRigData(rigFile1, constants.MODEL_FILE)
    modelFile1 = os.path.realpath(os.path.join(os.path.dirname(rigFile1), rigFile1Model))

    rigFile2Model = builder.Builder.getRigData(rigFile2, constants.MODEL_FILE)
    modelFile2 = os.path.realpath(os.path.join(os.path.dirname(rigFile2), rigFile2Model))

    # next we can compare the two model files. if theyre different throw a warning. They should match to merge properly!
    if modelFile1 != modelFile2:
        raise Warning("Model files do not match! Defaulting to file from rigFile1")

    relativeModel = os.path.relpath(modelFile1, rigEnv)
    return relativeModel


def mergeJsonFile(rigFile1, rigFile2, rigEnv, key):
    """Merge a two json files. """

    # get the data for rig file 1
    rigFile1Data = abstract_data.AbstractData()
    file1Relative = builder.Builder.getRigData(rigFile1, key)
    if file1Relative:
        file1Absolute = os.path.realpath(os.path.join(os.path.dirname(rigFile1), file1Relative))
        rigFile1Data.read(file1Absolute)

    # get the data for rig file 2
    rigFile2Data = abstract_data.AbstractData()
    file2Relative = builder.Builder.getRigData(rigFile2, key)
    if file2Relative:
        file2Absolute = os.path.realpath(os.path.join(os.path.dirname(rigFile2), file2Relative))
        rigFile2Data.read(file2Absolute)

    # combine the data and write it
    outputData = rigFile1Data + rigFile2Data
    if not file1Relative and not file2Relative:
        return
    if not file1Relative:
        file1Relative = file2Relative

    outputDataPath = os.path.realpath(os.path.join(rigEnv, file1Relative))
    outputData.write(outputDataPath)

    return file1Relative


def mergeSkinWeights(rigFile1, rigFile2, rigEnv, method='game'):
    """
    Do a sloppy merge of the skin weights. The method
    """

    if method == 'game':
        relativePath = mergeContentBased(rigFile1, rigFile2, rigEnv, key=constants.SKINS)

    else:
        raise NotImplementedError("merging with stacked skins has not yet been implemented.")

    return relativePath


def mergeContentBased(rigFile1, rigFile2, rigEnv, key):
    """ Merge types that are content based ie skinweights, blendshapes or SHAPES"""
    # build a skins folder from the first rig file
    relativePath = builder.Builder.getRigData(rigFile1, key)
    destPath = os.path.realpath(os.path.join(rigEnv, relativePath))
    os.makedirs(destPath)

    # copy the contents from file 1
    file1Path = getAbsoultePathFromRigFile(rigFile1, key)
    if file1Path:
        if not path.isDir(file1Path):
            raise RuntimeError("data from {} must be a directory to merge.".format(key))
        copy_tree(file1Path, destPath)

    # next we can copy the skin weights from the second skin file.
    # This will overwrite any files with the same name from rigFile1
    file2Path = getAbsoultePathFromRigFile(rigFile2, key)
    if file2Path:
        if not path.isDir(file2Path):
            raise RuntimeError("data from {} must be a directory to merge.".format(key))
        copy_tree(file2Path, destPath)

    return relativePath


def copyScripts(rigFile1, rigFile2, rigFile, dataKey):
    """
    Copy the scripts
    """
    relativePath = builder.Builder.getRigData(rigFile1, dataKey)
    relativePath = relativePath[0] if relativePath else None
    destPath = os.path.realpath(os.path.join(os.path.dirname(rigFile), relativePath))

    if not os.path.exists(destPath):
        os.makedirs(destPath)

    for fileToMerge in [rigFile1, rigFile2]:
        relativePaths = builder.Builder.getRigData(fileToMerge, dataKey)
        for relativePath in relativePaths:
            absoultePath = os.path.realpath(os.path.join(os.path.dirname(fileToMerge), relativePath))
            copy_tree(absoultePath, destPath)


def getAbsoultePathFromRigFile(rigFile, dataKey):
    """ get the absoulte path from a rig file """
    relativePath = builder.Builder.getRigData(rigFile, dataKey)
    if relativePath:
        absoultePath = os.path.realpath(os.path.join(os.path.dirname(rigFile), relativePath))
    return absoultePath
