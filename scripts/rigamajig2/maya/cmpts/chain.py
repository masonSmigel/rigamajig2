"""
chain component
"""
import maya.cmds as cmds
import rigamajig2.maya.cmpts.base
import rigamajig2.maya.rig.control as rig_control
import rigamajig2.maya.rig.spaces as spaces
import rigamajig2.maya.rig.ikfk as ikfk
import rigamajig2.maya.transform as rig_transform
import rigamajig2.shared.common as common
import rigamajig2.maya.meta as meta
import rigamajig2.maya.node
import rigamajig2.maya.attr
import rigamajig2.maya.joint

import logging

logger = logging.getLogger(__name__)


class Chain(rigamajig2.maya.cmpts.base.Base):

    def __init__(self, name, input=[], size=1, useScale=False, addFKSpace=False,
                 useProxyAttrs=True, rigParent=str()):
        """
        Create a chain component
        :param name: name of the components
        :type name: str
        :param input: list of two joints. A start and an end joint
        :type input: list
        :param size: default size of the controls:
        :type size: float
        :param: ikSpaces: dictionary of key and space for the ik control.
        :param useProxyAttrs: use proxy attributes instead of an ikfk control
        :type useProxyAttrs: bool
        """
        super(Chain, self).__init__(name, input=input, size=size, rigParent=rigParent)
        self.side = common.getSide(self.name)

        self.cmptData['component_side'] = self.side
        # initalize cmpt settings.
        self.cmptSettings['useProxyAttrs'] = useProxyAttrs
        self.cmptSettings['useScale'] = useScale
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
        self.root_hrc = cmds.createNode('transform', n=self.name + '_cmpt')
        self.params_hrc = cmds.createNode('transform', n=self.name + '_params', parent=self.root_hrc)
        self.control_hrc = cmds.createNode('transform', n=self.name + '_control', parent=self.root_hrc)
        self.spaces_hrc = cmds.createNode('transform', n=self.name + '_spaces', parent=self.root_hrc)

        self.fk_control_obj_list = list()
        if self.useScale:
            hideAttrs = ['v']
        else:
            hideAttrs = ['v', 's']

        for i in range(len(self.inputList)):
            parent = self.control_hrc
            heirarchy = ['trsBuffer', 'spaces_trs']
            if i > 0:
                parent = self.fk_control_obj_list[i - 1][-1]
                heirarchy = ['trsBuffer']
            control = rig_control.createAtObject(getattr(self, self.controlNameList[i]), self.side,
                                                 hierarchy=heirarchy, hideAttrs=hideAttrs,
                                                 size=self.size, color='blue', parent=parent, shapeAim='x',
                                                 shape='square', xformObj=self.inputList[i])

            self.fk_control_obj_list.append(control)

        self.fkControls = [ctl[-1] for ctl in self.fk_control_obj_list]

    def rigSetup(self):
        """Add the rig setup"""
        rigamajig2.maya.joint.connectChains(self.fkControls, self.inputList)

    def postRigSetup(self):
        """ Connect the blend chain to the bind chain"""
        pass

    def setupAnimAttrs(self):
        pass

    def connect(self):
        """Create the connection"""
        # connect the rig to is rigParent
        if cmds.objExists(self.rigParent):
            rig_transform.connectOffsetParentMatrix(self.rigParent, self.fk_control_obj_list[0][0], mo=True)

        if self.addFKSpace:
            spaces.create(self.fk_control_obj_list[0][1], self.fk_control_obj_list[0][-1], parent=self.spaces_hrc)

            # if the main control exists connect the world space
            if cmds.objExists('trs_motion'):
                spaces.addSpace(self.fk_control_obj_list[0][1], ['trs_motion'], nameList=['world'],
                                constraintType='orient')

    def finalize(self):
        """ Lock some attributes we dont want to see"""
        pass

    def showAdvancedProxy(self):
        """Show Advanced Proxy"""
        pass

    def setAttrs(self):
        """ Set some attributes to values that make more sense for the inital setup."""
        pass
