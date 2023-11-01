"""
neck component
"""
import maya.cmds as cmds

import rigamajig2.maya.attr as rig_attr
import rigamajig2.maya.components.base
import rigamajig2.maya.hierarchy as hierarchy
import rigamajig2.maya.joint as rig_joint
import rigamajig2.maya.rig.control as rig_control
import rigamajig2.maya.rig.live as live
import rigamajig2.maya.rig.spaces as spaces
import rigamajig2.maya.rig.spline as spline
import rigamajig2.maya.transform as rig_transform
import rigamajig2.shared.common as common

HEAD_PERCENT = 0.7


# pylint:disable = too-many-instance-attributes
class Neck(rigamajig2.maya.components.base.Base):
    """
    Neck component
    The neck has a head and neck controls.
    """
    VERSION_MAJOR = 1
    VERSION_MINOR = 0
    VERSION_PATCH = 0

    version_info = (VERSION_MAJOR, VERSION_MINOR, VERSION_PATCH)
    version = '%i.%i.%i' % version_info
    __version__ = version

    UI_COLOR = (47, 177, 161)

    def __init__(self, name, input, size=1, rigParent=str(), componentTag=None):
        """
        :param str name: name of the component
        :param list input: list of input joints. Starting with the base of the neck and ending with the head.
        :param float int size: default size of the controls.
        :param dict headSpaces: dictionary of key and space for the head control. formated as {"attrName": object}
        :param dict neckSpaces: dictionary of key and space for the neck control. formated as {"attrName": object}
        :param str rigParent: connect the component to a rigParent.
        """

        super(Neck, self).__init__(name, input=input, size=size, rigParent=rigParent, componentTag=componentTag)
        self.side = common.getSide(self.name)

        self.defineParameter(parameter="neck_name", value="neck", dataType="string")
        self.defineParameter(parameter="head_name", value="head", dataType="string")
        self.defineParameter(parameter="headGimble_name", value="headGimble", dataType="string")
        self.defineParameter(parameter="headTangent_name", value="headTan", dataType="string")
        self.defineParameter(parameter="neckTangent_name", value="neckTan", dataType="string")
        self.defineParameter(parameter="skull_name", value="skull", dataType="string")
        self.defineParameter(parameter="neckSpaces", value=dict(), dataType="dict")
        self.defineParameter(parameter="headSpaces", value=dict(), dataType="dict")

    def _createBuildGuides(self):
        """Create the build guides"""
        self.guidesHierarchy = cmds.createNode("transform", name='{}_guide'.format(self.name))

        neckPos = cmds.xform(self.input[0], q=True, ws=True, t=True)
        self.neckGuide = rig_control.createGuide(self.name + "_neck", side=self.side, parent=self.guidesHierarchy,
                                                 position=neckPos)
        rig_attr.lockAndHide(self.neckGuide, rig_attr.TRANSLATE + ['v'])

        self.headGuide = rig_control.createGuide(self.name + "_head", side=self.side, parent=self.guidesHierarchy)
        live.slideBetweenTransforms(self.headGuide, start=self.input[0], end=self.input[-1], defaultValue=HEAD_PERCENT)
        rig_attr.lock(self.headGuide, rig_attr.TRANSLATE + ['v'])

        skullPos = cmds.xform(self.input[-1], q=True, ws=True, t=True)
        self.skullGuide = rig_control.createGuide(self.name + "_skull", side=self.side, parent=self.guidesHierarchy,
                                                  position=skullPos)
        rig_attr.lockAndHide(self.skullGuide, rig_attr.TRANSLATE + ['v'])

    def _initialHierarchy(self):
        super(Neck, self)._initialHierarchy()

        self.neck = rig_control.createAtObject(
            self.neck_name, self.side,
            spaces=True,
            hideAttrs=['s', 'v'],
            size=self.size,
            color='yellow',
            parent=self.controlHierarchy,
            shape='cube',
            shapeAim='x',
            xformObj=self.neckGuide)

        self.head = rig_control.createAtObject(
            self.head_name, self.side,
            spaces=True,
            hideAttrs=['v'],
            size=self.size,
            color='yellow',
            parent=self.neck.name,
            shape='cube',
            shapeAim='x',
            xformObj=self.headGuide)

        self.headGimble = rig_control.createAtObject(
            self.headGimble_name,
            self.side,
            hideAttrs=['s', 'v'],
            size=self.size,
            color='yellow',
            parent=self.head.name,
            shape='cube',
            shapeAim='x',
            xformObj=self.headGuide)

        self.skull = rig_control.createAtObject(
            self.skull_name,
            self.side,
            hideAttrs=['v'],
            size=self.size,
            color='yellow',
            parent=self.headGimble.name,
            shape='cube',
            shapeAim='x',
            xformObj=self.skullGuide)

        self.headTanget = rig_control.createAtObject(
            self.headTangent_name, self.side,
            hideAttrs=['r', 's', 'v'],
            size=self.size,
            color='yellow',
            parent=self.headGimble.name,
            shape='diamond',
            shapeAim='x',
            xformObj=self.skullGuide)

        self.neckTanget = rig_control.createAtObject(
            self.neckTangent_name,
            self.side,
            hideAttrs=['r', 's', 'v'],
            size=self.size,
            color='yellow',
            parent=self.neck.name,
            shape='diamond',
            shapeAim='x',
            xformObj=self.neckGuide)

    def _rigSetup(self):
        """Add the rig setup"""
        # create the spline ik
        self.ikspline = spline.SplineBase(self.input, name=self.name)
        self.ikspline.setGroup(self.name + '_ik')
        self.ikspline.create(clusters=4, params=self.paramsHierarchy)
        cmds.parent(self.ikspline.getGroup(), self.rootHierarchy)

        # connect the volume factor and tangents visability attributes
        rig_attr.addSeparator(self.head.name, "----")
        rig_attr.createAttr(self.head.name, 'volumeFactor', attributeType='float', value=1, minValue=0, maxValue=10)
        cmds.connectAttr("{}.volumeFactor".format(self.head.name), "{}.volumeFactor".format(self.paramsHierarchy))

        rig_attr.createAttr(self.neck.name, 'tangentVis', attributeType='bool', value=1, channelBox=True, keyable=False)
        cmds.connectAttr("{}.tangentVis".format(self.neck.name), "{}.v".format(self.neckTanget.orig))
        rig_transform.matchTransform(self.ikspline.getClusters()[1], self.neckTanget.orig)

        rig_attr.createAttr(self.head.name, 'tangentVis', attributeType='bool', value=1, channelBox=True, keyable=False)
        cmds.connectAttr("{}.tangentVis".format(self.head.name), "{}.v".format(self.headTanget.orig))
        rig_transform.matchTransform(self.ikspline.getClusters()[2], self.headTanget.orig)

        # parent clusters to tangent controls
        cmds.parent(self.ikspline.getClusters()[1], self.neckTanget.name)
        cmds.parent(self.ikspline.getClusters()[2], self.headTanget.name)
        cmds.parent(self.ikspline.getClusters()[3], self.headGimble.name)

        # connect the skull to the head joint
        self.skullTrs = hierarchy.create(self.skull.name, ['{}_trs'.format(self.input[-1])], above=False)[0]
        rig_transform.matchTransform(self.input[-1], self.skullTrs)
        # delete exising parent constraint
        cmds.delete(cmds.ls(cmds.listConnections("{}.tx".format(self.input[-1])), type='parentConstraint'))
        rig_joint.connectChains(self.skullTrs, self.input[-1])

        # connect the orient constraint to the twist controls
        cmds.orientConstraint(self.neck.name, self.ikspline._startTwist, mo=True)
        cmds.orientConstraint(self.headGimble.name, self.ikspline._endTwist, mo=True)

        rig_transform.connectOffsetParentMatrix(self.neck.name, self.ikspline.getGroup(), mo=True)

    def _setupAnimAttrs(self):
        # create a visability control for the ikGimble control
        rig_attr.createAttr(self.head.name, "gimble", attributeType='bool', value=0, keyable=False, channelBox=True)
        rig_control.connectControlVisiblity(self.head.name, "gimble", controls=self.headGimble.name)

    def _connect(self):
        """Create the connection"""

        # connect the rig to is rigParent
        if cmds.objExists(self.rigParent):
            rig_transform.connectOffsetParentMatrix(self.rigParent, self.neck.orig, mo=True)

        spaces.create(self.neck.spaces, self.neck.name, parent=self.spacesHierarchy)
        spaces.create(self.head.spaces, self.head.name, parent=self.spacesHierarchy)

        # if the main control exists connect the world space
        if cmds.objExists('trs_motion'):
            spaces.addSpace(self.neck.spaces, ['trs_motion'], nameList=['world'], constraintType='orient')
            spaces.addSpace(self.head.spaces, ['trs_motion'], nameList=['world'], constraintType='orient')

        if self.neckSpaces:
            spaces.addSpace(self.head.spaces, [self.neckSpaces[k] for k in self.neckSpaces.keys()],
                            self.neckSpaces.keys(),
                            'orient')

        if self.headSpaces:
            spaces.addSpace(self.head.spaces, [self.headSpaces[k] for k in self.headSpaces.keys()],
                            self.headSpaces.keys(),
                            'orient')

    def _finalize(self):
        rig_attr.lock(self.ikspline.getGroup(), rig_attr.TRANSFORMS + ['v'])
        rig_attr.lockAndHide(self.paramsHierarchy, rig_attr.TRANSFORMS + ['v'])
