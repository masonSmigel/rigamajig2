"""
basic component
"""
import maya.cmds as cmds
import rigamajig2.maya.cmpts.base
import rigamajig2.maya.rig.control as rig_control
import rigamajig2.maya.rig.spaces as spaces
import rigamajig2.maya.rig.ikfk as ikfk
import rigamajig2.maya.transform as rig_transform
import rigamajig2.maya.joint as joint
import rigamajig2.shared.common as common
import rigamajig2.maya.meta as meta

import logging

logger = logging.getLogger(__name__)


class Basic(rigamajig2.maya.cmpts.base.Base):

    def __init__(self, name, input=[], size=1, rigParent=str(),
                 addSpaces=False,  addTrs=False, addSdk=False,
                 controlShape='cube', worldOrient=False):
        """
        Single control component.

        :param name: Component name. To add a side use a side token
        :param input: Single input joint
        :param size:  Default size of the controls.
        :param spacesGrp: add a spaces group
        :param trsGrp: add a trs group
        :param sdkGrp: add an sdk group
        :param rigParent:  Connect the component to a rigParent.
        :param controlShape: Control shape to apply. Default: "cube"
        :param worldOrient: Orient the control to the world. Default: False
        """
        super(Basic, self).__init__(name, input=input, size=size, rigParent=rigParent)
        self.side = common.getSide(self.name)

        inputBaseNames = [x.split("_")[0] for x in self.input]
        self.cmptSettings['controlName'] = inputBaseNames[0]
        self.cmptSettings['controlShape'] = controlShape
        self.cmptSettings['worldOrient'] = worldOrient
        self.cmptSettings['addSpaces'] = addSpaces
        self.cmptSettings['addTrs'] = addTrs
        self.cmptSettings['addSdk'] = addSdk

    def initalHierachy(self):
        super(Basic, self).initalHierachy()

        self.control = rig_control.create(self.controlName, self.side,
                                          spaces=self.addSpaces, trs=self.addTrs, sdk=self.addSdk,
                                          color='blue', parent=self.control_hrc, shape=self.controlShape)

        rig_transform.matchTranslate(self.input[0], self.control.orig)
        if not self.worldOrient:
            rig_transform.matchRotate(self.input[0], self.control.orig)

    def rigSetup(self):
        if self.worldOrient:
            offset = cmds.createNode("transform", n="{}_{}_trs".format(self.controlName, self.side))
            rig_transform.matchTransform(self.input[0], offset)
            cmds.parent(offset, self.control.name)
            joint.connectChains(offset, self.input[0])
        else:
            joint.connectChains(self.control.name, self.input[0])

    def connect(self):
        """Create the connection"""
        # connect the rig to is rigParent
        if cmds.objExists(self.rigParent):
            rig_transform.connectOffsetParentMatrix(self.rigParent, self.control.orig, mo=True)

    @staticmethod
    def createBindJoints(inputJoints):
        """
        Create bind joints from given input joints
        :return:
        """


        pass


    @staticmethod
    def createInputJoints(name=None, side=None, numJoints=4):
        import rigamajig2.maya.naming as naming

        name = name or 'basic'
        jnt = cmds.createNode("joint", name=name + "jnt")

        return [jnt]