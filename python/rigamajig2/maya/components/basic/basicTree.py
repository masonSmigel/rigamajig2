#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: basicHierarchy.py
    author: masonsmigel
    date: 12/2022
    description: The basic Tree is a chain of FK Controls built with the same parent hierarchy as the input joints

"""
from collections import OrderedDict

import maya.cmds as cmds

from rigamajig2.maya import joint
from rigamajig2.maya import transform
from rigamajig2.maya.components import base
from rigamajig2.maya.rig import control
from rigamajig2.shared import common


class BasicTree(base.BaseComponent):
    """
    Basic Tree component.

    The basic tree component creates an FK control for each input joint and creates a matching hierarchy for
    the controls. Controls will match the orientation of the input joints.
    """

    VERSION_MAJOR = 1
    VERSION_MINOR = 1
    VERSION_PATCH = 0

    version_info = (VERSION_MAJOR, VERSION_MINOR, VERSION_PATCH)
    version = "%i.%i.%i" % version_info
    __version__ = version

    UI_COLOR = (208, 132, 67)

    def __init__(self, name, input, size=1, rigParent=str(), componentTag=None):
        """
        :param name: Component name. To add a side use a side token
        :param input: Single input joint, all joints below it will be added to the tree
        :param size:  Default size of the controls.
        :param rigParent:  Connect the component to a rigParent.
        :param controlShape: Control shape to apply. Default: "cube"
        :param trsGrp: add a trs group
        :param sdkGrp: add a sdk group
        :param skipJoints: List of joints to skip from adding a control to. They must be an end joint.
        """
        super(BasicTree, self).__init__(
            name=name, input=input, size=size, rigParent=rigParent, componentTag=componentTag
        )

        self.side = common.getSide(name)

        self.controlShape = "sphere"
        self.addTrs = False
        self.addSdk = False
        self.skipJoints = []

        self.defineParameter(parameter="controlShape", value=self.controlShape, dataType="string")
        self.defineParameter(parameter="addTrs", value=self.addTrs, dataType="bool")
        self.defineParameter(parameter="addSdk", value=self.addSdk, dataType="bool")
        self.defineParameter(parameter="skipJoints", value=self.skipJoints, dataType="list")

    def _initialHierarchy(self):
        """build the initial hierarchy"""
        super(BasicTree, self)._initialHierarchy()

        # create a dictionary of the parents for the component
        self.hierarchyDict = OrderedDict()
        childJoints = cmds.listRelatives(self.input[0], allDescendents=True, type="joint")
        allJoints = [self.input[0]] + childJoints
        for i in range(len(allJoints)):
            jointDict = OrderedDict()
            jnt = allJoints[i]

            if jnt in self.skipJoints and joint.isEndJoint(jnt):
                continue

            if i == 0:
                parentJnt = None
            else:
                parentJnt = cmds.listRelatives(jnt, parent=True, type="joint")

            jointDict["parent"] = parentJnt[0] if parentJnt else None
            self.hierarchyDict[jnt] = jointDict

        # create the controls for the joints
        for jnt, data in self.hierarchyDict.items():
            ctl = control.createAtObject(
                name=jnt.rsplit("_", 1)[0],
                shape=self.controlShape,
                orig=True,
                trs=self.addTrs,
                sdk=self.addSdk,
                size=self.size,
                xformObj=jnt,
                shapeAim="x",
            )
            self.hierarchyDict[jnt]["control"] = ctl

        # now loop through all the items and parent the controls properly
        for jnt in list(self.hierarchyDict.keys()):
            parentJoint = self.hierarchyDict[jnt]["parent"]
            ctl = self.hierarchyDict[jnt]["control"]
            if parentJoint:
                parentControl = self.hierarchyDict[parentJoint]["control"]
                parent = parentControl.name
            else:
                parent = self.controlHierarchy

            cmds.parent(ctl.orig, parent)

    def _rigSetup(self):
        """"""
        # connect each item to the associated joint
        for jnt, data in self.hierarchyDict.items():
            ctl = data["control"]

            joint.connectChains([ctl.name], jnt)

    def _connect(self):
        """Create the connection"""
        # connect the rig to is rigParent
        if cmds.objExists(self.rigParent):
            firstKey, firstItem = list(self.hierarchyDict.items())[0]
            baseControl = firstItem["control"]
            transform.connectOffsetParentMatrix(self.rigParent, baseControl.orig, mo=True)
