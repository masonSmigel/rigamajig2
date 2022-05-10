"""
main component
"""
import maya.cmds as cmds
import rigamajig2.maya.cmpts.base
import rigamajig2.maya.rig.control as rig_control
import rigamajig2.maya.container
import rigamajig2.maya.node
import rigamajig2.maya.attr

RIG_HRC_NAME = 'rig'
BIND_HRC_NAME = 'bind'
MOD_HRC_NAME = 'model'


class Main(rigamajig2.maya.cmpts.base.Base):
    def __init__(self, name, input=[], size=1, rigParent=None):
        """
        Create a main control
        :param name:
        :param input:
        """
        super(Main, self).__init__(name=name, input=input, size=size)

    def initalHierachy(self):
        """Build the initial hirarchy"""
        self.root_hrc = cmds.createNode('transform', n=self.name)
        self.rig_hrc = cmds.createNode('transform', n=RIG_HRC_NAME, parent=self.root_hrc)
        self.bind_hrc = cmds.createNode('transform', n=BIND_HRC_NAME, parent=self.root_hrc)
        self.model_hrc = cmds.createNode('transform', n=MOD_HRC_NAME, parent=self.root_hrc)

        # Build our controls
        self.trs_global = rig_control.create('trs_global', hierarchy=[], size=self.size * 1.2,
                                             color='yellow', parent=self.root_hrc)[0]
        self.trs_shot = rig_control.create('trs_shot', hierarchy=[], size=self.size * 1.1,
                                           color='lightgreenyellow', parent=self.trs_global)[0]
        self.trs_motion = rig_control.create('trs_motion', hierarchy=[], size=self.size,
                                             color='yellowgreen', parent=self.trs_shot)[0]
        # add the trs to the top of our outliner
        cmds.reorder(self.trs_global, f=True)

        # add nodes to the container
        self.controlers += [self.trs_global, self.trs_shot, self.trs_motion]

    def rigSetup(self):
        """Add the self.rig setup"""
        # Setup the main scaling
        rigamajig2.maya.node.multMatrix([(self.trs_motion + '.matrix'),
                                         self.trs_shot + '.matrix',
                                         self.trs_global + '.matrix'],
                                        outputs=[self.rig_hrc, self.bind_hrc],
                                        t=True, r=True, s=True,
                                        name='main')

        # turn off inherit transform so we dont get double transformations
        cmds.setAttr("{}.{}".format(self.model_hrc, 'inheritsTransform'), 0)

        # Add the attribute for model override.
        ovrmod = rigamajig2.maya.attr.addEnum(self.trs_shot, longName='modDisplay',
                                              enum=['normal', 'template', 'reference'],
                                              value=2, keyable=False, channelBox=True)
        cmds.setAttr(self.model_hrc + '.overrideEnabled', 1)
        cmds.connectAttr(ovrmod, self.model_hrc + '.overrideDisplayType')

        # create some attributes for the geo and rig visablity
        modVisAttr = rigamajig2.maya.attr.addAttr(self.root_hrc, longName="model", attributeType='bool',
                                                  value=True, keyable=True, channelBox=True)
        rigVisAttr = rigamajig2.maya.attr.addAttr(self.root_hrc, longName="rig", attributeType='bool',
                                                  value=True, keyable=True, channelBox=True)
        cmds.connectAttr(modVisAttr, "{}.v".format(self.model_hrc))
        cmds.connectAttr(rigVisAttr, "{}.v".format(self.rig_hrc))

    def finalize(self):
        rigamajig2.maya.attr.lockAndHide(self.root_hrc, rigamajig2.maya.attr.TRANSFORMS + ['v'])
        rigamajig2.maya.attr.lock(self.rig_hrc, rigamajig2.maya.attr.TRANSFORMS)
        rigamajig2.maya.attr.lock(self.bind_hrc, rigamajig2.maya.attr.TRANSFORMS)
        rigamajig2.maya.attr.lock(self.model_hrc, rigamajig2.maya.attr.TRANSFORMS)

    def deleteSetup(self):
        if cmds.objExists(BIND_HRC_NAME):
            skel_children = cmds.listRelatives(BIND_HRC_NAME, c=True)
            if skel_children: cmds.parent(skel_children, world=True)

        if cmds.objExists(RIG_HRC_NAME):
            rig_children = cmds.listRelatives(RIG_HRC_NAME, c=True)
            if rig_children: cmds.parent(rig_children, world=True)

        if cmds.objExists(MOD_HRC_NAME):
            model_children = cmds.listRelatives(MOD_HRC_NAME, c=True)
            if model_children: cmds.parent(model_children, world=True)

        super(Main, self).deleteSetup()
