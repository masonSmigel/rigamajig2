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
    def __init__(self, name, input=[], size=1, rigParent=str(), lookAtSpaces=dict()):
        super(LookAt, self).__init__(name, input=input, size=size, rigParent=rigParent)
        self.side = common.getSide(self.name)

        self.cmptSettings['aimTargetName'] = self.name + "_aim"
        self.cmptSettings['lookAtSpaces'] = lookAtSpaces

        for input in self.input:
            self.cmptSettings['{}Name'.format(input)] = '_'.join(input.split("_")[:-1])
            self.cmptSettings['{}_aimVector'.format(input)] = rig_transform.getVectorFromAxis(
                rig_transform.getAimAxis(input))
            self.cmptSettings['{}_upVector'.format(input)] = (0, 1, 0)

    def createBuildGuides(self):
        """ create build guides_hrc """
        self.guides_hrc = cmds.createNode("transform", name='{}_guide'.format(self.name))

        self._lookAtTgt = rig_control.createGuide("{}_lookAtTgt".format(self.name), parent=self.guides_hrc)
        rig_transform.matchTranslate(self.input, self._lookAtTgt)
        for input in self.input:
            input_upVec = rig_control.createGuide("{}_lookAtTgt".format(input), parent=self.guides_hrc)
            setattr(self, "_{}_upVecTgt".format(input), input_upVec)

    def initalHierachy(self):
        """
        :return:
        """
        self.root_hrc = cmds.createNode('transform', n=self.name + '_cmpt')
        self.control_hrc = cmds.createNode('transform', n=self.name + '_control', parent=self.root_hrc)
        self.spaces_hrc = cmds.createNode('transform', n=self.name + '_spaces', parent=self.root_hrc)

        self.aimTarget = rig_control.createAtObject(self.aimTargetName, self.side,
                                                    hierarchy=['trsBuffer', 'spaces_trs'],
                                                    hideAttrs=['v', 's'], size=self.size, color='banana',
                                                    parent=self.control_hrc, shape='square', shapeAim='z',
                                                    xformObj=self._lookAtTgt)

        self.lookAtCtlList = list()
        for input in self.input:
            lookAtName = getattr(self, "{}Name".format(input))
            aimAxis = rig_transform.getAimAxis(input)
            lookAt_ctl = rig_control.createAtObject(lookAtName, hierarchy=['trsBuffer',  'trsAim'], hideAttrs=['v'], size=self.size,
                                                    color='banana', parent=self.control_hrc, shape='circle',
                                                    shapeAim=aimAxis, xformObj=input)

            # postion the control at the end joint. Get the aim vector from the input and mutiply by joint length.
            translation = mathUtils.scalarMult(rig_transform.getVectorFromAxis(aimAxis), joint.length(input))
            rig_control.translateShapes(lookAt_ctl[-1], translation)

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
            upVectorTrs = cmds.createNode("transform", name="{}_upVec".format(lookAt_ctl[1]), p=self.spaces_hrc)
            rig_transform.matchTranslate(lookAt_upVec_guide, upVectorTrs)
            self.UpVecObjList.append(upVectorTrs)

            cmds.aimConstraint(self.aimTarget[-1], lookAt_ctl[1], aim=lookAt_aimVec, upVector=lookAt_upVec,
                               worldUpType='object', worldUpObject=upVectorTrs, mo=True)

            # connect the control to input joint
            joint.connectChains(lookAt_ctl[-1], input)
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
                rig_transform.connectOffsetParentMatrix(self.rigParent, ctl[0], mo=True)
            for upVec in self.UpVecObjList:
                rig_transform.connectOffsetParentMatrix(self.rigParent, upVec, mo=True)

        spaces.create(self.aimTarget[1], self.aimTarget[-1], parent=self.spaces_hrc, defaultName='world')

        if self.lookAtSpaces:
            spaces.addSpace(self.aimTarget[1], [self.lookAtSpaces[k] for k in self.lookAtSpaces.keys()], self.lookAtSpaces.keys(), 'parent')
