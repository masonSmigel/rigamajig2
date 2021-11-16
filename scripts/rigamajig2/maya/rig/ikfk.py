"""
Module for Ik/Fk stuff
"""

import maya.cmds as cmds
import maya.api.OpenMaya as om2
from maya.api.OpenMaya import MVector

import rigamajig2.shared.common as common
import rigamajig2.maya.transform as transform
import rigamajig2.maya.node as node
import rigamajig2.maya.joint as joint
import rigamajig2.maya.mathUtils as mathUtils
import rigamajig2.maya.debug as debug


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
        This will create the ik/fk joints and connect them to the blendchain.
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

            # connect the IKFK to the blend joint
            if not blendJntExists:
                node.pairBlend(ikJnt, fkJnt, ikfkAttr, blendJnt, name=blendJnt + '_tr', rotInterp='quat')
                node.blendColors(ikJnt + '.s', fkJnt + '.s', ikfkAttr, blendJnt + '.s', name=blendJnt + '_s')

                for attr in ['{}{}'.format(x, y) for x in 'trs' for y in 'xyz']:
                    cmds.setAttr("{}.{}".format(blendJnt, attr), e=True, lock=True)


class IkFkLimb(IkFkBase):
    """
    This class creates a blending ik/fk system with a rotate plane solver
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

        if not grp or not cmds.objExists(grp):
            grp = cmds.createNode("transform", name='ikfk_stretch_hrc')

        # check if our joints are clean. If not return a warning but we can continue.

        if not joint.isClean(jnts[1]) or not joint.isClean(jnts[2]):
            cmds.warning("Some joints have dirty transformations. Stretch may not work as expected")

        cmds.addAttr(grp, ln='stretch', at='double', dv=1, min=0, max=1, k=True)
        cmds.addAttr(grp, ln='stretchTop', at='double', dv=1, k=True)
        cmds.addAttr(grp, ln='stretchBot', at='double', dv=1, k=True)
        cmds.addAttr(grp, ln='softStretch', at='double', dv=.001, min=.001, max=1, k=True)
        stretchAttr = '{}.stretch'.format(grp)
        stretchTopAttr = '{}.stretchTop'.format(grp)
        stretchBotAttr = '{}.stretchBot'.format(grp)
        softStretchAttr = '{}.softStretch'.format(grp)

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
    def createPvPin(ikHandle, pv, grp=None):
        jnts = IkFkLimb.getJointsFromHandle(ikHandle)

        if not grp or not cmds.objExists(grp):
            grp = cmds.createNode("transform", name='ikfk_stretch_hrc')

        cmds.addAttr(grp, ln='pvLock', at='double', dv=0, min=0, max=1, k=True)
        pvLockAttr = '{}.pvLock'.format(grp)

        switch = node.plusMinusAverage1D([1, "{}.{}".format(grp, 'ikfk')], operation='sub', name=grp + "_rev")
        pvPin = node.multDoubleLinear("{}.{}".format(switch, 'output1D'), "{}.{}".format(grp, 'pvLock'), name=grp + '_pvPin')

        pvdcmp = node.decomposeMatrix("{}.{}".format(pv, 'worldMatrix'), name=pv)
        shoulderToPv = node.distance(jnts[0], "{}.{}".format(pvdcmp, 'outputTranslate'), name=grp + '_upperPvPin')
        elbowToPv = node.distance(jnts[1], "{}.{}".format(pvdcmp, 'outputTranslate'), name=grp + '_lowerPvPin')

        shoulderToElbow = mathUtils.distanceNodes(jnts[0], jnts[1])
        elbowToWrist = mathUtils.distanceNodes(jnts[1], jnts[2])

        distance = node.multiplyDivide(
            ["{}.{}".format(shoulderToPv, 'distance'), "{}.{}".format(elbowToPv, 'distance'), 0],
            [shoulderToElbow, elbowToWrist, 0], operation='div', name=grp + '_pvDist')




    @staticmethod
    def ikMatchFk():
        pass

    @staticmethod
    def fkMatchIk():
        pass

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
    def getPoleVectorFromHandle(ikHandle, magnitude=10):
        """
        Get the pole vector position from an ikHandle
        :param ikHandle: Ik handle to get the joints from
        :param magnitude: magnitute (aka distance from mid joint to pole vector)
        :return:
        """
        jointList = IkFkLimb.getJointsFromHandle(ikHandle)
        pv_pos = IkFkLimb.getPoleVectorPos(jointList, magnitude)
        return pv_pos
