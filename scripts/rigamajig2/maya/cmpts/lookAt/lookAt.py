"""
Look at Component
"""
import maya.cmds as cmds
import rigamajig2.maya.cmpts.base
import rigamajig2.shared.common as common
import rigamajig2.maya.transform as rig_transform
import rigamajig2.maya.rig.control as rig_control
import rigamajig2.maya.joint as joint
import rigamajig2.maya.mathUtils as mathUtils
import rigamajig2.maya.rig.spaces as spaces


class LookAt(rigamajig2.maya.cmpts.base.Base):
    """
    Look at or Aim component.
    All joints within the same component will aim at the same target.
    """
    VERSION_MAJOR = 1
    VERSION_MINOR = 0
    VERSION_PATCH = 0

    version_info = (VERSION_MAJOR, VERSION_MINOR, VERSION_PATCH)
    version = '%i.%i.%i' % version_info
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

        super(LookAt, self).__init__(name, input=input, size=size, rigParent=rigParent, componentTag=componentTag)
        self.side = common.getSide(self.name)

        self.defineParameter(parameter="aimTargetName", value=self.name + "_aim", dataType="string")
        self.defineParameter(parameter="lookAtSpaces", value=dict(), dataType="dict")
        self.defineParameter(parameter="rigParentList", value=list(), dataType="list")
        self.defineParameter(parameter="upAxis", value="y", dataType="string")

        for input in self.input:
            if cmds.objExists(input):
                parameterName = '{}Name'.format(input)
                parameterValue = '_'.join(input.split("_")[:-1])
                self.defineParameter(parameter=parameterName, value=parameterValue, dataType="string")

    def createBuildGuides(self):
        """ create build guides_hrc """
        self.guidesHierarchy = cmds.createNode("transform", name='{}_guide'.format(self.name))

        self._lookAtTgt = rig_control.createGuide("{}_lookAtTgt".format(self.name), parent=self.guidesHierarchy)
        rig_transform.matchTranslate(self.input, self._lookAtTgt)
        for input in self.input:
            inputUpVector = rig_control.createGuide("{}_upVecTgt".format(input), parent=self.guidesHierarchy)
            setattr(self, "_{}_upVecTgt".format(input), inputUpVector)
            rig_transform.matchTranslate(input, inputUpVector)

    def initialHierarchy(self):
        """
        :return:
        """
        super(LookAt, self).initialHierarchy()

        self.aimTarget = rig_control.createAtObject(self.aimTargetName,
                                                    spaces=True,
                                                    hideAttrs=['v', 's'], size=self.size, color='banana',
                                                    parent=self.controlHierarchy, shape='square', shapeAim='z',
                                                    xformObj=self._lookAtTgt)

        self.lookAtCtlList = list()
        for input in self.input:
            lookAtName = getattr(self, "{}Name".format(input))
            aimAxis = rig_transform.getAimAxis(input)
            lookAtControl = rig_control.createAtObject(lookAtName, hideAttrs=['v'], size=self.size,
                                                       color='banana', parent=self.controlHierarchy, shape='circle',
                                                       shapeAim=aimAxis, xformObj=input)
            lookAtControl.addTrs("aim")

            # postion the control at the end joint. Get the aim vector from the input and mutiply by joint length.
            translation = mathUtils.scalarMult(rig_transform.getVectorFromAxis(aimAxis), joint.length(input))
            rig_control.translateShapes(lookAtControl.name, translation)

            self.lookAtCtlList.append(lookAtControl)

    def rigSetup(self):
        """
        setup the rig
        """
        self.upVecObjList = list()
        for input, lookatControl in zip(self.input, self.lookAtCtlList):
            # gather component settings from the container
            aimVector = rig_transform.getVectorFromAxis(rig_transform.getAimAxis(input))
            upVector = rig_transform.getVectorFromAxis(self.upAxis)
            upVectorGuide = getattr(self, "_{}_upVecTgt".format(input))

            # create an upvector and aim contraint
            upVectorTrs = cmds.createNode("transform", name="{}_upVec".format(lookatControl.trs),
                                          p=self.spacesHierarchy)
            rig_transform.matchTranslate(upVectorGuide, upVectorTrs)
            self.upVecObjList.append(upVectorTrs)

            cmds.aimConstraint(self.aimTarget.name, lookatControl.trs, aim=aimVector, upVector=upVector,
                               worldUpType='object', worldUpObject=upVectorTrs, mo=True)

            # connect the control to input joint
            joint.connectChains(lookatControl.name, input)
            # rig_transform.connectOffsetParentMatrix(lookAt_ctl[-1], input)

        # Delete the proxy guides_hrc:
        cmds.delete(self.guidesHierarchy)

    def connect(self):
        """
        connect to the rig parent
        """
        # connect the controls to the rig parent. Check if we have a rigParentList to override the default rig parent.
        if len(self.rigParentList) > 0:
            for ctl, rigParent in zip(self.lookAtCtlList, self.rigParentList):
                rig_transform.connectOffsetParentMatrix(rigParent, ctl.orig, mo=True)
            for upVec, rigParent in zip(self.upVecObjList, self.rigParentList):
                rig_transform.connectOffsetParentMatrix(rigParent, upVec, mo=True)

        elif cmds.objExists(self.rigParent):
            for ctl in self.lookAtCtlList:
                rig_transform.connectOffsetParentMatrix(self.rigParent, ctl.orig, mo=True)
            for upVec in self.upVecObjList:
                rig_transform.connectOffsetParentMatrix(self.rigParent, upVec, mo=True)

        spaces.create(self.aimTarget.spaces, self.aimTarget.name, parent=self.spacesHierarchy, defaultName='world')

        if self.lookAtSpaces:
            spaceValues = [self.lookAtSpaces[k] for k in self.lookAtSpaces.keys()]
            spacesAttrs = self.lookAtSpaces.keys()
            spaces.addSpace(self.aimTarget.spaces, spaceValues, spacesAttrs, 'parent')
