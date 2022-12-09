"""
COG component
"""
import maya.cmds as cmds
import rigamajig2.maya.cmpts.base
from rigamajig2.maya import attr
from rigamajig2.maya.rig import control
import rigamajig2.maya.rig.spaces as spaces
import rigamajig2.maya.rig.ikfk as ikfk
import rigamajig2.maya.transform as rig_transform
import rigamajig2.maya.hierarchy as hierarchy
import rigamajig2.maya.joint as joint
import rigamajig2.maya.meta as meta
import rigamajig2.maya.constrain as constrain

import logging

logger = logging.getLogger(__name__)


class Cog(rigamajig2.maya.cmpts.base.Base):
    """
    Center of gravity (COG) component.
    """
    VERSION_MAJOR = 1
    VERSION_MINOR = 0
    VERSION_PATCH = 0

    version_info = (VERSION_MAJOR, VERSION_MINOR, VERSION_PATCH)
    version = '%i.%i.%i' % version_info
    __version__ = version

    def __init__(self, name, input, size=1, bindToInput=False, rigParent=str()):
        """
        :param str name: name of the components
        :param list input: list of one joint. typically the hips.
        :param float int size: default size of the controls:
        :param str rigParent:  Connect the component to a rigParent.
        :param bool bindToInput: connect the output position of the COG cmpt to the input.
                            This should be False in most rigs as the hips will be controlled by the spine.
        """
        super(Cog, self).__init__(name, input=input, size=size, rigParent=rigParent)

        self.cmptSettings['bind_to_input'] = bindToInput
        self.cmptSettings['cog_control_shape'] = 'cube'
        self.cmptSettings['cog_name'] = 'hips'
        self.cmptSettings['cogGimble_name'] = 'hipsGimble'
        self.cmptSettings['cogPivot_name'] = 'hips_pivot'

    def initalHierachy(self):
        """Build the initial hirarchy"""
        self.rootHierarchy = cmds.createNode('transform', n=self.name + '_cmpt')
        self.controlHierarchy = cmds.createNode('transform', n=self.name + '_control', parent=self.rootHierarchy)

        if len(self.input) >= 1:
            pos = cmds.xform(self.input[0], q=True, ws=True, t=True)
        else:
            pos = (0, 0, 0)
        self.cog = control.create(self.cog_name,
                                  hideAttrs=['s', 'v'], size=self.size, color='yellow',
                                  parent=self.controlHierarchy, shape=self.cog_control_shape, shapeAim='x',
                                  position=pos)
        self.cogPivot = control.create(self.cogPivot_name,
                                       hideAttrs=['s', 'v'], size=self.size, color='yellow',
                                       parent=self.cog.name, shape='sphere', shapeAim='x',
                                       position=pos)
        self.cogGimble = control.create(self.cogGimble_name,
                                        hideAttrs=['s', 'v'], size=self.size, color='yellow',
                                        parent=self.cog.name, shape=self.cog_control_shape, shapeAim='x',
                                        position=pos)
        self.cogGimble.addTrs("neg")

    def rigSetup(self):
        # create the pivot negate

        negateOffsetName = self.cogGimble.trs + '_trs'
        negativeTrs = hierarchy.create(self.cogGimble.trs, [negateOffsetName], above=True, matchTransform=True)[0]
        constrain.parentConstraint(driver=self.cogPivot.name, driven=negativeTrs)

        constrain.negate(self.cogPivot.name, self.cogGimble.trs, t=True)
        if self.bind_to_input and len(self.input) >= 1:
            self.inputTrs = hierarchy.create(self.cogGimble.name, ['{}_trs'.format(self.input[0])], above=False)[0]
            rig_transform.matchTransform(self.input[0], self.inputTrs)
            joint.connectChains(self.inputTrs, self.input[0])

    def setupAnimAttrs(self):
        """ setup the animation attributes """

        # create a visability control for the ikGimble control
        attr.addSeparator(self.cog.name, "----")

        attr.createAttr(self.cog.name, "movablePivot", attributeType='bool', value=0, keyable=False, channelBox=True)
        control.connectControlVisiblity(self.cog.name, "movablePivot", controls=self.cogPivot.name)

        attr.createAttr(self.cog.name, "gimble", attributeType='bool', value=0, keyable=False, channelBox=True)
        control.connectControlVisiblity(self.cog.name, "gimble", controls=self.cogGimble.name)

    def connect(self):
        if cmds.objExists(self.rigParent):
            cmds.parentConstraint(self.rigParent, self.cog[0], mo=True)

