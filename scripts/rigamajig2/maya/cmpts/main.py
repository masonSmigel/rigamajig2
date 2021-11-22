"""
main component
"""
import maya.cmds as cmds
import rigamajig2.maya.cmpts.base
import rigamajig2.maya.rig.control as rig_control
import rigamajig2.maya.container
import rigamajig2.maya.node
import rigamajig2.maya.attr


class Main(rigamajig2.maya.cmpts.base.Base):
    def __init__(self, name, input=[], size=1):
        """
        Create a main control
        :param name:
        :param input:
        """
        super(Main, self).__init__(name=name, input=input)
        self.name = name
        self.size = size

    def initalHierachy(self):
        """Build the initial hirarchy"""
        self.root = cmds.createNode('transform', n=self.name)
        self.rig = cmds.createNode('transform', n='rig', parent=self.root)
        self.bind = cmds.createNode('transform', n='bind', parent=self.root)
        self.model = cmds.createNode('transform', n='model', parent=self.root)

        # Build our controls
        self.trs_global = rig_control.create('trs_global', hierarchy=[], size=self.size * 1.2,
                                             color='yellow', parent=self.root)[0]
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
                                        outputs=[self.rig, self.bind],
                                        t=True, r=True, s=True,
                                        name='main')

        # turn off inherit transform so we dont get double transformations
        cmds.setAttr("{}.{}".format(self.model, 'inheritsTransform'), 0)

        # Add the attribute for model override.
        ovrmod = rigamajig2.maya.attr.addEnum(self.trs_shot, longName='modDisplay',
                                              enum=['normal', 'template', 'reference'],
                                              value=2, keyable=False, channelBox=True)
        cmds.setAttr(self.model + '.overrideEnabled', 1)
        cmds.connectAttr(ovrmod, self.model + '.overrideDisplayType')

    def finalize(self):
        rigamajig2.maya.attr.lockAndHide(self.root, rigamajig2.maya.attr.TRANSFORMS + ['v'])
        rigamajig2.maya.attr.lock(self.rig, rigamajig2.maya.attr.TRANSFORMS)
        rigamajig2.maya.attr.lock(self.bind, rigamajig2.maya.attr.TRANSFORMS)
        rigamajig2.maya.attr.lock(self.model, rigamajig2.maya.attr.TRANSFORMS)
