#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: guides.py
    author: masonsmigel
    date: 07/2022
    discription:

"""
# PYTHON
import os

# MAYA
import maya.cmds as cmds

# RIGAMJIG
import rigamajig2.shared.common as common
import rigamajig2.maya.data.joint_data as joint_data
import rigamajig2.maya.data.guide_data as guide_data
import rigamajig2.maya.meta as meta
import rigamajig2.maya.joint as joint


def load_joints(path=None):
    """
    Load all joints for the builder
    :param path:
    :return:
    """
    if not os.path.exists(path):
        return

    data_obj = joint_data.JointData()
    data_obj.read(path)
    data_obj.applyData(data_obj.getKeys())

    # tag all bind joints
    for jnt in cmds.ls("*_bind", type='joint'):
        meta.tag(jnt, "bind")

    data_obj.getData().keys()
    for node in cmds.ls(data_obj.getKeys(), l=True):
        # add the joint orient to all joints in the file.
        joint.addJointOrientToChannelBox(node)

        # find joints without a parent and make them a root
        if not len(node.split('|')) > 2:
            meta.tag(node, 'skeleton_root')


def save_joints(path=None):
    """save the joints"""

    # find all skeleton roots and get the positions of their children
    skeleton_roots = common.toList(meta.getTagged('skeleton_root'))
    if len(skeleton_roots) > 0:
        data_obj = joint_data.JointData()
        for root in skeleton_roots:
            data_obj.gatherData(root)
            data_obj.gatherDataIterate(cmds.listRelatives(root, allDescendents=True, type='joint'))
        data_obj.write(path)
    else:
        raise RuntimeError("the root_hrc joint {} does not exists".format(skeleton_roots))


def load_guide_data(path=None):
    """
    Load guide data
    :return:
    """
    if not os.path.exists(path):
        return

    try:
        nd = guide_data.GuideData()
        nd.read(path)
        nd.applyData(nodes=nd.getKeys())
        return True
    except:
        return False


def save_guide_data(path=None):
    """
    Save guides data
    :param path:
    :return:
    """
    nd = guide_data.GuideData()
    nd.gatherDataIterate(meta.getTagged("guide"))
    nd.write(path)
