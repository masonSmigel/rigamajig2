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
    """
    Component for the main hierarchy.
    This includes the base heirarchy of the main, model, rig and bind groups as well the global controls.
    """
    VERSION_MAJOR = 1
    VERSION_MINOR = 0
    VERSION_PATCH = 0

    version_info = (VERSION_MAJOR, VERSION_MINOR, VERSION_PATCH)
    version = '%i.%i.%i' % version_info
    __version__ = version

    def __init__(self, name, input=None, size=1, rigParent=None):
        """
        :param name: name of the component
        :param input: inputs to the component. This is ignored in the component but is required for base component.
        :param rigParent:
        """
        super(Main, self).__init__(name=name, input=input, size=size)

    def initialHierarchy(self):
        """Build the initial hirarchy"""
        self.rootHierarchy = cmds.createNode('transform', n=self.name)
        self.rigHierarchy = cmds.createNode('transform', n=RIG_HRC_NAME, parent=self.rootHierarchy)
        self.bindHierarchy = cmds.createNode('transform', n=BIND_HRC_NAME, parent=self.rootHierarchy)
        self.modelHierarchy = cmds.createNode('transform', n=MOD_HRC_NAME, parent=self.rootHierarchy)

        # Build our controls
        self.trsGlobal = rig_control.create('trs_global',
                                            orig=False,
                                            size=self.size * 1.2,
                                            color='yellow',
                                            parent=self.rootHierarchy)
        self.trsShot = rig_control.create('trs_shot', orig=False,
                                          size=self.size * 1.1,
                                          color='lightgreenyellow',
                                          parent=self.trsGlobal.name)
        self.trsMotion = rig_control.create('trs_motion', orig=False,
                                            size=self.size,
                                            color='yellowgreen',
                                            parent=self.trsShot.name)
        # add the trs to the top of our outliner
        cmds.reorder(self.trsGlobal.name, f=True)

        # add nodes to the container
        self.controlers += [self.trsGlobal.name, self.trsShot.name, self.trsMotion.name]

    def rigSetup(self):
        """Add the self.rig setup"""
        # Setup the main scaling
        rigamajig2.maya.node.multMatrix([self.trsMotion.name + '.matrix',
                                         self.trsShot.name + '.matrix',
                                         self.trsGlobal.name + '.matrix'],
                                        outputs=[self.rigHierarchy, self.bindHierarchy],
                                        t=True, r=True, s=True,
                                        name='main')

        # turn off inherit transform so we dont get double transformations
        cmds.setAttr("{}.{}".format(self.modelHierarchy, 'inheritsTransform'), 0)

        # Add the attribute for model override.
        ovrmod = rigamajig2.maya.attr.createEnum(self.trsShot.name,
                                                 longName='modDisplay',
                                                 enum=['normal', 'template', 'reference'],
                                                 value=0,
                                                 keyable=False,
                                                 channelBox=True)

        cmds.setAttr(self.modelHierarchy + '.overrideEnabled', 1)
        cmds.connectAttr(ovrmod, self.modelHierarchy + '.overrideDisplayType')

        # create some attributes for the geo and rig visablity
        modVisAttr = rigamajig2.maya.attr.createAttr(self.rootHierarchy,
                                                     longName="model",
                                                     attributeType='bool',
                                                     value=True,
                                                     keyable=True,
                                                     channelBox=True)

        rigVisAttr = rigamajig2.maya.attr.createAttr(self.rootHierarchy,
                                                     longName="rig",
                                                     attributeType='bool',
                                                     value=True,
                                                     keyable=True,
                                                     channelBox=True)

        bindVisAttr = rigamajig2.maya.attr.createAttr(self.rootHierarchy,
                                                      longName="bind",
                                                      attributeType='bool',
                                                      value=True,
                                                      keyable=True,
                                                      channelBox=True)

        cmds.connectAttr(modVisAttr, "{}.v".format(self.modelHierarchy))
        cmds.connectAttr(rigVisAttr, "{}.v".format(self.rigHierarchy))
        cmds.connectAttr(bindVisAttr, "{}.v".format(self.bindHierarchy))

    def finalize(self):
        rigamajig2.maya.attr.lockAndHide(self.rootHierarchy, rigamajig2.maya.attr.TRANSFORMS + ['v'])
        rigamajig2.maya.attr.lock(self.rigHierarchy, rigamajig2.maya.attr.TRANSFORMS)
        rigamajig2.maya.attr.lock(self.bindHierarchy, rigamajig2.maya.attr.TRANSFORMS)
        rigamajig2.maya.attr.lock(self.modelHierarchy, rigamajig2.maya.attr.TRANSFORMS)

        self.addMetadataToMain()

    def deleteSetup(self):
        if cmds.objExists(BIND_HRC_NAME):
            skeletonChildren = cmds.listRelatives(BIND_HRC_NAME, c=True)
            if skeletonChildren: cmds.parent(skeletonChildren, world=True)

        if cmds.objExists(RIG_HRC_NAME):
            rigChildren = cmds.listRelatives(RIG_HRC_NAME, c=True)
            if rigChildren: cmds.parent(rigChildren, world=True)

        if cmds.objExists(MOD_HRC_NAME):
            modelChildred = cmds.listRelatives(MOD_HRC_NAME, c=True)
            if modelChildred: cmds.parent(modelChildred, world=True)

        super(Main, self).deleteSetup()

    def addMetadataToMain(self):
        """
        Add some Meta data to the main group. This data includes:
        - The version of rigamajig used
        - The user who created the rig
        - The data and time at which the rig was created
        """
        import rigamajig2
        import getpass
        from time import gmtime, strftime

        rigamajig2.maya.attr.createAttr(self.rootHierarchy, "__rigamajigVersion__", "string",
                                        value=rigamajig2.version,
                                        keyable=False,
                                        locked=True
                                        )
        rigamajig2.maya.attr.createAttr(self.rootHierarchy, "__creationUser__", "string",
                                        value=getpass.getuser(),
                                        keyable=False,
                                        locked=True
                                        )
        rigamajig2.maya.attr.createAttr(self.rootHierarchy, "__creationDate__", "string",
                                        value=strftime("%Y-%m-%d %H:%M:%S", gmtime()),
                                        keyable=False,
                                        locked=True
                                        )
