"""
Module for Ik/Fk stuff
"""

import maya.cmds as cmds
import maya.api.OpenMaya as om2
from maya.api.OpenMaya import MVector

import rigamajig2.shared.common as common
import rigamajig2.maya.hierarchy as rig_hierarchy
import rigamajig2.maya.transform as transform
import rigamajig2.maya.node as node
import rigamajig2.maya.joint as joint
import rigamajig2.maya.mathUtils as mathUtils
import rigamajig2.maya.debug as debug
import rigamajig2.maya.meta as meta


class IkFkBase(object):
    """
    This is a the base class for out Ik Fk solvers
    """

    def __init__(self, jointList, name='ikfk'):
        """
        default constructor
        :param jointList: list of joints to create ikfk setup from
        :type jointList: list
        :param name: name of the setup
        """

        self.setJointList(jointList)
        self._ikJointList = list()
        self._fkJointList = list()
        self._blendJointList = list()
        self._group = name + '_hrc'

    # GET
    def getJointList(self):
        """
        Return a list of joints used or created
        :return: list of joints
        :rtype: list
        """
        return self._jointList

    def getIkJointList(self):
        """
        Return a list of Ik joints used or created
        :return: list of joints
        :rtype: list
        """
        return self._ikJointList

    def getFkJointList(self):
        """
        Return a list of FK joints used or created
        :return: list of joints
        :rtype: list
        """
        return self._fkJointList

    def getBlendJointList(self):
        """
        Return a list of blend joints used or created
        :return: list of joints
        :rtype: list
        """
        return self._blendJointList

    def getGroup(self):
        """
        Return the group
        :return: group
        :rtype: str
        """
        return self._group

    # SET
    def setJointList(self, value):
        """
        Set the self._jointList attribute to a given list of joints
        :param value: list of joints to create/use in this instance
        :type value: list
        """
        if not isinstance(value, (list, tuple)):
            raise TypeError("{} must be a list or tuple".format(value))
        self._jointList = value

    def setIkJointList(self, value):
        """
        Set the self._ikJointList attribute to a given list of joints
        :param value: list of joints to create/use in this instance
        :type value: list
        """
        if not isinstance(value, (list, tuple)):
            raise TypeError("{} must be a list or tuple".format(value))
        self._ikJointList = value

    def setFkJointList(self, value):
        """
        Set the self._fkJointList attribute to a given list of joints
        :param value: list of joints to create/use in this instance
        :type value: list
        """
        if not isinstance(value, (list, tuple)):
            raise TypeError("{} must be a list or tuple".format(value))
        self._fkJointList = value

    def setBlendJointList(self, value):
        """
        Set the self._blendJointList attribute to a given list of joints
        :param value: list of joints to create/use in this instance
        :type value: list
        """
        if not isinstance(value, (list, tuple)):
            raise TypeError("{} must be a list or tuple".format(value))
        self._blendJointList = value

    def setGroup(self, value):
        """
        Set the attribtue self._group to the given name
        :return:
        """
        if not isinstance(value, basestring):
            raise TypeError("{} must be a str".format(value))
        if cmds.objExists(self._group) and value != self._group:
            cmds.rename(self._group, value)
        self._group = value

    def create(self):
        """
        This will create the ik/fkControls joints and connect them to the blendchain.
        IT WILL NOT RIG THEM in any way
        """
        if not cmds.objExists(self._group):
            cmds.createNode("transform", name=self._group)

        ikfkAttr = "{}.ikfk".format(self._group)

        if not cmds.objExists(ikfkAttr):
            cmds.addAttr(self._group, ln='ikfk', at='double', min=0, max=1, keyable=True)

        fkParent = self._group
        ikParent = self._group
        blendParent = self._group

        for joint in self._jointList:
            if not cmds.objExists(joint):
                continue

            # create the FK setup
            fkJnt = "{}_fk".format(joint)
            if not cmds.objExists(fkJnt):
                cmds.duplicate(joint, parentOnly=True, returnRootsOnly=True, name=fkJnt)
                cmds.parent(fkJnt, fkParent)
            self._fkJointList.append(fkJnt)
            fkParent = fkJnt

            # create the Ik setup
            ikJnt = "{}_ik".format(joint)
            if not cmds.objExists(ikJnt):
                cmds.duplicate(joint, parentOnly=True, returnRootsOnly=True, name=ikJnt)
                cmds.parent(ikJnt, ikParent)
            self._ikJointList.append(ikJnt)
            ikParent = ikJnt

            # create the blend setup
            blendJntExists = False
            blendJnt = "{}_blend".format(joint)
            if not cmds.objExists(blendJnt):
                cmds.duplicate(joint, parentOnly=True, returnRootsOnly=True, name=blendJnt)
                cmds.parent(blendJnt, blendParent)
            else:
                blendJntExists = True
            self._blendJointList.append(blendJnt)
            blendParent = blendJnt

            debug.hide([fkJnt, ikJnt, blendJnt])

            # connect the IKFK joints to the blend joint
            if not blendJntExists:
                # create a blend matrix node
                blendMatrix = cmds.createNode("blendMatrix", n='{}_blendMatrix'.format(blendJnt))
                cmds.connectAttr("{}.{}".format(ikJnt, 'worldMatrix'), "{}.{}".format(blendMatrix, "inputMatrix"), f=True)
                cmds.connectAttr("{}.{}".format(fkJnt, 'worldMatrix'), "{}.{}".format(blendMatrix, "target[0].targetMatrix"), f=True)
                cmds.connectAttr(ikfkAttr, "{}.{}".format(blendMatrix, "target[0].weight"), f=True)

                # if the node has a parent create a mult matrix to account for the offset
                parent = cmds.listRelatives(blendJnt, parent=True, path=True)[0] or None
                if parent:
                    mm = cmds.createNode("multMatrix", name="{}_mm".format(blendJnt))
                    cmds.connectAttr("{}.{}".format(blendMatrix, 'outputMatrix'), "{}.{}".format(mm, 'matrixIn[0]'), f=True)
                    cmds.connectAttr("{}.{}".format(parent, 'worldInverseMatrix'), "{}.{}".format(mm, 'matrixIn[1]'), f=True)
                    cmds.connectAttr("{}.{}".format(mm, 'matrixSum'), "{}.{}".format(blendJnt, 'offsetParentMatrix'), f=True)
                else:
                    cmds.connectAttr("{}.{}".format(blendMatrix, "outputMatrix"), "{}.{}".format(blendJnt, "offsetParentMatrix"))

                # reset the transformations
                transform.resetTransformations(blendJnt)
                for attr in ['{}{}'.format(x, y) for x in 'trs' for y in 'xyz']:
                    cmds.setAttr("{}.{}".format(blendJnt, attr), e=True, lock=True)

    @staticmethod
    def connectVisibility(attrHolder, attr='ikfk', ikList=[], fkList=[]):
        """
        Connect the fkControls and Ik visibility. Mostly used for controls
        :param attrHolder: node that holds the attribute
        :param attr: node to switch between ik and fkControls
        :param ikList: list of ik controls
        :param fkList: list of fkControls controls
        """
        if not cmds.objExists(attrHolder):
            raise RuntimeError('Node {} does not exist'.format(attrHolder))
        if not cmds.objExists("{}.{}".format(attrHolder, attr)):
            raise RuntimeError('attribute "{}.{}" does not exist'.format(attrHolder, attr))

        if not cmds.objExists("{}.ikVisNode".format(attrHolder)):
            rev = node.reverse("{}.{}".format(attrHolder, attr), name="{}_{}".format(attrHolder, attr))
            meta.addMessageConnection(attrHolder, rev, 'ikfkReverseNode')
        else:
            rev = meta.getMessageConnection('{}.ikVisNode'.format(attrHolder))

        for ikNode in ikList:
            shapes = cmds.listRelatives(ikNode, s=True)
            for shape in shapes:
                cmds.connectAttr("{}.{}".format(rev, 'outputX'), "{}.{}".format(shape, 'v'))

        for fkNode in fkList:
            shapes = cmds.listRelatives(fkNode, s=True) or []
            for shape in shapes:
                cmds.connectAttr("{}.{}".format(attrHolder, attr), "{}.{}".format(shape, 'v'))


