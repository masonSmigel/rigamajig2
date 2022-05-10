"""
COG component
"""
import maya.cmds as cmds
import rigamajig2.maya.cmpts.base
import rigamajig2.maya.rig.control as rig_control
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

    def __init__(self, name, input=[], size=1, bindToInput=False):
        """
        Center of gravity (COG) component.

        :param name: name of the components
        :param input: list of one joint. typically the hips.
        :type input: list
        :param size: default size of the controls:
        :type size: float
        :param rigParent:  Connect the component to a rigParent.
        :param bindToInput: connect the output position of the COG cmpt to the input.
                            This should be False in most rigs as the hips will be controlled by the spine.
        :type bindToInput: bool
        """
        super(Cog, self).__init__(name, input=input, size=size)

        self.cmptSettings['bind_to_input'] = bindToInput
        self.cmptSettings['cog_control_shape'] = 'cube'
        self.cmptSettings['cog_name'] = 'hips'
        self.cmptSettings['cogGimble_name'] = 'hipsGimble'
        self.cmptSettings['cogPivot_name'] = 'hips_pivot'

    def initalHierachy(self):
        """Build the initial hirarchy"""
        self.root_hrc = cmds.createNode('transform', n=self.name + '_cmpt')
        # self.params_hrc = cmds.createNode('transform', n=self.name + '_params', parent=self.root_hrc)
        self.control_hrc = cmds.createNode('transform', n=self.name + '_control', parent=self.root_hrc)
        # self.spaces_hrc = cmds.createNode('transform', n=self.name + '_spaces', parent=self.root_hrc)

        if len(self.input) >= 1:
            pos = cmds.xform(self.input[0], q=True, ws=True, t=True)
        else:
            pos = (0,0,0)
        self.cog = rig_control.create(self.cog_name,
                                      hierarchy=['trsBuffer'],
                                      hideAttrs=['s', 'v'], size=self.size, color='yellow',
                                      parent=self.control_hrc, shape=self.cog_control_shape, shapeAim='x',
                                      position=pos)
        self.cog_pivot = rig_control.create(self.cogPivot_name,
                                            hierarchy=['trsBuffer'],
                                            hideAttrs=['s', 'v'], size=self.size, color='yellow',
                                            parent=self.cog[-1], shape='sphere', shapeAim='x',
                                            position=pos)
        self.cog_gimble = rig_control.create(self.cogGimble_name,
                                             hierarchy=['trsBuffer', 'neg'],
                                             hideAttrs=['s', 'v'], size=self.size, color='yellow',
                                             parent=self.cog[-1], shape=self.cog_control_shape, shapeAim='x',
                                             position=pos)

    def rigSetup(self):
        # create the pivot negate
        constrain.negate(self.cog_pivot[-1], self.cog_gimble[1], t=True)
        if self.bind_to_input and len(self.input) >= 1:
            self.input_trs = hierarchy.create(self.cog_gimble[-1], ['{}_trs'.format(self.input[0])], above=False)[0]
            rig_transform.matchTransform(self.input[0], self.input_trs)
            joint.connectChains(self.input_trs, self.input[0])

    def connect(self):

        if cmds.objExists(self.rigParent):
            cmds.parentConstraint(self.rigParent, self.cog[0], mo=True)
