#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: jaw.py
    author: masonsmigel
    date: 09/2022
    description: create a jaw control

"""

import maya.cmds as cmds

from rigamajig2.maya import attr
from rigamajig2.maya import joint
from rigamajig2.maya import node
from rigamajig2.maya import transform
from rigamajig2.maya.components import base
from rigamajig2.maya.rig import control
from rigamajig2.shared import common


class Jaw(base.BaseComponent):
    """
    A simple jaw component
    """

    VERSION_MAJOR = 1
    VERSION_MINOR = 1
    VERSION_PATCH = 0

    version_info = (VERSION_MAJOR, VERSION_MINOR, VERSION_PATCH)
    version = "%i.%i.%i" % version_info
    __version__ = version

    UI_COLOR = (254, 66, 129)

    def __init__(self, name, input, size=1, rigParent=str(), componentTag=None):
        """
        :param name: Component Name
        :param input: specific list of joints. [jaw, muppet,  lipsTop, lipsBot, lips_l, lips_r]
        :param size: default size of the controls
        :param rigParent: connect the component to a rigParent
        """
        super(Jaw, self).__init__(
            name, input=input, size=size, rigParent=rigParent, componentTag=componentTag
        )
        self.side = common.getSide(self.name)

        self.addLipControls = True
        self.jawOpenTyOffset = -0.2
        self.jawOpenTzOffset = -0.4

        self.defineParameter(
            parameter="addLipControls", value=self.addLipControls, dataType="bool"
        )
        self.defineParameter(
            parameter="jawOpenTyOffset", value=self.jawOpenTyOffset, dataType="float"
        )
        self.defineParameter(
            parameter="jawOpenTzOffset", value=self.jawOpenTzOffset, dataType="float"
        )

        # TODO: jaw component names
        inputBaseNames = [x.split("_")[0] for x in self.input]
        self.defineParameter(
            parameter="jawName", value=inputBaseNames[0], dataType="string"
        )
        self.defineParameter(
            parameter="muppetName", value=inputBaseNames[1], dataType="string"
        )
        self.defineParameter(
            parameter="lipsTopName", value=inputBaseNames[2], dataType="string"
        )
        self.defineParameter(
            parameter="lipsBotName", value=inputBaseNames[3], dataType="string"
        )
        self.defineParameter(
            parameter="lips_lName", value=inputBaseNames[4] + "_l", dataType="string"
        )
        self.defineParameter(
            parameter="lips_rName", value=inputBaseNames[5] + "_r", dataType="string"
        )

    def _initialHierarchy(self):
        """Build the inital rig hierarchy"""
        super(Jaw, self)._initialHierarchy()

        self.jawControl = control.createAtObject(
            self.jawName,
            self.side,
            trs=True,
            color="lightyellow",
            parent=self.controlHierarchy,
            shape="cube",
            xformObj=self.input[0],
        )

        self.muppetControl = control.createAtObject(
            name=self.muppetName,
            side=self.side,
            color="lightyellow",
            parent=self.controlHierarchy,
            shape="cube",
            xformObj=self.input[1],
        )

        self.lipsTopControl = control.createAtObject(
            name=self.lipsTopName,
            side=self.side,
            color="lightyellow",
            parent=self.jawControl.name,
            shape="square" if self.addLipControls else None,
            shapeAim="z",
            xformObj=self.input[2],
        )

        self.lipsBotControl = control.createAtObject(
            name=self.lipsBotName,
            side=self.side,
            color="lightyellow",
            parent=self.jawControl.name,
            shape="square" if self.addLipControls else None,
            shapeAim="z",
            xformObj=self.input[3],
        )

        self.lipsLControl = control.createAtObject(
            name=self.lips_lName,
            side=self.side,
            color="lightyellow",
            parent=self.jawControl.name,
            shape="triangle" if self.addLipControls else None,
            shapeAim="-x",
            xformObj=self.input[4],
        )

        self.lipsRControl = control.createAtObject(
            name=self.lips_rName,
            side=self.side,
            color="lightyellow",
            parent=self.jawControl.name,
            shape="triangle" if self.addLipControls else None,
            shapeAim="-x",
            xformObj=self.input[5],
        )

        self.lipsControls = [
            self.lipsTopControl,
            self.lipsBotControl,
            self.lipsLControl,
            self.lipsRControl,
        ]
        self.allControls = [self.jawControl, self.muppetControl] + self.lipsControls

    def _rigSetup(self):
        """Create the rig setup"""

        # bind all the contols to the joints
        joint.connectChains([x.name for x in self.allControls], self.input)

        defaultValues = [0, 1, 0.5, 0.5]
        # add interpolations between the jaw and muppet to all the lips
        for i, lipControl in enumerate(self.lipsControls):
            # create an attribute to control the blending
            blendAttr = attr.createAttr(
                node=self.paramsHierarchy,
                longName="{}Follow".format(lipControl.name),
                attributeType="float",
                value=defaultValues[i],
                minValue=0,
                maxValue=1.0,
            )

            # blend the rotation between the two joints
            jawMultMatrix, _ = transform.connectOffsetParentMatrix(
                driver=self.input[0],
                driven=lipControl.orig,
                mo=True,
                t=True,
                r=True,
                s=True,
                sh=True,
            )

            muppetMultMatrix, _ = transform.connectOffsetParentMatrix(
                driver=self.input[1],
                driven=lipControl.orig,
                mo=True,
                t=True,
                r=True,
                s=True,
                sh=True,
            )

            blendMatrix = cmds.createNode(
                "blendMatrix",
                name="{}_{}_blendMatrix".format(self.input[1], self.input[0]),
            )
            cmds.connectAttr(
                "{}.matrixSum".format(muppetMultMatrix),
                "{}.inputMatrix".format(blendMatrix),
            )
            cmds.connectAttr(
                "{}.matrixSum".format(jawMultMatrix),
                "{}.target[0].targetMatrix".format(blendMatrix),
            )
            cmds.connectAttr(blendAttr, "{}.envelope".format(blendMatrix))

            # connect the blendMatrix to the pick matrix (and therefore the interp joint)
            cmds.connectAttr(
                "{}.outputMatrix".format(blendMatrix),
                "{}.offsetParentMatrix".format(lipControl.orig),
                force=True,
            )

        # setup the corner pinning
        for cornerControl in [self.lipsLControl, self.lipsRControl]:
            attr.addSeparator(cornerControl.name, "----")
            pinAttr = attr.createAttr(
                cornerControl.name,
                longName="pin",
                attributeType="float",
                minValue=-1,
                maxValue=1,
            )

            lipFollowAttr = "{}.{}Follow".format(
                self.paramsHierarchy, cornerControl.name
            )
            node.remapValue(
                pinAttr,
                inMin=-1,
                inMax=1,
                outMin=1,
                outMax=0,
                output=lipFollowAttr,
                name=cornerControl.name,
            )

        # setup the lip push stuff
        attr.addSeparator(self.jawControl.name, "----")
        chewAttr = attr.createAttr(
            self.jawControl.name,
            longName="chew",
            attributeType="float",
            value=0,
            minValue=0,
            maxValue=1,
        )
        chewHeight = attr.createAttr(
            self.jawControl.name,
            longName="chewHeight",
            attributeType="float",
            value=0,
            minValue=-1,
            maxValue=1,
        )
        autoPushAttr = attr.createAttr(
            self.jawControl.name,
            longName="autoPush",
            attributeType="float",
            value=1,
            minValue=0,
            maxValue=1,
        )

        lipsPushMinAttr = attr.createAttr(
            self.jawControl.name,
            longName="lipPushAngle",
            attributeType="float",
            value=-10,
            maxValue=0,
        )

        jawRotateAttr = "{}.rx".format(self.input[0])
        pushBlendRemap = node.remapValue(
            jawRotateAttr,
            inMin=lipsPushMinAttr,
            inMax=0.0,
            outMin=1.0,
            outMax=0.0,
            name="{}_pushBlend".format(self.name),
        )

        autoSwitch = node.multDoubleLinear(
            "{}.outValue".format(pushBlendRemap),
            autoPushAttr,
            name="{}_autoSwitch".format(self.name),
        )

        chewTriggerCond = node.condition(
            chewAttr,
            0,
            ifTrue=[chewAttr, chewHeight, 0],
            ifFalse=["{}.output".format(autoSwitch), -1, 0],
            name="{}_chewTrigger".format(self.name),
            operation=">",
        )

        lipPushCond = node.condition(
            jawRotateAttr,
            0,
            operation="<",
            ifTrue="{}.outColorR".format(chewTriggerCond),
            ifFalse=chewAttr,
            name="{}_lipPush".format(self.name),
        )

        # setup the chew stuff
        lipTopFollowAttr = "{}.{}Follow".format(
            self.paramsHierarchy, self.lipsTopControl.name
        )
        lipBotFollowAttr = "{}.{}Follow".format(
            self.paramsHierarchy, self.lipsBotControl.name
        )

        node.blendTwoAttrs(
            chewHeight,
            -1,
            weight="{}.outColorR".format(lipPushCond),
            name="{}_autoPush".format(self.name),
        )

        chewHeightName = "{}_chewHeight".format(self.name)
        chewHeightRemaped = node.remapValue(
            "{}.outColorG".format(chewTriggerCond),
            inMin=-1,
            inMax=1,
            outMin=0,
            outMax=1,
            name=chewHeightName,
        )

        # setup the bottom control chew
        botMdlName = "{}_chew".format(self.lipsBotControl.name)
        botChewMdl = node.multDoubleLinear(
            "{}.outValue".format(chewHeightRemaped),
            "{}.outColorR".format(lipPushCond),
            name=botMdlName,
        )

        botChewReverse = "{}_chew".format(self.lipsBotControl.name)
        node.reverse(
            "{}.output".format(botChewMdl), output=lipBotFollowAttr, name=botChewReverse
        )

        # setup the top control chew
        topChewReverseName = "{}_chew".format(self.lipsTopControl.name)
        topChewReverse = node.reverse(
            "{}.outValue".format(chewHeightRemaped), name=topChewReverseName
        )

        topChewMdlName = "{}_chew".format(self.lipsTopControl.name)
        node.multDoubleLinear(
            "{}.outputX".format(topChewReverse),
            "{}.outColorR".format(lipPushCond),
            output=lipTopFollowAttr,
            name=topChewMdlName,
        )

        # setup the jaw translate stuff

        # HACK: for some reason the metaNode doesnt handle the negative floats well so we'll store them as strings
        # and make sure to convert them back to floats before we apply them
        jawOpenTy = attr.createAttr(
            self.paramsHierarchy,
            longName="jawOpenTy",
            attributeType="float",
            value=float(self.jawOpenTyOffset),
        )
        jawOpenTz = attr.createAttr(
            self.paramsHierarchy,
            longName="jawOpenTz",
            attributeType="float",
            value=float(self.jawOpenTzOffset),
        )

        jawControlRotate = "{}.rx".format(self.jawControl.name)
        node.remapValue(
            jawControlRotate,
            inMin=0,
            inMax=20,
            outMin=0,
            outMax=jawOpenTy,
            output="{}.ty".format(self.jawControl.trs),
            name="{}_jawOpenTy".format(self.name),
        )

        node.remapValue(
            jawControlRotate,
            inMin=0,
            inMax=20,
            outMin=0,
            outMax=jawOpenTz,
            output="{}.tz".format(self.jawControl.trs),
            name="{}_jawOpenTz".format(self.name),
        )

    def _connect(self):
        """connect the rig to its rigparent"""
        if cmds.objExists(self.rigParent):
            transform.connectOffsetParentMatrix(
                self.rigParent, self.jawControl.orig, mo=True
            )
            transform.connectOffsetParentMatrix(
                self.rigParent, self.muppetControl.orig, mo=True
            )
