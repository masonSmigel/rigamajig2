"""
chain component
"""
import maya.cmds as cmds
import rigamajig2.maya.cmpts.base
import rigamajig2.maya.rig.control as rig_control
import rigamajig2.maya.rig.spaces as spaces
import rigamajig2.maya.transform as rig_transform
import rigamajig2.shared.common as common
import rigamajig2.maya.node
import rigamajig2.maya.joint

import logging

logger = logging.getLogger(__name__)


class Chain(rigamajig2.maya.cmpts.base.Base):
    VERSION_MAJOR = 1
    VERSION_MINOR = 0
    VERSION_PATCH = 0

    version_info = (VERSION_MAJOR, VERSION_MINOR, VERSION_PATCH)
    version = '%i.%i.%i' % version_info
    __version__ = version

    def __init__(self, name, input=[], size=1, useScale=False, addFKSpace=False, addSdk=True,
                 useProxyAttrs=True, rigParent=str()):
        """
        Fk chain component.
        This is a simple chain component made of only an fk chain.

        :param name: name of the components
        :type name: str
        :param input: list of two joints. A start and an end joint
        :type input: list
        :param size: default size of the controls:
        :type size: float
        :param addFKSpace: add a world/local space switch to the base of the fk chain
        :type addFKSpace: bool
        :param rigParent: node to parent to connect the component to in the heirarchy
        :type rigParent: str
        """
        super(Chain, self).__init__(name, input=input, size=size, rigParent=rigParent)
        self.side = common.getSide(self.name)

        self.cmptSettings['component_side'] = self.side
        # initalize cmpt settings.
        self.cmptSettings['useProxyAttrs'] = useProxyAttrs
        self.cmptSettings['useScale'] = useScale
        self.cmptSettings['addSdk'] = addSdk
        self.cmptSettings['addFKSpace'] = addFKSpace

        # noinspection PyTypeChecker
        if len(self.input) != 2:
            raise RuntimeError('Input list must have a length of 2')

    def setInitalData(self):
        # if the last joint is an end joint dont include it in the list.
        self.inputList = rigamajig2.maya.joint.getInbetweenJoints(self.input[0], self.input[1])
        if rigamajig2.maya.joint.isEndJoint(self.inputList[-1]):
            self.inputList.remove(self.inputList[-1])

        # setup base names for each joint we want to make controls for
        inputBaseNames = [x.split("_")[0] for x in self.inputList]

        self.controlNameList = list()
        for i in range(len(self.inputList)):
            jointNameStr = ("joint{}Name".format(i))
            self.controlNameList.append(jointNameStr)
            self.cmptSettings[jointNameStr] = inputBaseNames[i] + "_fk"

    def initalHierachy(self):
        """Build the initial hirarchy"""
        super(Chain, self).initalHierachy()

        self.fk_control_obj_list = list()
        if self.useScale:
            hideAttrs = ['v']
        else:
            hideAttrs = ['v', 's']

        for i in range(len(self.inputList)):
            parent = self.control_hrc
            addSpaces = True
            if i > 0:
                parent = self.fk_control_obj_list[i - 1].name
                addSpaces = False
            control = rig_control.createAtObject(getattr(self, self.controlNameList[i]), self.side,
                                                 spaces=addSpaces, sdk=self.addSdk, hideAttrs=hideAttrs,
                                                 size=self.size, color='blue', parent=parent, shapeAim='x',
                                                 shape='square', xformObj=self.inputList[i])

            self.fk_control_obj_list.append(control)

        self.controlers = [ctl.name for ctl in self.fk_control_obj_list]

    def rigSetup(self):
        """Add the rig setup"""
        rigamajig2.maya.joint.connectChains(self.controlers, self.inputList)

    def connect(self):
        """Create the connection"""
        # connect the rig to is rigParent
        if cmds.objExists(self.rigParent):
            rig_transform.connectOffsetParentMatrix(self.rigParent, self.fk_control_obj_list[0].orig, mo=True)

        if self.addFKSpace:
            spaces.create(self.fk_control_obj_list[0][1], self.fk_control_obj_list[0].name, parent=self.spaces_hrc)

            # if the main control exists connect the world space
            if cmds.objExists('trs_motion'):
                spaces.addSpace(self.fk_control_obj_list[0].spaces, ['trs_motion'], nameList=['world'],
                                constraintType='orient')

    @staticmethod
    def createInputJoints(name=None, side=None, numJoints=4):
        import rigamajig2.maya.naming as naming
        import rigamajig2.maya.joint as joint
        joints = list()

        parent = None
        for i in range(numJoints):
            name = name or 'chain'
            jointName = naming.getUniqueName("{}_0".format(name))
            jnt = cmds.createNode("joint", name=jointName)

            if parent:
                cmds.parent(jnt, parent)
            if i > 0:
                cmds.xform(jnt, objectSpace=True, t=(0, 5, 0))

            joints.append(jnt)
            parent = jnt

        joint.orientJoints(joints, aimAxis='x', upAxis='y')
        cmds.setAttr("{}.jox".format(joints[0]), -90)
        return [joints[0], joints[-1]]
