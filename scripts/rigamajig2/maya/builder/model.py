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

# MAYA
import maya.cmds as cmds

# RIGAMAJIG
import rigamajig2.maya.file as file
import rigamajig2.maya.meta as meta


def importModel(path=None):
    """
    import the model into the scene.
    :param path: path to model
    :return:
    """
    nodes = list()
    if path and os.path.exists(path):
        nodes = file.import_(path, namespace=None)

    # get top level nodes in the skeleton
    if nodes:
        for node in cmds.ls(nodes, l=True, type='transform'):
            if not len(node.split('|')) > 2:
                meta.tag(node, 'model_root')
