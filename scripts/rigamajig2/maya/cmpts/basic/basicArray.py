#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: basicArray.py
    author: masonsmigel
    date: 10/2022
    discription: 

"""
import maya.cmds as cmds
import rigamajig2.maya.cmpts.base
from rigamajig2.shared import common
from rigamajig2.maya.cmpts.basic import basic
from rigamajig2.maya import meta


class BasicArray(rigamajig2.maya.cmpts.base.Base):
    """
    A wrapper of the basic component that will create several basic components with the same rig parent.
    """
    VERSION_MAJOR = 1
    VERSION_MINOR = 0
    VERSION_PATCH = 0

    version_info = (VERSION_MAJOR, VERSION_MINOR, VERSION_PATCH)
    version = '%i.%i.%i' % version_info
    __version__ = version

    def __init__(self, name, input, size=1, rigParent=str(),
                 addSpaces=False, addTrs=False, addSdk=False, addBpm=False,
                 controlShape='cube', worldOrient=False):
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
        super(BasicArray, self).__init__(name, input=input, size=size, rigParent=rigParent)
        self.side = common.getSide(self.name)

        self.cmptSettings['controlName'] = name
        self.cmptSettings['controlShape'] = controlShape
        self.cmptSettings['worldOrient'] = worldOrient
        self.cmptSettings['addSpaces'] = addSpaces
        self.cmptSettings['addTrs'] = addTrs
        self.cmptSettings['addSdk'] = addSdk
        self.cmptSettings['addBpm'] = addBpm

    def setInitalData(self):
        """ Build the joint name attributes"""

        inputBaseNames = [x.rsplit("_", 1)[0] for x in self.input]
        self.controlNameAttrs = list()
        for i in range(len(self.input)):
            jointNameStr = "joint{}Name".format(i)
            self.controlNameAttrs.append(jointNameStr)
            self.cmptSettings[jointNameStr] = inputBaseNames[i]

    def initialHierarchy(self):
        """ Build the inital hierarchy"""
        super(BasicArray, self).initialHierarchy()

        self.basicComponentList = list()
        for i in range(len(self.input)):
            if self.side:
                componentName = getattr(self, self.controlNameAttrs[i]) + '_' + self.side
            else:
                componentName = getattr(self, self.controlNameAttrs[i])

            component = basic.Basic(
                name=componentName,
                input=[self.input[i]],
                rigParent=self.rigParent,
                controlShape=self.controlShape,
                worldOrient=self.worldOrient,
                addSpaces=self.addSpaces,
                addTrs=self.addTrs,
                addSdk=self.addSdk,
                addBpm=self.addBpm)

            component._initalizeComponent()
            cmds.container(self.container, e=True, f=True, addNode=component.getContainer())
            meta.tag(component.getContainer(), 'subComponent')
            self.basicComponentList.append(component)

    def rigSetup(self):
        """Setup the rig, for this component that includes buidling the basic components"""

        for cmpt in self.basicComponentList:
            cmpt._buildComponent()
            cmds.parent(cmpt.paramsHierarchy, self.paramsHierarchy)
            cmds.parent(cmpt.control.orig, self.controlHierarchy)
            cmds.parent(cmpt.spacesHierarchy, self.spacesHierarchy)

            if self.addBpm:
                self.bpmHierarchy = cmds.createNode("transform", name="{}_bpm_hrc".format(self.name),
                                                    parent=self.rootHierarchy)
                cmds.parent(cmpt.bpmHierarchy, self.bpmHierarchy)

            cmds.delete(cmpt.rootHierarchy)

    def connect(self):
        """ run the setup step of each component"""
        for cmpt in self.basicComponentList:
            cmpt._connectComponent()