class IkFkLimb(IkFkBase):
    """
    This class creates a blending ik/fkControls system with a rotate plane solver
    """

    def __init__(self, jointList):
        super(IkFkLimb, self).__init__(jointList)

        self._handle = str()
        self._effector = str()

    def getHandle(self):
        """
        This will return the ikHandle
        :return: name of the ikHandle
        """
        return self._handle

    def getEffector(self):
        """
        This will return the ikEffector
        :return: name of the ikEffector
        """
        return self._effector

    def setJointList(self, value):
        """
        Set the self._jointList attribute to a given list of joints.
        Checks the length of the joint list to ensure only 3 joints are in the list
        :param value: list of joints to create/use in this instance
        :type value: list
        """
        if len(value) != 3:
            raise RuntimeError("Joint list be have a length of 3")

        super(IkFkLimb, self).setJointList(value)

    def create(self):
        """
        Create an IkFK chain with an ikHandle using the ikRPsolver
        :return:
        """
        if not self._ikJointList:
            super(IkFkLimb, self).create()

        guess_hdl = "{}_hdl".format(self._ikJointList[-1])
        if not cmds.objExists(guess_hdl):
            self._handle, self._effector = cmds.ikHandle(sj=self._ikJointList[0], ee=self._ikJointList[-1],
                                                         sol='ikRPsolver',
                                                         name=guess_hdl)
            cmds.parent(self._handle, self._group)
        else:
            self._handle = guess_hdl

    @staticmethod
    def createStretchyIk(ikHandle, grp=None):
        """
        Create a 2Bone stretchy ik from an  ikHandle
        :param ikHandle: Ikhandle to turn into a stretchy chain
        :param grp: Optional-group to hold attributes and calculate scale
        :return: target joints created
        """
        # get the joints influenced by the IK handle
        jnts = IkFkLimb.getJointsFromHandle(ikHandle)
        pvNode = IkFkLimb.getPoleVectorFromHandle(ikHandle)
        if not grp or not cmds.objExists(grp):
            grp = cmds.createNode("transform", name='ikfk_stretch_hrc')

        # check if our joints are clean. If not return a warning but we can continue.

        if not joint.isClean(jnts[1]) or not joint.isClean(jnts[2]):
            cmds.warning("Some joints have dirty transformations. Stretch may not work as expected")

        cmds.addAttr(grp, ln='stretch', at='double', dv=1, min=0, max=1, k=True)
        cmds.addAttr(grp, ln='stretchTop', at='double', dv=1, k=True)
        cmds.addAttr(grp, ln='stretchBot', at='double', dv=1, k=True)
        cmds.addAttr(grp, ln='softStretch', at='double', dv=.001, min=.001, max=1, k=True)
        cmds.addAttr(grp, ln='softStretchCompensate', at='double', dv=0, min=-1, max=0, k=False)
        stretchAttr = '{}.stretch'.format(grp)
        stretchTopAttr = '{}.stretchTop'.format(grp)
        stretchBotAttr = '{}.stretchBot'.format(grp)
        softStretchAttr = '{}.softStretch'.format(grp)
        softStretchCompensateAttr = '{}.softStretchCompensate'.format(grp)

        # create target joints for the distance calulation
        startTgt = cmds.createNode('joint', n="{}_{}".format(jnts[0], common.TARGET))
        endTgt = cmds.createNode('joint', n="{}_{}".format(jnts[2], common.TARGET))
        transform.matchTranslate(jnts[0], startTgt)
        transform.matchTranslate(jnts[2], endTgt)

        # create a distance between node to get the hypontonouse
        distbtwn = node.distance(startTgt, endTgt, name=ikHandle + "_full")

        # get the scale from the world matrix and divide
        scale = node.decomposeMatrix("{}.worldMatrix[0]".format(grp), name=grp + '_scale')
        normScale = node.multiplyDivide("{}.distance".format(distbtwn), "{}.outputScaleX".format(scale),
                                        operation='div', name=grp + '_normScale')

        # get default joint distances and mutliply the distance by the stretch
        aimAxis = transform.getAimAxis(jnts[1], allowNegative=False)
        jnt1Dist = cmds.getAttr('{}.t{}'.format(jnts[1], aimAxis))
        jnt2Dist = cmds.getAttr('{}.t{}'.format(jnts[2], aimAxis))
        jntLength = jnt1Dist + jnt2Dist

        # if a pole vector node is found add the pv setup!
        if pvNode:
            # add pole vector pinning attributes
            cmds.addAttr(grp, ln='pvPin', at='double', dv=0, min=0, max=1, k=True)
            pvPinAttr = '{}.pvPin'.format(grp)

            # get the distance from the joint3_fk and joint1_fk to pole vector
            pvdcmp = node.decomposeMatrix("{}.{}".format(pvNode, 'worldMatrix'), name=pvNode)
            jnt1PvDist = node.distance(startTgt, "{}.{}".format(pvdcmp, 'outputTranslate'), name=grp + '_upperPvPin')
            jnt2PvDist = node.distance(endTgt, "{}.{}".format(pvdcmp, 'outputTranslate'), name=grp + '_lowerPvPin')

            # get the pole vector distance as a multiplier
            pvMultiplier = node.multiplyDivide(
                ["{}.{}".format(jnt1PvDist, 'distance'), "{}.{}".format(jnt2PvDist, 'distance'), 1],
                [abs(jnt1Dist), abs(jnt2Dist), 1], operation='div', name=grp + '_pvDist')

            normPvScale = node.multiplyDivide("{}.{}".format(pvMultiplier, "output"), "{}.outputScale".format(scale),
                                              operation='div', name=grp + '_pvNormScale')

            # create a blend between the multipler and 1
            pvDistBlend = node.blendColors([1, 1, 1],
                                           ["{}.{}".format(normPvScale, 'outputX'),
                                            "{}.{}".format(normPvScale, 'outputY'), 1],
                                           weight=pvPinAttr, name=grp + '_pvBlend')

            # get the proper multipler. normalized with the TopStretch and BotStretch
            jnt1multiplier = node.plusMinusAverage1D(
                [-1, stretchTopAttr, str("{}.{}".format(pvDistBlend, 'outputR')), softStretchCompensateAttr],
                operation='sum', name=jnts[1] + '_lenMult')
            jnt2multiplier = node.plusMinusAverage1D(
                [-1, stretchBotAttr, str("{}.{}".format(pvDistBlend, 'outputG')), softStretchCompensateAttr],
                operation='sum', name=jnts[2] + '_lenMult')

            # connect the final multipler to the base length of the joint.
            jnt1baseLen = node.multDoubleLinear("{}.{}".format(jnt1multiplier, 'output1D'), jnt1Dist,
                                                name=jnts[1] + '_baseLen')
            jnt2baseLen = node.multDoubleLinear("{}.{}".format(jnt2multiplier, 'output1D'), jnt2Dist,
                                                name=jnts[2] + '_baseLen')
        else:
            jnt1baseLen = node.multDoubleLinear(stretchTopAttr, jnt1Dist, name=jnts[1] + '_baseLen')
            jnt2baseLen = node.multDoubleLinear(stretchBotAttr, jnt2Dist, name=jnts[2] + '_baseLen')

        actualDist = node.addDoubleLinear('{}.output'.format(jnt1baseLen), '{}.output'.format(jnt2baseLen),
                                          name=ikHandle + '_actualDist')
        # get the soft distance (full distance - the actual distance - )
        softDist = node.plusMinusAverage1D(['{}.output'.format(actualDist), softStretchAttr], operation='sub',
                                           name=ikHandle + '_softDist')

        # Get the soft distance
        softDistSoftP = node.plusMinusAverage1D(["{}.outputX".format(normScale), "{}.output1D".format(softDist)],
                                                operation='sub', name=ikHandle + '_softDist_softP')
        softPDiv = node.multiplyDivide("{}.output1D".format(softDistSoftP), softStretchAttr, operation='div',
                                       name=ikHandle + '_softPDiv')
        softPInv = node.multDoubleLinear("{}.outputX".format(softPDiv), -1, name=ikHandle + "_softPDivInvert")
        exponent = node.multiplyDivide(2.718, "{}.output".format(softPInv), operation='pow',
                                       name=ikHandle + '_exponent')
        scaleMult = node.multDoubleLinear("{}.outputX".format(exponent), softStretchAttr, name=ikHandle + '_scale')
        addStretch = node.plusMinusAverage1D(["{}.output".format(actualDist), '{}.output'.format(scaleMult)],
                                             operation='sub', name=ikHandle + '_addStretch')
        multiplier = node.multiplyDivide("{}.outputX".format(normScale), "{}.output1D".format(addStretch),
                                         operation='div', name=ikHandle + '_multiplier')
        # get stretch joint length
        jnt1length = node.multDoubleLinear("{}.outputX".format(multiplier), "{}.output".format(jnt1baseLen),
                                           name=jnts[1] + '_len')
        jnt2length = node.multDoubleLinear("{}.outputX".format(multiplier), "{}.output".format(jnt2baseLen),
                                           name=jnts[2] + '_len')
        cond = node.condition(firstTerm="{}.outputX".format(normScale), secondTerm="{}.output1D".format(softDist),
                              ifTrue=["{}.output".format(jnt1length), "{}.output".format(jnt2length), 0],
                              ifFalse=["{}.output".format(jnt1baseLen), "{}.output".format(jnt2baseLen), 0],
                              operation='>', name=ikHandle)
        blendColors = node.blendColors(input1=["{}.output".format(jnt1baseLen), "{}.output".format(jnt2baseLen), 0],
                                       input2=["{}.outColorR".format(cond), "{}.outColorG".format(cond), 0],
                                       weight=stretchAttr, name=ikHandle)

        # if the joints are negative then adjust accordingly
        if jntLength < 0:
            # create a mult node to flip the sign of the ikdistance
            negDistanceFlip = node.multDoubleLinear("{}.outputX".format(normScale), -1,
                                                    name=grp + "_distNeg")
            cmds.connectAttr("{}.output".format(negDistanceFlip), "{}.input1X".format(multiplier), f=True)
            cmds.connectAttr("{}.output".format(negDistanceFlip), "{}.firstTerm".format(cond), f=True)
            # If the joints are negative then adjust the opperation to less than and sum.
            cmds.setAttr("{}.operation".format(cond), 4)
            cmds.setAttr("{}.operation".format(softDistSoftP), 1)
            cmds.setAttr("{}.operation".format(softDist), 1)
            cmds.setAttr("{}.operation".format(addStretch), 1)

        # Connect the output to the translate of the joint.
        cmds.connectAttr("{}.outputR".format(blendColors), "{}.t{}".format(jnts[1], aimAxis), f=True)
        cmds.connectAttr("{}.outputG".format(blendColors), "{}.t{}".format(jnts[2], aimAxis), f=True)

        # parent the ikHandle to the endTgt
        cmds.parent(ikHandle, endTgt)

        # Hide the targets and parent them under the group.
        for jnt in [startTgt, endTgt]:
            cmds.setAttr('{}.drawStyle'.format(jnt), 2)
            cmds.parent(jnt, grp)
        cmds.setAttr("{}.v".format(ikHandle), 0)

        return [startTgt, endTgt]

    @staticmethod
    def getPoleVectorPos(matchList, magnitude=10):
        """
        Return the position for a pole vector
        :param matchList: list of transforms to get pole vector position from
        :param magnitude: magnitute (aka distance from mid joint to pole vector)
        :return: world space position for the pole vector
        """
        if len(matchList) != 3:
            raise RuntimeError("Joint list be have a length of 3")
        start = cmds.xform(matchList[0], q=True, ws=True, t=True)
        mid = cmds.xform(matchList[1], q=True, ws=True, t=True)
        end = cmds.xform(matchList[2], q=True, ws=True, t=True)

        start_vector = om2.MVector(*start)
        mid_vector = om2.MVector(*mid)
        end_vector = om2.MVector(*end)

        line = (end_vector - start_vector)
        point = (mid_vector - start_vector)

        scale_value = (line * point) / (line * line)
        proj_vec = (line * scale_value) + start_vector

        avLen = ((start_vector - mid_vector).length() + (mid_vector - end_vector).length())
        pv_pos = ((mid_vector - proj_vec).normal() * (magnitude + avLen)) + mid_vector

        return pv_pos

    @staticmethod
    def match_magnitude(vector, magnitude, attempts=20):
        """
        Match the magnitude of a vector to a given value
        :param vector: vector to match magnitude of
        :param magnitude: goal magnitude to match
        :param attempts: Optional - number of itterations to match magnitude of vector
        :return: vector matching the maginitude (or as close as it can get within the attemps)
        """
        if not vector.length() >= magnitude and attempts > 0:
            vector = vector * 2
            return IkFkLimb.match_magnitude(vector, magnitude, attempts - 1)
        return vector

    @staticmethod
    def getJointsFromHandle(ikHandle):
        """
        Get Joints affected by the ikHandle
        :param ikHandle: Ik handle to get the joints from
        :return: list of joints affected by the Ik handle
        """
        if not cmds.objExists(ikHandle): raise Exception('ikHandle {} does not exist'.format(ikHandle))
        if cmds.objectType(ikHandle) != 'ikHandle': raise Exception(
            'Object {} is not a valid ikHandle'.format(ikHandle))

        # get the start joint
        joints = cmds.ikHandle(ikHandle, q=True, jointList=True)
        joints.append(cmds.listRelatives(joints[-1], c=True, type='joint')[0])

        return joints

    @staticmethod
    def getPoleVectorFromHandle(ikHandle):
        """
        Get Pole Vector affecting the ikHandle
        :param ikHandle: Ik handle to get the pole vector from
        :return: list of joints affected by the Ik handle
        """
        if not cmds.objExists(ikHandle): raise Exception('ikHandle {} does not exist'.format(ikHandle))
        if cmds.objectType(ikHandle) != 'ikHandle': raise Exception(
            'Object {} is not a valid ikHandle'.format(ikHandle))
        connected = cmds.listConnections("{}.{}".format(ikHandle, 'poleVectorX'), s=True)
        if connected:
            node = cmds.listConnections("{}.{}".format(connected[0], 'target[0].targetTranslate'), s=True)
            return node[0]
        return None

    @staticmethod
    def getPoleVectorPosFromHandle(ikHandle, magnitude=10):
        """
        Get the pole vector position from an ikHandle
        :param ikHandle: Ik handle to get the joints from
        :param magnitude: magnitute (aka distance from mid joint to pole vector)
        :return:
        """
        jointList = IkFkLimb.getJointsFromHandle(ikHandle)
        pv_pos = IkFkLimb.getPoleVectorPos(jointList, magnitude)
        return pv_pos


