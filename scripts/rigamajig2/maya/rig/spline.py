"""
Module for Ik Spline
"""
import sys
import maya.cmds as cmds

import rigamajig2.shared.common as common
import rigamajig2.maya.debug as debug
import rigamajig2.maya.curve as rig_curve
import rigamajig2.maya.cluster as rig_cluster
import rigamajig2.maya.node as node
import rigamajig2.maya.transform as rig_transform
import rigamajig2.maya.attr as rig_attr
import rigamajig2.maya.joint as rig_joint
import rigamajig2.maya.mathUtils as mathUtils
import rigamajig2.maya.meta as meta

if sys.version_info[0] >= 3:
    basestring = str


class SplineBase(object):
    """
    base class for ik spline
    """

    def __init__(self, jointList, curve=None, name='splineIk', scaleFactor=1.0):
        """
        default constructor
        :param jointList: list of joints to create ik spline setup from
        :param name: name of the ikSpline setup
        :param curve: Optional - curve to be used for ikSpline, if None it will be automatically created
        :param scaleFactor:
        """
        self.setJointList(jointList)
        self._name = name
        self._group = name + '_hrc'
        self._curve = curve
        self._handle = str()
        self._ikJointList = list()
        self._clusters = list()
        self._startTwist = str()
        self._endTwist = str()
        self._scaleFactor = scaleFactor

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
        Return a list of ik joints used or created
        :return: list of joints
        :rtype: list
        """
        return self._ikJointList

    def getGroup(self):
        """
        Return the group
        :return: group
        :rtype: str
        """
        return self._group

    def getClusters(self):
        """
        Return the clusters
        :return: clusters
        :rtype: list
        """
        return self._clusters

    def getCurve(self):
        """
        Return the curve
        :return: curve
        :rtype: str
        """
        return self._curve

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

    def setName(self, name):
        """
        Set the attribute of the self._name
        :param name: name to set
        :type name: str
        :return:
        """
        self._name = name

    def create(self, clusters=4):
        """
        This will create the ik spline and connect them to the jointList.
        :param clusters: number of clusters to make
        """
        ikParent = self._group

        if clusters < 4:
            cmds.warning('Cannot create ikSpline with less than 4 controls')
            clusters = 4

        for joint in self._jointList:
            if not cmds.objExists(joint):
                raise RuntimeError('Joint "{}" does not exist'.format(joint))

        if not cmds.objExists(self._group):
            cmds.createNode("transform", name=self._group)

        cmds.addAttr(self._group, ln='stretchy', at='double', dv=1, min=0, max=1, k=True)
        cmds.addAttr(self._group, ln='volumeFactor', at='double', dv=1, min=0, k=True)
        stretchyAttr = '{}.stretchy'.format(self._group)
        volumeAttr = '{}.volumeFactor'.format(self._group)

        # create a duplicate joint chain, if we dont have an ikJointChain
        for i, joint in enumerate(self._jointList):
            ikJoint = "{}_jnt_{}".format(self._name, i)
            cmds.duplicate(joint, parentOnly=True, returnRootsOnly=True, name=ikJoint)
            self._ikJointList.append(ikJoint)
            debug.showLocalRotationAxis(ikJoint)
            if i:
                cmds.parent(ikJoint, ikParent)
            else:
                cmds.parent(ikJoint, self._group)
            ikParent = ikJoint

        startJoint = self._ikJointList[0]
        endJoint = self._ikJointList[-1]

        # create a curve from our joints and make an IkHandle
        curve = rig_curve.createCurveFromTransform([self._ikJointList[0], self._ikJointList[1],
                                                    self._ikJointList[-2], self._ikJointList[-1]],
                                                   degree=1, name="{}_crv".format(self._name))
        self._handle, self._effector, self._curve = cmds.ikHandle(name="{}_handle".format(self._name),
                                                                  pcv=0, ns=(clusters - 3), sol='ikSplineSolver',
                                                                  sj=startJoint, ee=endJoint, curve=curve,
                                                                  freezeJoints=True)

        self._curve = cmds.rename(self._curve, "{}_crv".format(self._name))

        cmds.parent(self._handle, self._curve, self._group)

        cvs = rig_curve.getCvs(self._curve)
        for i, cv in enumerate(cvs):
            cluster, handle = cmds.cluster(cv, n='{}_cls_{}'.format(self._name, i))
            self._clusters.append(handle)
            cmds.parent(handle, self._group)
            rig_cluster.localize(cluster, self._group, self._group, weightedCompensation=True)

        # CLUSTERS SCALE

        # STRETCH
        curve_info = cmds.rename(cmds.arclen(self._curve, ch=True), self._name + '_curveInfo')
        cmds.connectAttr(self._curve + '.local', curve_info + '.inputCurve', f=True)
        arc_len = cmds.getAttr("{}.{}".format(curve_info, 'arcLength'))
        stretchBta = node.blendTwoAttrs(arc_len, "{}.arcLength".format(curve_info), weight=stretchyAttr,
                                        name="{}_stretch".format(self._name))

        scaleAll = node.multiplyDivide(["{}.output".format(stretchBta), 1, 1], [arc_len, 1, 1], operation='div',
                                       name="{}_scale".format(self._name))

        # get aim axis and rotate order
        isNegative = True if '-' in rig_transform.getAimAxis(self._ikJointList[1], allowNegative=True) else False
        aimAxis = rig_transform.getAimAxis(self._ikJointList[1], allowNegative=False)
        rotOrder = cmds.getAttr('{}.ro'.format(self._ikJointList[1]))

        for i, joint in enumerate(self._ikJointList[1:]):
            if i > 0:
                jnt_len = mathUtils.distanceNodes(self._ikJointList[i], self._ikJointList[i + 1])
            else:
                jnt_len = mathUtils.distanceNodes(self._ikJointList[0], self._ikJointList[i + 1])

            if isNegative:
                jnt_len *= -1

            # Connect the stretch to the joint translation
            node.multDoubleLinear("{}.outputX".format(scaleAll), jnt_len,
                                  output="{}.t{}".format(joint, aimAxis),
                                  name='{}_stretch'.format(joint))
        # start twist decompose
        startgrp = cmds.createNode('transform', n=self._name + '_start_buffer', p=self._group)
        start = cmds.createNode('joint', n=self._name + '_start_' + common.TARGET, p=startgrp)
        self._startTwist = start
        rig_transform.matchTransform(self._ikJointList[0], startgrp)
        startTwist = rig_transform.decomposeRotation(self._startTwist, aimAxis)[list('xyz').index(aimAxis)]

        # end twist decompose
        endgrp = cmds.createNode('transform', n=self._name + '_end_buffer', p=self._group)
        end = cmds.createNode('joint', n=self._name + '_end_' + common.TARGET, p=endgrp)
        self._endTwist = end
        rig_transform.matchTransform(self._ikJointList[-1], endgrp)
        endTwist = rig_transform.decomposeRotation(self._endTwist, aimAxis)[list('xyz').index(aimAxis)]

        # The overall twist is calculated as roll = startTwist, twist =  (endTwist - startTwist)
        twist_multipler = -1 if isNegative else -1
        reverseStartTwist = node.multDoubleLinear(startTwist, twist_multipler,
                                                  name="{}_reverseStart".format(self._name))
        if isNegative:
            endReverse = node.multDoubleLinear(endTwist, -1, name="{}_reverseEnd".format(self._name))
            endTwist = "{}.output".format(endReverse)
        twistSum = node.addDoubleLinear(endTwist, "{}.output".format(reverseStartTwist),
                                        name="{}_addTwist".format(self._name))
        cmds.connectAttr(startTwist, "{}.roll".format(self._handle))
        cmds.connectAttr("{}.output".format(twistSum), "{}.twist".format(self._handle))
        scaleInvert = node.multiplyDivide(1, "{}.outputX".format(scaleAll), operation='div',
                                          name="{}_scaleInvert".format(self._name))
        # Connect the ikTo the bind joints
        i = 0
        for ik, bind in zip(self._ikJointList, self._jointList):
            # Calculate the volume perservation
            cmds.addAttr(self._group, ln="scale_{}".format(i), at='double', min=0, max=1, dv=1)

            scaleReversed = node.reverse("{}.scale_{}".format(self._group, i), name='{}_scaleRev'.format(ik))
            exponent = node.plusMinusAverage1D([1, "{}.outputX".format(scaleReversed)], operation='sub',
                                               name='{}_exponent'.format(ik))
            volume = node.multDoubleLinear("{}.output1D".format(exponent), volumeAttr, name='{}_volume'.format(ik))
            factor = node.multiplyDivide("{}.outputX".format(scaleInvert), "{}.output".format(volume), operation='pow',
                                         name='{}_factor'.format(ik))

            scaleAttrs = ['x', 'y', 'z']
            scaleAttrs.pop(scaleAttrs.index(aimAxis))
            for attr in scaleAttrs:
                cmds.connectAttr(".outputX".format(factor), '{}.s{}'.format(ik, attr))

            i += 1

        # connect the ik to bind chain
        rig_joint.connectChains(self.getIkJointList(), self.getJointList())

        # set the interpolations
        setScaleList = list(self._ikJointList)
        size = len(setScaleList)
        for i in range(size):
            percent = i / float(size - 1)
            value = mathUtils.parabolainterp(0, 1, percent)
            cmds.setAttr("{}.scale_{}".format(self._group, self._ikJointList.index(setScaleList[i])), value)

        # Hide the targets and parent them under the group.
        for jnt in [start, end]:
            cmds.setAttr('{}.drawStyle'.format(jnt), 2)
        for cls in self._clusters:
            cmds.setAttr('{}.v'.format(cls), 0)
        debug.hide(self._ikJointList)
        cmds.setAttr("{}.v".format(self._handle), 0)
        cmds.setAttr("{}.overrideEnabled".format(self._curve), 1)
        cmds.setAttr("{}.overrideDisplayType".format(self._curve), 1)

        meta.untag(self._ikJointList, "bind")


def addTwistJoints(start, end, jnts=4, name="twist", bind_parent=None, rig_parent=None):
    """
    add twist and bend joints between a start and end joint
    :param start: start joint
    :param end: end joint
    :param jnts: number of joints to add
    :param name: name of the group
    :param bind_parent: parent the bind group here
    :param rig_parent: parent the rig group
    :return: returns a list of targets and a spline object created.
            reminder: to get the first target you must first acess the list. ex addTwistJoints[0][0]
    """

    start = common.getFirstIndex(start)
    end = common.getFirstIndex(end)

    startJnt = "{}_0".format(name)
    cmds.duplicate(start, parentOnly=True, returnRootsOnly=True, name=startJnt)
    rig_attr.unlock(startJnt, rig_attr.KEYABLE(startJnt))
    # cmds.parent(startJnt, bind_grp)

    endJnt = "{}_{}".format(end, jnts + 1)
    cmds.duplicate(end, parentOnly=True, returnRootsOnly=True, name=endJnt)
    rig_attr.unlock(endJnt, rig_attr.KEYABLE(endJnt))
    cmds.parent(endJnt, startJnt)

    insertJnts = rig_joint.insertJoints(startJnt, endJnt, amount=jnts)
    jointList = [startJnt] + insertJnts + [endJnt]

    # ensure all transformation takes place on the main nodes
    rig_transform.unfreezeToTransform(jointList)
    rig_joint.toOrientation(jointList)

    spline_ = SplineBase(jointList=jointList, name=name)
    if not cmds.objExists(spline_.getGroup()):
        cmds.createNode("transform", n=spline_.getGroup())

    # parent the bind group
    rig_group = spline_.getGroup()
    if bind_parent and cmds.objExists(bind_parent):
        cmds.parent(jointList[0], bind_parent)
    else:
        rig_group = [rig_group] + [bind_grp]

    # parent the rig group
    if rig_parent and cmds.objExists(rig_parent):
        cmds.parent(rig_group, rig_parent)

    spline_.create()

    # create three output joints
    startTgt = cmds.createNode('joint', n="{}_start_spline_{}".format(name, common.TARGET))
    rig_transform.matchTransform(jointList[0], startTgt)

    midTgt = cmds.createNode('joint', n="{}_mid_spline_{}".format(name, common.TARGET))
    rig_transform.matchTranslate(jointList[::len(jointList) - 1], midTgt)
    rig_transform.matchRotate(jointList[0], midTgt)

    endTgt = cmds.createNode('joint', n="{}_end_spline_{}".format(name, common.TARGET))
    rig_transform.matchTransform(jointList[-1], endTgt)

    cmds.parent(startTgt, midTgt, endTgt, spline_.getGroup())

    # connect the targets to the main joints source
    cmds.parent(spline_.getClusters()[0], startTgt)
    cmds.parent(spline_.getClusters()[1:-1], midTgt)
    cmds.parent(spline_.getClusters()[-1], endTgt)

    # connect to the twist of the joints
    rig_transform.connectOffsetParentMatrix(start, spline_.getGroup(), mo=True)
    cmds.orientConstraint(end, spline_._endTwist, mo=True)

    # general cleanup
    for jnt in [startTgt, midTgt, endTgt]:
        cmds.setAttr('{}.drawStyle'.format(jnt), 2)

    return [startTgt, midTgt, endTgt], spline_
