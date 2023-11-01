#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: basicArray.py
    author: masonsmigel
    date: 10/2022
    description: 

"""
import maya.cmds as cmds

import rigamajig2.maya.components.base
from rigamajig2.maya import meta
from rigamajig2.maya.components.basic import basic
from rigamajig2.shared import common


class BasicArray(rigamajig2.maya.components.base.Base):
    """
    A wrapper of the basic component that will create several basic components with the same rig parent.
    """
    VERSION_MAJOR = 1
    VERSION_MINOR = 0
    VERSION_PATCH = 0

    version_info = (VERSION_MAJOR, VERSION_MINOR, VERSION_PATCH)
    version = '%i.%i.%i' % version_info
    __version__ = version

    UI_COLOR = (255, 201, 115)

    def __init__(self, name, input, size=1, rigParent=str(), componentTag=None):
        """
       :param name: Component name. To add a side use a side token
       :param input: Single input joint
       :param size:  Default size of the controls.
       :param spacesGrp: add a spaces group
       :param trsGrp: add a trs group
       :param sdkGrp: add an sdk group
       :param addBpm: add an associated bind pre matrix joint to the components skin joint.
       :param rigParent:  Connect the component to a rigParent.
       :param controlShape: Control shape to apply. Default: "cube"
       :param worldOrient: Orient the control to the world. Default: False
       """
        super(BasicArray, self).__init__(name, input=input, size=size, rigParent=rigParent, componentTag=componentTag)
        self.side = common.getSide(self.name)

        self.defineParameter(parameter="controlName", value=name, dataType="string")
        self.defineParameter(parameter="controlShape", value="cube", dataType="string")
        self.defineParameter(parameter="worldOrient", value=False, dataType="bool")
        self.defineParameter(parameter="addSpaces", value=False, dataType="bool")
        self.defineParameter(parameter="addTrs", value=False, dataType="bool")
        self.defineParameter(parameter="addSdk", value=False, dataType="bool")
        self.defineParameter(parameter="addBpm", value=False, dataType="bool")

    def _setInitialData(self):
        """ Build the joint name attributes"""

        inputBaseNames = [x.rsplit("_bind", 1)[0] for x in self.input]
        self.controlNameAttrs = list()
        for i in range(len(self.input)):
            jointNameStr = "joint{}Name".format(i)
            self.controlNameAttrs.append(jointNameStr)
            self.defineParameter(parameter=jointNameStr, value=inputBaseNames[i], dataType="string")

    def _initialHierarchy(self):
        """ Build the initial hierarchy"""
        super(BasicArray, self)._initialHierarchy()

        self.basicComponentList = list()
        for i in range(len(self.input)):
            if self.side:
                componentName = getattr(self, self.controlNameAttrs[i]) + '_' + self.side
            else:
                componentName = getattr(self, self.controlNameAttrs[i])

            component = basic.Basic(name=componentName, input=[self.input[i]], rigParent=self.rigParent)
            component.defineParameter("controlShape", self.controlShape)
            component.defineParameter("worldOrient", self.worldOrient)
            component.defineParameter("addSpaces", self.addSpaces)
            component.defineParameter("addTrs", self.addTrs)
            component.defineParameter("addSdk", self.addSdk)
            component.defineParameter("addBpm", self.addBpm)

            component.initializeComponent()
            cmds.container(self.container, e=True, f=True, addNode=component.getContainer())
            meta.tag(component.getContainer(), 'subComponent')
            self.basicComponentList.append(component)

    def _rigSetup(self):
        """Setup the rig, for this component that includes building the basic components"""

        for component in self.basicComponentList:
            component.buildComponent()
            cmds.parent(component.paramsHierarchy, self.paramsHierarchy)
            cmds.parent(component.control.orig, self.controlHierarchy)
            cmds.parent(component.spacesHierarchy, self.spacesHierarchy)

            if self.addBpm:
                self.bpmHierarchy = cmds.createNode("transform", name="{}_bpm_hrc".format(self.name),
                                                    parent=self.rootHierarchy)
                cmds.parent(component.bpmHierarchy, self.bpmHierarchy)

            cmds.delete(component.rootHierarchy)

    def _connect(self):
        """ run the setup step of each component"""
        for component in self.basicComponentList:
            component.connectComponent()
