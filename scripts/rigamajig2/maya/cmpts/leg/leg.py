"""
main component
"""
import maya.cmds as cmds
import rigamajig2.maya.cmpts.limb.limb
import rigamajig2.maya.rig.control as rig_control
import rigamajig2.maya.rig.spaces as spaces
import rigamajig2.maya.rig.ikfk as ikfk
import rigamajig2.maya.transform as rig_transform
import rigamajig2.shared.common as common
import rigamajig2.maya.meta as meta
import rigamajig2.maya.container
import rigamajig2.maya.node
import rigamajig2.maya.attr
import rigamajig2.maya.joint

import logging

logger = logging.getLogger(__name__)


class Leg(rigamajig2.maya.cmpts.limb.limb.Limb):
    """
    Leg Component  (sublcass of the limb.limb)
    The leg component includes a foot.
    """
    VERSION_MAJOR = 1
    VERSION_MINOR = 0
    VERSION_PATCH = 0

    version_info = (VERSION_MAJOR, VERSION_MINOR, VERSION_PATCH)
    version = '%i.%i.%i' % version_info
    __version__ = version

    def __init__(self, name, input, size=1, ikSpaces=None, pvSpaces=None, useProxyAttrs=True, useScale=True,
                 rigParent=str()):
        """
        :param str  name: component name. To add a side use a side token
        :param list input: list of 6 joints starting with the pelvis and ending with the toes.
        :param float int size: default size of the controls.
        :param str rigParent: connect the component to a rigParent.
        :param dict ikSpaces: dictionary of key and space for the ik control. formated as {"attrName": object}
        :param dict pvSpaces: dictionary of key and space for the pv control. formated as {"attrName": object}
        :param bool useProxyAttrs: use proxy attributes instead of an ikfk control
        """
        if ikSpaces is None:
            ikSpaces = dict()

        if pvSpaces is None:
            pvSpaces = dict()

        super(Leg, self).__init__(name, input=input, size=size, ikSpaces=ikSpaces, pvSpaces=pvSpaces,
                                  useProxyAttrs=useProxyAttrs, useScale=useScale, rigParent=rigParent)

        self.cmptSettings['toes_fkName'] = 'toes_fk'
        self.cmptSettings['toes_ikName'] = 'toes_ik'
        self.cmptSettings['ball_ikName'] = 'ball_ik'
        self.cmptSettings['heel_ikName'] = 'heel_ik'
        # noinspection PyTypeChecker
        if len(self.input) != 6:
            raise RuntimeError('Input list must have a length of 6')

    def setInitalData(self):
        side = "_{}".format(self.side) if self.side else ""
        self.cmptSettings['ikSpaces']['hip'] = self.cmptSettings['limbSwingName'] + side
        self.cmptSettings['pvSpaces']['foot'] = self.cmptSettings['limb_ikName'] + side

    def createBuildGuides(self):
        """ create build guides_hrc """
        super(Leg, self).createBuildGuides()

        self.heelGuide = rig_control.createGuide("{}_heel".format(self.name), parent=self.guidesHierarchy)
        self.innGuide = rig_control.createGuide("{}_inn".format(self.name), parent=self.guidesHierarchy)
        self.outGuide = rig_control.createGuide("{}_out".format(self.name), parent=self.guidesHierarchy)
        self.ballGuide = rig_control.createGuide("{}_ball".format(self.name), parent=self.guidesHierarchy)
        self.toeGuide = rig_control.createGuide("{}_toe".format(self.name), parent=self.guidesHierarchy)

    def initalHierachy(self):
        """Build the initial hirarchy"""
        super(Leg, self).initalHierachy()
        self.toesFk = rig_control.createAtObject(
            self.toes_fkName,
            self.side,
            orig=True,
            hideAttrs=['v', 't', 's'],
            size=self.size,
            color='blue',
            parent=self.controlHierarchy,
            shape='square',
            shapeAim='x',
            xformObj=self.input[4]
            )
        # create ik piviot controls
        self.heelIk = rig_control.createAtObject(
            self.heel_ikName,
            self.side,
            orig=True,
            hideAttrs=['v', 't', 's'],
            size=self.size,
            color='blue',
            parent=self.controlHierarchy,
            shape='cube',
            shapeAim='x',
            xformObj=self.heelGuide
            )
        self.ballIk = rig_control.createAtObject(
            self.ball_ikName,
            self.side,
            orig=True,
            hideAttrs=['v', 't', 's'],
            size=self.size,
            color='blue',
            parent=self.controlHierarchy,
            shape='cube',
            shapeAim='x',
            xformObj=self.ballGuide
            )
        self.toesIk = rig_control.createAtObject(
            self.toes_ikName,
            self.side,
            orig=True,
            hideAttrs=['v', 't', 's'],
            size=self.size,
            color='blue',
            parent=self.controlHierarchy,
            shape='cube',
            shapeAim='x',
            xformObj=self.toeGuide
            )

        self.ikControls += [self.heelIk.name, self.ballIk.name, self.toesIk.name]

    def rigSetup(self):
        """Add the rig setup"""
        super(Leg, self).rigSetup()
        # setup the foot Ik
        self.footikfk = ikfk.IkFkFoot(jointList=self.input[3:],
                                      heelPivot=self.heelGuide, innPivot=self.innGuide, outPivot=self.outGuide)
        self.footikfk.setGroup(self.ikfk.getGroup())
        self.footikfk.create(params=self.paramsHierarchy)
        ikfk.IkFkFoot.createFootRoll(self.footikfk.getPivotList(), self.footikfk.getGroup(), params=self.paramsHierarchy)

        # connect the Foot IKFK to the ankle IK
        cmds.parent(self._ikEndTgt, self.footikfk.getPivotList()[6])
        cmds.parent(self.footikfk.getPivotList()[0], self.limbGimbleIk.name)
        cmds.delete(cmds.listRelatives(self._ikEndTgt, ad=True, type='pointConstraint'))

        # add in the foot roll controllers
        cmds.parent(self.heelIk.orig, self.footikfk.getPivotList()[1])
        cmds.parent(self.footikfk.getPivotList()[2], self.heelIk.name)

        cmds.parent(self.toesIk.orig, self.footikfk.getPivotList()[4])
        cmds.parent(self.footikfk.getPivotList()[5], self.toesIk.name)
        cmds.parent(self.footikfk.getPivotList()[7], self.toesIk.name)

        cmds.parent(self.ballIk.orig, self.footikfk.getPivotList()[5])
        cmds.parent(self.footikfk.getPivotList()[6], self.ballIk.name)

        # setup the toes
        rig_transform.connectOffsetParentMatrix(self.footikfk.getBlendJointList()[2], self.toesFk.orig, mo=True)
        # TODO: this is alittle hacky... maybe fix it later
        cmds.setAttr("{}.{}".format(self.footikfk.getIkJointList()[1], 'segmentScaleCompensate'), 0)

    def postRigSetup(self):
        """ Connect the blend chain to the bind chain"""
        blendedJointlist = self.ikfk.getBlendJointList() + [self.toesFk.name]
        rigamajig2.maya.joint.connectChains(blendedJointlist, self.input[1:-1])
        rigamajig2.maya.attr.lock(self.input[-1], rigamajig2.maya.attr.TRANSFORMS + ['v'])
        ikfk.IkFkBase.connectVisibility(self.paramsHierarchy, 'ikfk', ikList=self.ikControls, fkList=self.fkControls)

        if self.addTwistJoints:
            for jnt in [self.input[1], self.input[2]]:
                cmds.setAttr("{}.{}".format(jnt, "drawStyle"), 2)

        # connect the base to the main bind chain
        rigamajig2.maya.joint.connectChains(self.limbBase.name, self.input[0])

    def setupAnimAttrs(self):
        """ setup animation attributes"""
        super(Leg, self).setupAnimAttrs()
        # connect the fook ik attributes to the foot control
        rigamajig2.maya.attr.addSeparator(self.limbIk.name, '----')
        rigamajig2.maya.attr.driveAttribute('roll', self.paramsHierarchy, self.limbIk.name)
        rigamajig2.maya.attr.driveAttribute('bank', self.paramsHierarchy, self.limbIk.name)
        rigamajig2.maya.attr.driveAttribute('ballAngle', self.paramsHierarchy, self.limbIk.name)
        rigamajig2.maya.attr.driveAttribute('toeStraightAngle', self.paramsHierarchy, self.limbIk.name)

    def connect(self):
        """Create the connection"""
        super(Leg, self).connect()

    def finalize(self):
        """ Lock some attributes we dont want to see"""
        super(Leg, self).finalize()

    @staticmethod
    def createInputJoints(name=None, side=None, numJoints=None):
        """static method to create input joints"""
        import rigamajig2.maya.naming as naming
        import rigamajig2.maya.joint as joint
        guidePostions = {
            "hip": (0, 70, 0),
            "thigh": (10, 0, 0),
            "knee": (0, -30, 2),
            "ankle": (0, -35, -2),
            "ball": (0, -5, 8),
            "toe": (0, 0, 6),
            }

        joints = list()
        parent = None
        for key in ['hip', 'thigh', 'knee', 'ankle', 'ball', 'toe']:
            name = naming.getUniqueName(key, side)
            jnt = cmds.createNode("joint", name=name + "_jnt")
            if parent:
                cmds.parent(jnt, parent)

            position = guidePostions[key]
            if side == 'r':
                position = (position[0] * -1, position[1], position[2])
            cmds.xform(jnt, objectSpace=True, t=position)

            # add the joints to the joint list
            joints.append(jnt)

            parent = jnt

        # orient the joints
        aimAxis = 'x'
        upAxis = 'z'
        hipsUpAxis = '-x'
        if side == 'r':
            aimAxis = '-x'
            upAxis = '-z'
            hipsUpAxis = 'x'
        joint.orientJoints(joints[0], aimAxis='-z', upAxis=hipsUpAxis, autoUpVector=False)
        joint.orientJoints(joints[1:4], aimAxis=aimAxis, upAxis=upAxis, autoUpVector=True)
        joint.orientJoints(joints[4:], aimAxis=aimAxis, upAxis=upAxis, autoUpVector=True)
        return joints
