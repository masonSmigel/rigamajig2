#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: stickyControls.py
    author: masonsmigel
    date: 10/2022
    discription: a sticky controller class

"""
import maya.cmds as cmds
import rigamajig2.maya.cmpts.base
from collections import OrderedDict
from rigamajig2.maya import meta
from rigamajig2.shared import common
from rigamajig2.maya.rig import control
from rigamajig2.maya import mesh
from rigamajig2.maya import transform
from rigamajig2.maya import joint

CONTROLLER_NAME_ATTR = "control_{}_name"
CONTROLLER_SIZE_ATTR = "control_{}_size"
CONTROLLER_MIRROR_ATTR = "control_{}_mirror"


class StickyControls(rigamajig2.maya.cmpts.base.Base):
    """
    The Sticky control component will create a whole bunch of sticky controlers, this is typically for facial rigging.

    The component will create a bunch of guides which can be used to place the facial controllers,
    the component will find the closest vertex to the input mesh and connect the control to that vertex.

    Mirroring is currently only supported across the X axis.
    """
    VERSION_MAJOR = 1
    VERSION_MINOR = 0
    VERSION_PATCH = 0

    version_info = (VERSION_MAJOR, VERSION_MINOR, VERSION_PATCH)
    version = '%i.%i.%i' % version_info
    __version__ = version

    def __init__(self, name, input, size=1, rigParent=str(), numControls=1, negateTranslate=True, mirrorAxis='x'):
        """
        :param name: Component name. To add a side use a side token
        :param input: The name of the mesh to stick to. This should be the final deformation Mesh.
        :param size:  Default size of the controls.
        :param rigParent: onnect the component to a rigParent.
        :param numControls: number of controlers to create.
        """
        input = common.getFirstIndex(input)
        if not mesh.isMesh(input):
            raise Exception("The input for {} must be a mesh object.".format(name))

        if mirrorAxis != "x":
            raise NotImplemented("Mirror Across other axis has not been implemented yet.")

        super(StickyControls, self).__init__(name, input=input, size=size, rigParent=rigParent)

        self.cmptSettings['numControls'] = numControls
        self.cmptSettings['negateTranslate'] = negateTranslate
        self.cmptSettings['mirrorAxis'] = mirrorAxis

    def loadSettings(self, data):
        """
       Overwrite the loadSettings function in order to add more data when we set the data.
        For this we need to  add some attributes for each controller we want to create.
        :param data: The loadSettings function takes in a data varrable. We will passs this into the super.
        :return:
        """
        super(StickyControls, self).loadSettings(data)
        
        # store the number of controls before loading stuff from the class.
        numberofControls = self.cmptSettings['numControls']
        self._loadComponentParametersToClass()
        self.controlIndecies = list()

        for i in range(self.numControls):
            newDict = OrderedDict()
            newDict[CONTROLLER_NAME_ATTR.format(i)] = "control_{}".format(i)
            newDict[CONTROLLER_SIZE_ATTR.format(i)] = self.size
            newDict[CONTROLLER_MIRROR_ATTR.format(i)] = False

            # here we need to manually re-add new attributes to the metanode
            self.metaNode.setDataDict(data=newDict, hide=True)
            self.controlIndecies.append(i)
            self.cmptSettings.update(newDict)

        # TODO: optimize
        # This is alittle slopy but we essentially need to load twice. Once to get the number of controls to add.
        # then a second tme to get the data for the new attributes we add
        super(StickyControls, self).loadSettings(data)

    def initialHierachy(self):
        """Setup the inital Hirarchy. implement in subclass"""
        super(StickyControls, self).initialHierachy()

        # in order for the controls to rotate properly with their parent we need to connect the rigparents matrix to the
        self.controlOffsetTrs = cmds.createNode('transform', n=self.name + '_control_trs', parent=self.controlHierarchy)
        if self.rigParent:
            transform.matchTranslate(self.rigParent, self.controlOffsetTrs)

    def createBuildGuides(self):
        """
        Create a build guide for each control we add.
        """
        self.guidesHierarchy = cmds.createNode("transform", name='{}_guide'.format(self.name))

        self.guidesList = list()
        for index in self.controlIndecies:
            controlName = getattr(self, CONTROLLER_NAME_ATTR.format(index))
            controlSize = getattr(self, CONTROLLER_SIZE_ATTR.format(index))
            controlMirror = getattr(self, CONTROLLER_MIRROR_ATTR.format(index))

            guide = control.createGuide(controlName, parent=self.guidesHierarchy)
            self.guidesList.append(guide)

        self._loadComponentParametersToClass()

    def rigSetup(self):
        """
        build the rig setup
        """

        for index in self.controlIndecies:
            guide = self.guidesList[index]
            controlName = getattr(self, CONTROLLER_NAME_ATTR.format(index))
            controlSize = getattr(self, CONTROLLER_SIZE_ATTR.format(index))
            controlMirror = getattr(self, CONTROLLER_MIRROR_ATTR.format(index))

            controlObj = control.createMeshRivetAtObject(
                controlName,
                mesh=self.input,
                orig=True,
                neg=self.negateTranslate,
                xformObj=guide,
                parent=self.controlOffsetTrs,
                size=controlSize,
                shapeAim='z')

            # set the controler scale here
            cmds.xform(controlObj.orig, s=[1 * controlSize, 1 * controlSize, 1 * controlSize])

            self.controlers.append(controlObj.name)

            if controlMirror:
                mirroredControlName = common.getMirrorName(controlName)

                mirroredGuide = control.createGuide(mirroredControlName, parent=self.guidesHierarchy)
                transform.matchTransform(guide, mirroredGuide)

                joint.mirror(guide, axis='x', mode='translate', zeroRotation=False)
                mirroredControlObj = control.createMeshRivetAtObject(
                    mirroredControlName,
                    mesh=self.input,
                    orig=True,
                    neg=self.negateTranslate,
                    xformObj=mirroredGuide,
                    parent=self.controlOffsetTrs,
                    size=controlSize,
                    shapeAim='z')

                # set the negative scale here
                cmds.xform(mirroredControlObj.orig, s=[1 * controlSize, 1 * controlSize, -1 * controlSize])

                self.controlers.append(mirroredControlObj.name)

    def connect(self):
        """
        Connect the stickyControls to a rig Parent.
        Since the translation is handled by the uvPin we only want to connect the rotation from the rigParent
        :return:
        """
        if cmds.objExists(self.rigParent):
            transform.connectOffsetParentMatrix(self.rigParent, self.controlOffsetTrs, mo=True)
