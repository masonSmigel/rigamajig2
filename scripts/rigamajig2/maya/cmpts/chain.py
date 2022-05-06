"""
chain component
"""
import maya.cmds as cmds
import maya.mel as mel
import rigamajig2.maya.cmpts.base
import rigamajig2.maya.rig.control as rig_control
import rigamajig2.maya.rig.spaces as spaces
import rigamajig2.maya.rig.ikfk as ikfk
import rigamajig2.maya.transform as rig_transform
import rigamajig2.shared.common as common
import rigamajig2.maya.meta as meta
import rigamajig2.maya.rig.spline as spline
import rigamajig2.maya.node
import rigamajig2.maya.attr as rig_attr
import rigamajig2.maya.joint

import logging

logger = logging.getLogger(__name__)


class Chain(rigamajig2.maya.cmpts.base.Base):

    def __init__(self, name, input=[], size=1, useScale=False, addFKSpace=False,
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

    def connect(self):
        """Create the connection"""
        # connect the rig to is rigParent
        if cmds.objExists(self.rigParent):
            rig_transform.connectOffsetParentMatrix(self.rigParent, self.fk_control_obj_list[0][0], mo=True)

        if self.addFKSpace:
            spaces.create(self.fk_control_obj_list[0][1], self.fk_control_obj_list[0][-1], parent=self.spaces_hrc)

            # if the main control exists connect the world space
            if cmds.objExists('trs_motion'):
                spaces.addSpace(self.fk_control_obj_list[0][1], ['trs_motion'], nameList=['world'], constraintType='orient')


class SplineFK(rigamajig2.maya.cmpts.base.Base):

    def __init__(self, name, input=[], size=1, rigParent=str(), numControls=4, addFKSpace=False):
        """
       Spline fk chain  component.
       This component is made of a longer chain of joints connected through a spline ik handle
       used fk controls to control the clusters of the spline.

       :param name: name of the components
       :param input: list of two joints. A start and an end joint
       :type input: list
       :param size: default size of the controls:
       :type size: float
       :param: numControls: number of controls to add along the spline
       :param addFKSpace: add a world/local space switch to the fk chain
       :type addFKSpace: bool
       """
        super(SplineFK, self).__init__(name, input=input, size=size, rigParent=rigParent)
        self.side = common.getSide(self.name)
        self.cmptSettings['component_side'] = self.side

        # initalize cmpt settings
        self.cmptSettings['numControls'] = numControls

        self.cmptSettings['fkControlName'] = "{}_fk_0".format(self.name)
        self.cmptSettings['ikControlName'] = "{}_ik_0".format(self.name)

        self.cmptSettings['addFKSpace'] = addFKSpace

        self.inputList = rigamajig2.maya.joint.getInbetweenJoints(self.input[0], self.input[1])

        # noinspection PyTypeChecker
        if len(self.input) != 2:
            raise RuntimeError('Input list must have a length of 2')

    def createBuildGuides(self):
        """Create the build guides"""

        self.guides_hrc = cmds.createNode("transform", name='{}_guide'.format(self.name))

        pos = cmds.xform(self.inputList[0], q=True, ws=True, t=True)
        self.up_vec_guide = rig_control.createGuide(self.name + "_upVector", parent=self.guides_hrc,
                                                    position=pos)

    def initalHierachy(self):
        """Build the initial hirarchy"""
        self.root_hrc = cmds.createNode('transform', n=self.name + '_cmpt')
        self.params_hrc = cmds.createNode('transform', n=self.name + '_params', parent=self.root_hrc)
        self.control_hrc = cmds.createNode('transform', n=self.name + '_control', parent=self.root_hrc)
        self.spaces_hrc = cmds.createNode('transform', n=self.name + '_spaces', parent=self.root_hrc)

        self.fk_control_obj_list = list()
        self.ik_control_obj_list = list()

        hideAttrs = ['v', 's']
        for i in range(self.numControls):
            parent = self.control_hrc
            hierarchy = ['trsBuffer', 'spaces_trs']
            if i > 0:
                parent = self.fk_control_obj_list[i - 1][-1]
                hierarchy = ['trsBuffer']
            fk_control = rig_control.create(self.fkControlName, hierarchy=hierarchy, hideAttrs=hideAttrs,
                                            size=self.size, color='blue', parent=parent, shapeAim='x',
                                            shape='square')
            ik_control = rig_control.create(self.ikControlName, hierarchy=[], hideAttrs=hideAttrs,
                                            size=self.size * 0.5, color='blue', parent=fk_control[-1], shapeAim='x',
                                            shape='circle')
            self.fk_control_obj_list.append(fk_control)
            self.ik_control_obj_list.append(ik_control)

        self.fkControls = [ctl[-1] for ctl in self.fk_control_obj_list]
        self.ikControls = [ctl[-1] for ctl in self.ik_control_obj_list]

    def rigSetup(self):
        self.ikspline = spline.SplineBase(self.inputList, name=self.name)
        self.ikspline.setGroup(self.name + '_ik')
        self.ikspline.create(clusters=self.numControls, params=self.params_hrc)
        cmds.parent(self.ikspline.getGroup(), self.root_hrc)

        aim = rig_transform.getAimAxis(self.inputList[0])
        up = rig_transform.getClosestAxis(self.inputList[0], self.up_vec_guide)

        aim_vector = rig_transform.getVectorFromAxis(aim)
        up_vector = rig_transform.getVectorFromAxis(up)

        # setup the controls
        for i in range(len(self.ikspline.getClusters())):
            tmp_obj = cmds.createNode("transform", n="{}_temp_trs".format(self.name))
            rig_transform.matchTransform(self.ikspline.getClusters()[i], tmp_obj)

            if i == len(self.ikspline.getClusters()) - 1:
                target = self.ikspline.getClusters()[i - 1]
                # flip the anim vector
                aim_vector = [v * -1 for v in aim_vector]
            else:
                target = self.ikspline.getClusters()[i + 1]

            const = cmds.aimConstraint(target, tmp_obj, aimVector=aim_vector, upVector=up_vector,
                                       worldUpType='object', worldUpObject=self.up_vec_guide, mo=False, w=1)
            cmds.delete(const)

            # setup the rig connections
            rig_transform.matchTransform(tmp_obj, self.fk_control_obj_list[i][0])
            cmds.parent(self.ikspline.getClusters()[i], self.ik_control_obj_list[i][-1])

            # delete temp objects
            cmds.delete(tmp_obj)

        # connect the orientation of the controls to the rig
        cmds.orientConstraint(self.fk_control_obj_list[0][-1], self.ikspline._startTwist, mo=True)
        cmds.orientConstraint(self.fk_control_obj_list[-1][-1], self.ikspline._endTwist, mo=True)

        # setup the ik visablity attribute
        rig_attr.addAttr(self.fk_control_obj_list[0][-1], "ikVis", "bool", value=0, keyable=False, channelBox=True)

        for control in self.ikControls:
            rig_control.connectControlVisiblity(self.fkControls[0], "ikVis", control)

        # delete the guides
        cmds.delete(self.guides_hrc)

    def connect(self):
        """Create the connection"""
        # connect the rig to is rigParent
        if cmds.objExists(self.rigParent):
            rig_transform.connectOffsetParentMatrix(self.rigParent, self.fk_control_obj_list[0][0], s=False, sh=False, mo=True)

        if self.addFKSpace:
            spaces.create(self.fk_control_obj_list[0][1], self.fk_control_obj_list[0][-1], parent=self.spaces_hrc)

            # if the main control exists connect the world space
            if cmds.objExists('trs_motion'):
                spaces.addSpace(self.fk_control_obj_list[0][1], ['trs_motion'], nameList=['world'], constraintType='orient')


if __name__ == '__main__':
    import rigamajig2; rigamajig2.reloadModule()
    try:
        cmpt.deleteSetup()
    except:
        pass

    cmpt = SplineFK('tail', input=['joint1', 'joint2'], numControls=8)

    cmpt._intialize_cmpt()
    cmpt._build_cmpt()
