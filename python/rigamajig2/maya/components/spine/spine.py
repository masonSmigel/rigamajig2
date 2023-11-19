"""
spine component
"""
import maya.cmds as cmds

from rigamajig2.maya import attr
from rigamajig2.maya import hierarchy
from rigamajig2.maya import joint
from rigamajig2.maya import node
from rigamajig2.maya import transform
from rigamajig2.maya.components import base
from rigamajig2.maya.rig import control
from rigamajig2.maya.rig import live
from rigamajig2.maya.rig import spaces
from rigamajig2.maya.rig import spline
from rigamajig2.shared import common

HIPS_PERCENT = 0.33
SPINE_PERCENT = 0.5
TORSO_PERCENT = 0.15


class Spine(base.BaseComponent):
    """
    Spine component.
    The spine containts the hipSwivel, torso and chest controls.
    Based on an IKSpline to create a smooth movement in the spine
    """
    VERSION_MAJOR = 1
    VERSION_MINOR = 0
    VERSION_PATCH = 0

    version_info = (VERSION_MAJOR, VERSION_MINOR, VERSION_PATCH)
    version = '%i.%i.%i' % version_info
    __version__ = version

    UI_COLOR = (140, 215, 122)

    def __init__(self, name, input, size=1, rigParent=str(), componentTag=None):
        """
        :param str name: name of the component
        :param list input: list of input joints. Starting with the base of the neck and ending with the head.
        :param float int size: default size of the controls.
        :param str rigParent: connect the component to a rigParent.
        """
        super(Spine, self).__init__(name, input=input, size=size, rigParent=rigParent, componentTag=componentTag)
        self.side = common.getSide(self.name)

        self.addSpineMid = True
        self.chestSpaces = {}
        self.chestName = "chest"
        self.spineName = "spine"
        self.torsoName = "torso"
        self.hipsName = "hip"

        self.defineParameter(parameter="addSpineMid", value=self.addSpineMid, dataType="bool")
        self.defineParameter(parameter="hipsName", value=self.hipsName, dataType="string")
        self.defineParameter(parameter="torsoName", value=self.torsoName, dataType="string")
        self.defineParameter(parameter="chestName", value=self.chestName, dataType="string")
        self.defineParameter(parameter="chestSpaces", value=self.chestSpaces, dataType="dict")
       
    def _createBuildGuides(self):
        """Create the build guides"""
        self.guidesHierarchy = cmds.createNode("transform", name='{}_guide'.format(self.name))

        self.hipsSwivelGuide = control.createGuide(
            self.name + "_hipSwivel",
            side=self.side,
            parent=self.guidesHierarchy)
        live.slideBetweenTransforms(self.hipsSwivelGuide, self.input[1], self.input[-2], defaultValue=HIPS_PERCENT)

        self.torsoGuide = control.createGuide(
            self.name + "_torso",
            side=self.side,
            parent=self.guidesHierarchy)

        # setup the slider for the guide
        live.slideBetweenTransforms(self.torsoGuide, self.input[1], self.input[-2], defaultValue=TORSO_PERCENT)

        self.chestGuide = control.createGuide(
            self.name + "_chest",
            side=self.side,
            parent=self.guidesHierarchy,
            position=cmds.xform(self.input[-2], q=True, ws=True, t=True))

        self.chestTopGuide = control.createGuide(
            self.name + "_chestTop",
            side=self.side,
            parent=self.guidesHierarchy,
            position=cmds.xform(self.input[-1], q=True, ws=True, t=True))

        if self.addSpineMid:
            self.spineMidGuide = control.createGuide(
                self.name + "_spineMid",
                side=self.side,
                parent=self.guidesHierarchy,
                position=cmds.xform(self.input[-2], q=True, ws=True, t=True)
                )

            live.slideBetweenTransforms(self.spineMidGuide, self.input[1], self.input[-2], defaultValue=SPINE_PERCENT)

        for guide in [self.hipsSwivelGuide, self.torsoGuide, self.chestGuide]:
            attr.lock(guide, attr.TRANSLATE)

        attr.lockAndHide(self.chestTopGuide, attr.TRANSLATE + ['v'])

    def _initialHierarchy(self):
        """Build the initial hirarchy"""
        super(Spine, self)._initialHierarchy()

        # build the hips swivel control
        hipPos = cmds.xform(self.input[0], q=True, ws=True, t=True)
        self.hipSwing = control.createAtObject(
            name=self.hipsName + "_swing",
            side=self.side,
            spaces=True,
            hideAttrs=['s', 'v'],
            size=self.size,
            color='yellow',
            parent=self.controlHierarchy,
            shape='cube',
            shapeAim='x',
            xformObj=self.hipsSwivelGuide
            )

        # build the torso control
        self.torso = control.createAtObject(
            name=self.torsoName,
            side=self.side,
            spaces=True,
            hideAttrs=['s', 'v'],
            size=self.size,
            color='yellow',
            parent=self.controlHierarchy,
            shape='cube',
            shapeAim='x',
            xformObj=self.torsoGuide
            )

        # if we want to add a spineMid then add it between the chest and torso
        if self.addSpineMid:
            self.spineMid = control.createAtObject(
                name=self.spineName+"Mid",
                side=self.side,
                hideAttrs=['s', 'v'],
                size=self.size,
                color='yellow',
                parent=self.torso.name,
                shape='cube',
                shapeAim='x',
                xformObj=self.spineMidGuide
                )

        # build the chest control
        self.chest = control.createAtObject(
            name=self.chestName,
            side=self.side,
            spaces=True,
            hideAttrs=['s', 'v'],
            size=self.size,
            color='yellow',
            parent=self.spineMid.name if self.addSpineMid else self.torso.name,
            shape='cube',
            shapeAim='x',
            xformObj=self.chestGuide
            )
        self.chest.addTrs("neg")

        chestPos = cmds.xform(self.input[-1], q=True, ws=True, t=True)
        self.chestTop = control.createAtObject(
            name=self.chestName+"Top",
            side=self.side,
            hideAttrs=['s', 'v'],
            size=self.size,
            color='yellow',
            parent=self.chest.name,
            shape='cube',
            shapeAim='x',
            xformObj=self.chestTopGuide
            )
        self.chest.addTrs("len")

        self.hipTangent = control.create(
            name=self.hipsName+"Tan",
            side=self.side,
            hideAttrs=['r', 's', 'v'],
            size=self.size,
            color='yellow',
            parent=self.hipSwing.name,
            shape='diamond',
            shapeAim='x',
            position=hipPos
            )

        self.chestTangent = control.create(
            name=self.chestName+"Tan",
            side=self.side,
            hideAttrs=['r', 's', 'v'],
            size=self.size,
            color='yellow',
            parent=self.chest.name,
            shape='diamond',
            shapeAim='x',
            position=chestPos
            )

    def _rigSetup(self):
        """Add the rig setup"""

        # the spline might shift slightly when the ik is created.
        # If built first this could affect the input of joints downstream
        # To comabt this  first we'll use the last joint to anchor the end of the spine to the chest top control
        self.chestTopTrs = hierarchy.create(self.chestTop.name, ['{}_trs'.format(self.input[0])], above=False)[0]
        transform.matchTransform(self.input[-1], self.chestTopTrs)

        joint.connectChains(self.chestTopTrs, self.input[-1])

        # create the spline ik
        self.ikspline = spline.SplineBase(self.input[1:-1], name=self.name)
        self.ikspline.setGroup(self.name + '_ik')
        self.ikspline.create(clusters=4, params=self.paramsHierarchy)
        cmds.parent(self.ikspline.getGroup(), self.rootHierarchy)

        # setup the hipSwivel
        self.hipSwingTrs = hierarchy.create(self.hipSwing.name, ['{}_trs'.format(self.input[0])], above=False)[0]
        transform.matchTransform(self.input[0], self.hipSwingTrs)
        joint.connectChains(self.hipSwingTrs, self.input[0])

        # create  attributes
        attr.addSeparator(self.chest.name, '----')
        attr.addSeparator(self.hipSwing.name, '----')
        attr.createAttr(self.chest.name, 'pivotHeight', attributeType='float', value=3.5, minValue=0, maxValue=10)
        # connect the some attributes
        attr.createAttr(self.chest.name, 'volumeFactor', attributeType='float', value=1, minValue=0, maxValue=10)
        cmds.connectAttr("{}.volumeFactor".format(self.chest.name), "{}.volumeFactor".format(self.paramsHierarchy))

        # connect the tangets to the visablity
        attr.createAttr(self.chest.name, 'tangentVis', attributeType='bool', value=1, channelBox=True,
                            keyable=False)
        cmds.connectAttr("{}.tangentVis".format(self.chest.name), "{}.v".format(self.chestTangent.orig))
        attr.createAttr(self.hipSwing.name, 'tangentVis', attributeType='bool', value=1, channelBox=True,
                            keyable=False)
        cmds.connectAttr("{}.tangentVis".format(self.hipSwing.name), "{}.v".format(self.hipTangent.orig))

        # create the chest piviot offset
        axis = transform.getAimAxis(self.chest.name)
        remap = node.remapValue('{}.{}'.format(self.chest.name, 'pivotHeight'),
                                                inMin=0, inMax=10, outMin=0,
                                                outMax=cmds.arclen(self.ikspline.getCurve(), ch=False),
                                                name=self.chest.name + "height")
        node.multDoubleLinear('{}.{}'.format(remap, 'outValue'), -1,
                                              output='{}.{}'.format(self.chest.name, 'rotatePivot' + axis.upper()),
                                              name=self.chest.name + "height")

        # connect the clusters to the spline
        cmds.parent(self.ikspline.getClusters()[0], self.hipSwingTrs)
        cmds.parent(self.ikspline.getClusters()[3], self.chest.name)
        transform.matchTransform(self.ikspline.getClusters()[1], self.hipTangent.orig)
        cmds.parent(self.ikspline.getClusters()[1], self.hipTangent.name)
        transform.matchTransform(self.ikspline.getClusters()[2], self.chestTangent.orig)
        cmds.parent(self.ikspline.getClusters()[2], self.chestTangent.name)

        # connect the orient constraint to the twist controls
        cmds.orientConstraint(self.hipSwing.name, self.ikspline._startTwist, mo=True)
        cmds.orientConstraint(self.chestTop.name, self.ikspline._endTwist, mo=True)

    def _connect(self):
        """Create the connection"""

        # add world space switches
        if cmds.objExists('trs_motion'):
            # setup the spaces
            spaces.create(self.hipSwing.spaces, self.hipSwing.name, parent=self.spacesHierarchy, defaultName='local')
            spaces.create(self.torso.spaces, self.torso.name, parent=self.spacesHierarchy, defaultName='local')
            spaces.create(self.chest.spaces, self.chest.name, parent=self.spacesHierarchy, defaultName='local')

            spaces.addSpace(self.hipSwing.spaces, ['trs_motion'], nameList=['world'], constraintType='orient')
            spaces.addSpace(self.torso.spaces, ['trs_motion'], nameList=['world'], constraintType='orient')
            spaces.addSpace(self.chest.spaces, ['trs_motion'], nameList=['world'], constraintType='parent')

        if self.chestSpaces:
            ikspaceValues = [self.chestSpaces[k] for k in self.chestSpaces.keys()]
            spaces.addSpace(self.chest.spaces, ikspaceValues, self.chestSpaces.keys(), 'parent')

        if cmds.objExists(self.rigParent):
            transform.connectOffsetParentMatrix(self.rigParent, self.hipSwing.orig, mo=True)
            transform.connectOffsetParentMatrix(self.rigParent, self.torso.orig, mo=True)
            transform.connectOffsetParentMatrix(self.rigParent, self.ikspline.getGroup(), mo=True)

    def _finalize(self):
        attr.lock(self.ikspline.getGroup(), attr.TRANSFORMS + ['v'])
        attr.lockAndHide(self.paramsHierarchy, attr.TRANSFORMS + ['v'])

