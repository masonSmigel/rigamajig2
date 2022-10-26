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

    def __init__(self, name, input, size=1, rigParent=str(), lookAtSpaces=None):
        """
        :param str name: name of the components
        :param list input: list of input joints to aim at a target. the aim axis is determined by the direction of the child
        :param float int size: default size of the controls:
        :param str rigParent: node to parent to connect the component to in the heirarchy
        :param dict lookAtSpaces: list of space connections for the aim control. formated as {"attrName": object}
        """

        super(LookAt, self).__init__(name, input=input, size=size, rigParent=rigParent)
        self.side = common.getSide(self.name)

        if lookAtSpaces is None:
            lookAtSpaces = dict()

        self.cmptSettings['aimTargetName'] = self.name + "_aim"
        self.cmptSettings['lookAtSpaces'] = lookAtSpaces

        for input in self.input:
            if not cmds.objExists(input):
                continue

            aimVector = rig_transform.getVectorFromAxis(rig_transform.getAimAxis(input))
            if cmds.objExists(input):
                self.cmptSettings['{}Name'.format(input)] = '_'.join(input.split("_")[:-1])
                self.cmptSettings['{}_aimVector'.format(input)] = aimVector
                self.cmptSettings['{}_upVector'.format(input)] = (0, 1, 0)

    def createBuildGuides(self):
        """ create build guides_hrc """
        self.guidesHierarchy = cmds.createNode("transform", name='{}_guide'.format(self.name))

        self._lookAtTgt = rig_control.createGuide("{}_lookAtTgt".format(self.name), parent=self.guidesHierarchy)
        rig_transform.matchTranslate(self.input, self._lookAtTgt)
        for input in self.input:
            inputUpVector = rig_control.createGuide("{}_upVecTgt".format(input), parent=self.guidesHierarchy)
            setattr(self, "_{}_upVecTgt".format(input), inputUpVector)
            rig_transform.matchTranslate(input, inputUpVector)

    def initalHierachy(self):
        """
        :return:
        """
        super(LookAt, self).initalHierachy()

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
            aimVector = getattr(self, "{}_aimVector".format(input))
            upVector = getattr(self, "{}_upVector".format(input))
            upVectorGuide = getattr(self, "_{}_upVecTgt".format(input))

            # create an upvector and aim contraint
            upVectorTrs = cmds.createNode("transform", name="{}_upVec".format(lookatControl.trs), p=self.spacesHierarchy)
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
        # connect the controls to the rig parent
        if cmds.objExists(self.rigParent):
            for ctl in self.lookAtCtlList:
                rig_transform.connectOffsetParentMatrix(self.rigParent, ctl.orig, mo=True)
            for upVec in self.upVecObjList:
                rig_transform.connectOffsetParentMatrix(self.rigParent, upVec, mo=True)

        spaces.create(self.aimTarget.spaces, self.aimTarget.name, parent=self.spacesHierarchy, defaultName='world')

        if self.lookAtSpaces:
            spaceValues = [self.lookAtSpaces[k] for k in self.lookAtSpaces.keys()]
            spacesAttrs = self.lookAtSpaces.keys()
            spaces.addSpace(self.aimTarget.spaces, spaceValues, spacesAttrs, 'parent')

    @staticmethod
    def createInputJoints(name=None, side=None, numJoints=4):
        import rigamajig2.maya.naming as naming
        import rigamajig2.maya.joint as joint
        joints = list()

        for i in range(numJoints):
            name = name or 'lookAt'
            jointName  = naming.getUniqueName("{}_0".format(name))
            jnt = cmds.createNode("joint", name=jointName + "_{}".format(i))

            jntEnd = cmds.createNode("joint", name=jointName + "_{}".format(i) + "_1")
            cmds.parent(jntEnd, jnt)
            cmds.xform(jntEnd, objectSpace=True, t=(0, 0, 10))

            joints.append(jnt)

        return joints