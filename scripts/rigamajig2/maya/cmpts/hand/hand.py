"""
hand component
"""
import maya.cmds as cmds
import rigamajig2.maya.cmpts.base
import rigamajig2.maya.cmpts.chain.chain
import rigamajig2.maya.rig.control as rig_control
import rigamajig2.maya.rig.spaces as spaces
import rigamajig2.maya.rig.ikfk as ikfk
import rigamajig2.maya.transform as rig_transform
import rigamajig2.shared.common as common
import rigamajig2.maya.meta as meta
import rigamajig2.maya.container as container

import logging

logger = logging.getLogger(__name__)


class Hand(rigamajig2.maya.cmpts.base.Base):

    def __init__(self, name, input=[], size=1, useProxyAttrs=True, useScale=False, addFKSpace=False, rigParent=str()):
        """
        Hand component.
        The Hand is a system of chain components.

        :param name: name of the components
        :type name: str
        :param input: list of base joints for each finger. Add the joints in order from from pinky to thumb.
        :type input: list
        :param size: default size of the controls:
        :param useProxyAttrs: use proxy attributes instead of an ikfk control
        :type useProxyAttrs: bool
        :param useScale: enable the animator to scale the controls
        :type useScale: bool
        :param addFKSpace: add an FK space switch:
        :type addFKSpace: bool
        """
        super(Hand, self).__init__(name, input=input, size=size, rigParent=rigParent)
        self.side = common.getSide(self.name)

        self.cmptSettings['useProxyAttrs'] = useProxyAttrs
        self.cmptSettings['useScale'] = useScale
        self.cmptSettings['addFKSpace'] = addFKSpace

    def setInitalData(self):
        pass

    def initalHierachy(self):
        """Build the initial hirarchy"""
        super(Hand, self).initalHierachy()

        # disable auto-container placement
        cmds.container(self.container, e=True, c=False)

        # intialize new compoents
        self.finger_cmpt_list = list()
        inputBaseNames = [x.split("_")[0] for x in self.input]
        for i in range(len(self.input)):
            endJoint = cmds.ls(reversed(cmds.listRelatives(self.input[i], ad=True)), type='joint')[-1]

            # initalize a finger component
            finger_name = inputBaseNames[i] + '_' + self.side if self.side else inputBaseNames[i]
            finger_cmpt = rigamajig2.maya.cmpts.chain.chain.Chain(
                finger_name,
                input=[self.input[i], endJoint],
                useScale=self.useScale,
                addFKSpace=self.addFKSpace,
                rigParent=self.rigParent
                )
            finger_cmpt._intialize_cmpt()
            cmds.container(self.container, e=True, f=True, addNode=finger_cmpt.getContainer())
            meta.tag(finger_cmpt.getContainer(), 'subComponent')
            self.finger_cmpt_list.append(finger_cmpt)

    def rigSetup(self):
        for cmpt in self.finger_cmpt_list:
            cmpt._build_cmpt()
            cmds.parent(cmpt.control_hrc, self.control_hrc)
            cmds.parent(cmpt.spaces_hrc, self.spaces_hrc)

            # delete the root hrc from the finger component and re-assign the hand to be the componet root
            cmds.delete(cmpt.root_hrc)
            cmpt.root_hrc = self.root_hrc

    def connect(self):
        for cmpt in self.finger_cmpt_list:
            cmpt._connect_cmpt()

    def finalize(self):
        # navigate around container parenting since we have already parented the containers to the hand container
        for cmpt in self.finger_cmpt_list:
            cmpt.finalize()
            cmpt.setAttrs()
            cmpt.postScript()

    def optimize(self):
        for cmpt in self.finger_cmpt_list:
            cmpt._optimize_cmpt()

    def delete_setup(self):

        for cmpt in self.finger_cmpt_list:
            cmpt.deleteSetup()
        super(Hand, self).deleteSetup()

    @staticmethod
    def createInputJoints(name=None, side=None, numJoints=None):
        """static method to create input joints"""
        import rigamajig2.maya.naming as naming
        import rigamajig2.maya.joint as joint
        GUIDE_POSITIONS = {
            "thumb": (1, 0, 6),
            "index": (2, 0, 2),
            "middle": (2, 0, 0),
            "ring": (2, 0, -2),
            "pinky": (2, 0, -4),
            }
        joints = list()

        for i, finger in enumerate(['thumb', 'index', 'middle', 'ring', 'pinky']):
            parent = None
            jointNum = 6
            if finger == 'thumb':
                jointNum = 5

            for j in range(jointNum):
                name = finger + "_" + side if side else finger
                jnt = cmds.createNode("joint", name=name + "_0")
                if parent:
                    cmds.parent(jnt, parent)

                if j < 1:
                    position = GUIDE_POSITIONS[finger]
                    joints.append(jnt)
                    rootJnt = jnt
                elif j == 2:
                    position = (6, 0, 0)
                    if finger == 'thumb':
                        position = (4, 0, 0)
                elif j == 3:
                    position = (3, 0, 0)
                else:
                    position = (2, 0, 0)

                # apply the postion.
                if side == 'r':
                    position = (position[0] * -1, position[1], position[2])
                cmds.xform(jnt, os=True, t=position)

                parent = jnt

            if side == 'r':
                cmds.setAttr("{}.jox".format(rootJnt), 180)

        return joints
