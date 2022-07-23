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
    VERSION_MAJOR = 1
    VERSION_MINOR = 0
    VERSION_PATCH = 0

    version_info = (VERSION_MAJOR, VERSION_MINOR, VERSION_PATCH)
    version = '%i.%i.%i' % version_info
    __version__ = version

    def __init__(self, name, input=[], size=1, rigParent=str(), lookAtSpaces=dict()):
        """
        Look at or aim component.
        All joints within the same component will aim at the same target.


        :param name: name of the components
        :type name: str
        :param input: list of input joints to aim at a target. the aim axis is determined by the direction of the child
        :type input: list
        :param size: default size of the controls:
        :type size: float
        :param rigParent: node to parent to connect the component to in the heirarchy
        :type rigParent: str
        :param lookAtSpaces: list of space connections for the aim control. formated as {"attrName": object}
        :type lookAtSpaces: dict
        """

        super(LookAt, self).__init__(name, input=input, size=size, rigParent=rigParent)
        self.side = common.getSide(self.name)

        self.cmptSettings['aimTargetName'] = self.name + "_aim"
        self.cmptSettings['lookAtSpaces'] = lookAtSpaces

        for input in self.input:
            if not cmds.objExists(input):
                continue
            self.cmptSettings['{}Name'.format(input)] = '_'.join(input.split("_")[:-1])
            self.cmptSettings['{}_aimVector'.format(input)] = rig_transform.getVectorFromAxis(rig_transform.getAimAxis(input))
            self.cmptSettings['{}_upVector'.format(input)] = (0, 1, 0)

    def createBuildGuides(self):
        """ create build guides_hrc """
        self.guides_hrc = cmds.createNode("transform", name='{}_guide'.format(self.name))

        self._lookAtTgt = rig_control.createGuide("{}_lookAtTgt".format(self.name), parent=self.guides_hrc)
        rig_transform.matchTranslate(self.input, self._lookAtTgt)
        for input in self.input:
            input_upVec = rig_control.createGuide("{}_upVecTgt".format(input), parent=self.guides_hrc)
            setattr(self, "_{}_upVecTgt".format(input), input_upVec)
            rig_transform.matchTranslate(input, input_upVec)

    def initalHierachy(self):
        """
        :return:
        """
        super(LookAt, self).initalHierachy()

        self.aimTarget = rig_control.createAtObject(self.aimTargetName,
                                                    spaces=True,
                                                    hideAttrs=['v', 's'], size=self.size, color='banana',
                                                    parent=self.control_hrc, shape='square', shapeAim='z',
                                                    xformObj=self._lookAtTgt)

        self.lookAtCtlList = list()
        for input in self.input:
            lookAtName = getattr(self, "{}Name".format(input))
            aimAxis = rig_transform.getAimAxis(input)
            lookAt_ctl = rig_control.createAtObject(lookAtName, hideAttrs=['v'], size=self.size,
                                                    color='banana', parent=self.control_hrc, shape='circle',
                                                    shapeAim=aimAxis, xformObj=input)
            lookAt_ctl.addTrs("aim")

            # postion the control at the end joint. Get the aim vector from the input and mutiply by joint length.
            translation = mathUtils.scalarMult(rig_transform.getVectorFromAxis(aimAxis), joint.length(input))
            rig_control.translateShapes(lookAt_ctl.name, translation)

            self.lookAtCtlList.append(lookAt_ctl)

    def rigSetup(self):
        """
        setup the rig
        """
        self.UpVecObjList = list()
        for input, lookAt_ctl in zip(self.input, self.lookAtCtlList):

            # gather component settings from the container
            lookAt_aimVec = getattr(self, "{}_aimVector".format(input))
            lookAt_upVec = getattr(self, "{}_upVector".format(input))
            lookAt_upVec_guide = getattr(self, "_{}_upVecTgt".format(input))

            # create an upvector and aim contraint
            upVectorTrs = cmds.createNode("transform", name="{}_upVec".format(lookAt_ctl.trs), p=self.spaces_hrc)
            rig_transform.matchTranslate(lookAt_upVec_guide, upVectorTrs)
            self.UpVecObjList.append(upVectorTrs)

            cmds.aimConstraint(self.aimTarget.name, lookAt_ctl.trs, aim=lookAt_aimVec, upVector=lookAt_upVec,
                               worldUpType='object', worldUpObject=upVectorTrs, mo=True)

            # connect the control to input joint
            joint.connectChains(lookAt_ctl.name, input)
            # rig_transform.connectOffsetParentMatrix(lookAt_ctl[-1], input)

        # Delete the proxy guides_hrc:
        cmds.delete(self.guides_hrc)

    def connect(self):
        """
        connect to the rig parent
        """
        # connect the controls to the rig parent
        if cmds.objExists(self.rigParent):
            for ctl in self.lookAtCtlList:
                rig_transform.connectOffsetParentMatrix(self.rigParent, ctl.orig, mo=True)
            for upVec in self.UpVecObjList:
                rig_transform.connectOffsetParentMatrix(self.rigParent, upVec, mo=True)

        spaces.create(self.aimTarget.spaces, self.aimTarget.name, parent=self.spaces_hrc, defaultName='world')

        if self.lookAtSpaces:
            spaces.addSpace(self.aimTarget.spaces, [self.lookAtSpaces[k] for k in self.lookAtSpaces.keys()], self.lookAtSpaces.keys(), 'parent')

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