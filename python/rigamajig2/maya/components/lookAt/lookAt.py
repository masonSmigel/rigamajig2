"""
Look at Component
"""
import maya.cmds as cmds

from rigamajig2.maya import joint
from rigamajig2.maya import mathUtils
from rigamajig2.maya import transform
from rigamajig2.maya.components import base
from rigamajig2.maya.rig import control
from rigamajig2.maya.rig import spaces
from rigamajig2.shared import common


class LookAt(base.BaseComponent):
    """
    Look at or Aim component.
    All joints within the same component will aim at the same target.
    """

    VERSION_MAJOR = 1
    VERSION_MINOR = 1
    VERSION_PATCH = 0

    version_info = (VERSION_MAJOR, VERSION_MINOR, VERSION_PATCH)
    version = "%i.%i.%i" % version_info
    __version__ = version

    UI_COLOR = (198, 167, 255)

    def __init__(self, name, input, size=1, rigParent=str(), componentTag=None):
        """
        :param str name: name of the components
        :param list input: list of input joints to aim at a target. the aim axis is determined by the direction of the child
        :param float int size: default size of the controls:
        :param str rigParent: node to parent to connect the component to in the heirarchy
        :param dict lookAtSpaces: list of space connections for the aim control. formated as {"attrName": object}
        :param list rigParentList: Optional - list of rig parents that overrides the default rig parent.
                                   This can be useful for things like eyes where each input should have a different rig parent.
        """

        super(LookAt, self).__init__(
            name, input=input, size=size, rigParent=rigParent, componentTag=componentTag
        )
        self.side = common.getSide(self.name)

        self.aimTargetName = self.name + "_aim"
        self.lookAtSpaces = {}
        self.rigParentList = []
        self.upAxis = "y"

        self.defineParameter(
            parameter="aimTargetName", value=self.aimTargetName, dataType="string"
        )
        self.defineParameter(
            parameter="lookAtSpaces", value=self.lookAtSpaces, dataType="dict"
        )
        self.defineParameter(
            parameter="rigParentList", value=self.rigParentList, dataType="list"
        )
        self.defineParameter(parameter="upAxis", value=self.upAxis, dataType="string")

        for input in self.input:
            if cmds.objExists(input):
                parameterName = "{}Name".format(input)
                parameterValue = "_".join(input.split("_")[:-1])
                self.defineParameter(
                    parameter=parameterName, value=parameterValue, dataType="string"
                )

    def _createBuildGuides(self):
        """create build guides_hrc"""
        self.guidesHierarchy = cmds.createNode(
            "transform", name="{}_guide".format(self.name)
        )

        self._lookAtTgt = control.createGuide(
            "{}_lookAtTgt".format(self.name), parent=self.guidesHierarchy
        )
        transform.matchTranslate(self.input[0], self._lookAtTgt)
        for input in self.input:
            inputUpVector = control.createGuide(
                "{}_upVecTgt".format(input), parent=self.guidesHierarchy
            )
            setattr(self, "_{}_upVecTgt".format(input), inputUpVector)
            transform.matchTranslate(input, inputUpVector)

    def _initialHierarchy(self):
        """
        :return:
        """
        super(LookAt, self)._initialHierarchy()

        self.aimTarget = control.createAtObject(
            self.aimTargetName,
            spaces=True,
            hideAttrs=["v", "s"],
            size=self.size,
            color="banana",
            parent=self.controlHierarchy,
            shape="square",
            shapeAim="z",
            xformObj=self._lookAtTgt,
        )

        self.lookAtCtlList = list()
        for input in self.input:
            lookAtName = getattr(self, "{}Name".format(input))
            aimAxis = transform.getAimAxis(input)
            lookAtControl = control.createAtObject(
                lookAtName,
                hideAttrs=["v"],
                size=self.size,
                color="banana",
                parent=self.controlHierarchy,
                shape="circle",
                shapeAim=aimAxis,
                xformObj=input,
            )
            lookAtControl.addTrs("aim")

            # postion the control at the end joint. Get the aim vector from the input and mutiply by joint length.
            translation = mathUtils.scalarMult(
                transform.getVectorFromAxis(aimAxis), joint.length(input)
            )
            control.translateShapes(lookAtControl.name, translation)

            self.lookAtCtlList.append(lookAtControl)

    def _rigSetup(self):
        """
        setup the rig
        """
        self.upVecObjList = list()
        for input, lookatControl in zip(self.input, self.lookAtCtlList):
            # gather component settings from the container
            aimVector = transform.getVectorFromAxis(transform.getAimAxis(input))
            upVector = transform.getVectorFromAxis(self.upAxis)
            upVectorGuide = getattr(self, "_{}_upVecTgt".format(input))

            # create an upvector and aim contraint
            upVectorTrs = cmds.createNode(
                "transform",
                name="{}_upVec".format(lookatControl.trs),
                parent=self.spacesHierarchy,
            )
            transform.matchTranslate(upVectorGuide, upVectorTrs)
            self.upVecObjList.append(upVectorTrs)

            cmds.aimConstraint(
                self.aimTarget.name,
                lookatControl.trs,
                aimVector=aimVector,
                upVector=upVector,
                worldUpType="object",
                worldUpObject=upVectorTrs,
                maintainOffset=True,
            )

            # connect the control to input joint
            joint.connectChains(lookatControl.name, input)

        cmds.delete(self.guidesHierarchy)

    def _connect(self):
        """
        connect to the rig parent
        """
        # connect the controls to the rig parent. Check if we have a rigParentList to override the default rig parent.
        if self.rigParentList:
            for ctl, rigParent in zip(self.lookAtCtlList, self.rigParentList):
                transform.connectOffsetParentMatrix(rigParent, ctl.orig, mo=True)
            for upVec, rigParent in zip(self.upVecObjList, self.rigParentList):
                transform.connectOffsetParentMatrix(rigParent, upVec, mo=True)

        elif cmds.objExists(self.rigParent):
            for ctl in self.lookAtCtlList:
                transform.connectOffsetParentMatrix(self.rigParent, ctl.orig, mo=True)
            for upVec in self.upVecObjList:
                transform.connectOffsetParentMatrix(self.rigParent, upVec, mo=True)

        spaces.create(
            self.aimTarget.spaces,
            self.aimTarget.name,
            parent=self.spacesHierarchy,
            defaultName="world",
        )

        if self.lookAtSpaces:
            spaceValues = [self.lookAtSpaces[k] for k in self.lookAtSpaces.keys()]
            spacesAttrs = list(self.lookAtSpaces.keys())
            spaces.addSpace(self.aimTarget.spaces, spaceValues, spacesAttrs, "parent")