class IkFkFoot(IkFkBase):
    def __init__(self, jointList, heelPivot=None, innPivot=None, outPivot=None):
        super(IkFkFoot, self).__init__(jointList)

        self.setJointList(jointList)
        self._handles = list()
        self.ankleHandle = str()
        self._pivotList = list()

        # additional pivots
        self._heel_piviot = heelPivot
        self._inn_piviot = innPivot
        self._out_piviot = outPivot

    def getHandles(self):
        return self._handles

    def setPiviotList(self, value):
        if len(value) != 8:
            raise RuntimeError("Piviot list be have a length of 8")

        self._pivotList = value

    def getPivotList(self):
        return self._pivotList

    def setJointList(self, value):
        """
       Set the self._jointList attribute to a given list of joints.
       Checks the length of the joint list to ensure only 3 joints are in the list
       :param value: list of joints to create/use in this instance
       :type value: list
       """
        if len(value) != 3:
            raise RuntimeError("Joint list be have a length of 3")

        super(IkFkFoot, self).setJointList(value)

    def create(self):
        """
        construct the ikfk system
        """
        if not self._ikJointList:
            super(IkFkFoot, self).create()

        ankleConnections = cmds.listConnections("{}.tx".format(self._ikJointList[0]), source=False, destination=True)
        if ankleConnections:
            effectors = cmds.ls(ankleConnections, type='ikEffector')
            if effectors:
                self.ankleHandle = cmds.listConnections("{}.handlePath[0]".format(effectors[0]))[0]

        if not self._pivotList:
            self.createPiviots()

        if not self._handles:
            self._handles.append(cmds.ikHandle(sj=self._ikJointList[0], ee=self._ikJointList[1],
                                               sol='ikSCsolver', name='{}_hdl'.format(self._ikJointList[1]))[0])
            self._handles.append(cmds.ikHandle(sj=self._ikJointList[1], ee=self._ikJointList[2],
                                               sol='ikSCsolver', name='{}_hdl'.format(self._ikJointList[2]))[0])

            # unlock the ik handle
            cmds.setAttr(self.ankleHandle + '.tx', l=0)
            cmds.setAttr(self.ankleHandle + '.ty', l=0)
            cmds.setAttr(self.ankleHandle + '.tz', l=0)

            # parent stuff
            cmds.parent(self._handles[1], self._pivotList[-1])
            if cmds.objExists(self.ankleHandle):
                cmds.parent(self.ankleHandle, self._pivotList[-2])
            cmds.parent(self._handles[0], self._pivotList[-2])

            for handle in self._handles:
                cmds.setAttr("{}.v".format(handle), 0)

    @staticmethod
    def createFootRoll(pivotList, grp=None):
        """
        Create our advanced footroll setup
        :param pivotList: list of foot pivots
        :param grp: Optional-group to hold attributes and calculate scale
        :return:
        """
        if len(pivotList) != 8:
            raise RuntimeError("Pivot list must have a length of 8")

        if not grp or not cmds.objExists(grp):
            grp = cmds.createNode("transform", name='ikfk_foot_hrc')

        cmds.addAttr(grp, ln='roll', at='double', dv=0, min=-90, max=180, k=True)
        cmds.addAttr(grp, ln='bank', at='double', dv=0, k=True)
        cmds.addAttr(grp, ln='ballAngle', at='double', dv=45, min=0, k=True)
        cmds.addAttr(grp, ln='toeStraightAngle', at='double', dv=70, min=0, k=True)
        rollAttr = '{}.roll'.format(grp)
        ballAngleAttr = '{}.ballAngle'.format(grp)
        toeStraightAngleAttr = '{}.toeStraightAngle'.format(grp)
        bankAttr = '{}.bank'.format(grp)

        # Setup the bank
        bankCond = node.condition(bankAttr, 0, ifTrue=[bankAttr, 0, 0], ifFalse=[0, bankAttr, 0], operation='>',
                                  name="{}_bank".format(grp))
        cmds.connectAttr("{}.outColorR".format(bankCond), "{}.rz".format(pivotList[2]))
        cmds.connectAttr("{}.outColorG".format(bankCond), "{}.rz".format(pivotList[3]))

        # check to see if its on the right side.
        inn_pos = cmds.xform(pivotList[2], q=True, ws=True, t=True)
        out_pos = cmds.xform(pivotList[3], q=True, ws=True, t=True)
        if out_pos < inn_pos:
            cmds.setAttr("{}.operation".format(bankCond), 4)

        # Setup the foot roll
        heelClamp = node.clamp(rollAttr, inMin=-180, inMax=0, output="{}.rx".format(pivotList[1]),
                               name="{}_heel".format(grp))
        ballClamp = node.clamp(rollAttr, inMin=0, inMax=ballAngleAttr, name="{}_ball".format(grp))
        toeClamp = node.clamp(rollAttr, inMin=ballAngleAttr, inMax=toeStraightAngleAttr, name="{}_toe".format(grp))

        toeRemap = node.remapValue("{}.outputR".format(toeClamp), inMin=ballAngleAttr, inMax=toeStraightAngleAttr,
                                   outMin=0, outMax=1, name="{}_toe".format(grp))
        toeRotate = node.multDoubleLinear("{}.outValue".format(toeRemap), rollAttr, output="{}.rx".format(pivotList[4]),
                                          name="{}_toeRotate".format(grp))

        ballRemap = node.remapValue("{}.outputR".format(ballClamp), inMin=0, inMax=ballAngleAttr, outMin=0, outMax=1,
                                    name="{}_ball".format(grp))
        ballRotateInvert = node.plusMinusAverage1D([1, "{}.outValue".format(toeRemap)], operation='sub',
                                                   name='{}_ballInvert'.format(grp))
        ballRotateMult = node.multDoubleLinear("{}.output1D".format(ballRotateInvert), "{}.outValue".format(ballRemap),
                                               name='{}_ballMult'.format(grp))
        toeRotate = node.multDoubleLinear("{}.output".format(ballRotateMult), rollAttr,
                                          output="{}.rx".format(pivotList[5]), name="{}_ballRotate".format(grp))

    def createPiviots(self):
        """
        Create a nessesary pivots.

        Piviot indecies are as follows:
            0 - root
            1 - heel
            2 - inn
            3 - out
            4 - end (toes)
            5 - ball
            6 - ankle
            7 - toe tap
        """

        piviot_dict = {
            'root': {
                'heel': {
                    'inn': {
                        'out': {
                            'end': {
                                'ball': {'ankle': None},
                                'toe': None}
                            }
                        }
                    }
                }
            }

        piv_hierarchy = rig_hierarchy.DictHierarchy(piviot_dict, parent=self._group, prefix=self._group + "_",
                                                    suffix='_piv')
        piv_hierarchy.create()
        self._pivotList = piv_hierarchy.getNodes()

        if not cmds.objExists(self._heel_piviot) or not cmds.objExists(self._inn_piviot) or not cmds.objExists(
                self._out_piviot):
            raise RuntimeError("missing required addional piviots. Please supply a heel, inn and out piviot")

        # matchup the piviots to their correct spots
        transform.matchTranslate(self._ikJointList[0], self._pivotList[0])
        transform.matchTranslate(self._heel_piviot, self._pivotList[1])
        transform.matchTranslate(self._inn_piviot, self._pivotList[2])
        transform.matchTranslate(self._out_piviot, self._pivotList[3])
        transform.matchTranslate(self._ikJointList[2], self._pivotList[4])
        transform.matchTranslate(self._ikJointList[1], self._pivotList[5])
        transform.matchTranslate(self._ikJointList[0], self._pivotList[6])
        transform.matchTranslate(self._ikJointList[1], self._pivotList[7])
