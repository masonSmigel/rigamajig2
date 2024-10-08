"""
main component
"""
import maya.cmds as cmds

from rigamajig2.maya import attr
from rigamajig2.maya import joint
from rigamajig2.maya import transform
from rigamajig2.maya.components.limb import limb
from rigamajig2.maya.rig import control
from rigamajig2.maya.rig import ikfk


class Leg(limb.Limb):
    """
    Leg Component  (subclass of the limb.limb)
    The leg component includes a foot.
    """

    VERSION_MAJOR = 1
    VERSION_MINOR = 1
    VERSION_PATCH = 0

    version_info = (VERSION_MAJOR, VERSION_MINOR, VERSION_PATCH)
    version = "%i.%i.%i" % version_info
    __version__ = version

    def __init__(self, name, input, size=1, rigParent=str(), componentTag=None):
        """
        :param str  name: component name. To add a side use a side token
        :param list input: list of 6 joints starting with the pelvis and ending with the toes.
        :param float int size: default size of the controls.
        :param str rigParent: connect the component to a rigParent.
        :param dict ikSpaces: dictionary of key and space for the ik control. formatted as {"attrName": object}
        :param dict pvSpaces: dictionary of key and space for the pv control. formatted as {"attrName": object}
        :param bool useProxyAttrs: use proxy attributes instead of an ikfk control
        """
        super(Leg, self).__init__(
            name, input=input, size=size, rigParent=rigParent, componentTag=componentTag
        )

        # TODO: jaw control names
        self.defineParameter(
            parameter="toes_fkName", value="toes_fk", dataType="string"
        )
        self.defineParameter(
            parameter="toes_ikName", value="toes_ik", dataType="string"
        )
        self.defineParameter(
            parameter="ball_ikName", value="ball_ik", dataType="string"
        )
        self.defineParameter(
            parameter="heel_ikName", value="heel_ik", dataType="string"
        )

        # noinspection PyTypeChecker
        if len(self.input) != 6:
            raise RuntimeError("Input list must have a length of 6")

    def _createBuildGuides(self):
        """create build guides_hrc"""
        super(Leg, self)._createBuildGuides()

        self.heelGuide = control.createGuide(
            "{}_heel".format(self.name), parent=self.guidesHierarchy
        )
        self.innGuide = control.createGuide(
            "{}_inn".format(self.name), parent=self.guidesHierarchy
        )
        self.outGuide = control.createGuide(
            "{}_out".format(self.name), parent=self.guidesHierarchy
        )
        self.ballGuide = control.createGuide(
            "{}_ball".format(self.name), parent=self.guidesHierarchy
        )
        self.toeGuide = control.createGuide(
            "{}_toe".format(self.name), parent=self.guidesHierarchy
        )

    def _autoOrientGuides(self):
        """Auto orient the foot pivot guides"""
        # auto aim the guides. these should ALWAYS be in world space.
        cmds.delete(
            cmds.aimConstraint(
                self.toeGuide,
                self.heelGuide,
                aimVector=(0, 0, 1),
                upVector=(0, 1, 0),
                worldUpType="scene",
                mo=False,
            )
        )
        transform.matchTransform(self.input[4], self.ballGuide)
        cmds.delete(
            cmds.aimConstraint(
                self.input[5],
                self.ballGuide,
                aimVector=(0, 0, 1),
                upVector=(0, 1, 0),
                worldUpType="scene",
                mo=False,
            )
        )
        cmds.delete(
            cmds.aimConstraint(
                self.heelGuide,
                self.toeGuide,
                aimVector=(0, 0, -1),
                upVector=(0, 1, 0),
                worldUpType="scene",
                mo=False,
            )
        )

    def _initialHierarchy(self):
        """Build the initial hierarchy"""
        super(Leg, self)._initialHierarchy()

        self.toesFk = control.createAtObject(
            self.toes_fkName,
            self.side,
            orig=True,
            hideAttrs=["v", "t", "s"],
            size=self.size,
            color="blue",
            parent=self.controlHierarchy,
            shape="square",
            shapeAim="x",
            xformObj=self.input[4],
        )
        # create ik pivot controls
        self.heelIk = control.createAtObject(
            self.heel_ikName,
            self.side,
            orig=True,
            hideAttrs=["v", "t", "s"],
            size=self.size,
            color="blue",
            parent=self.controlHierarchy,
            shape="cube",
            shapeAim="x",
            xformObj=self.heelGuide,
        )
        self.ballIk = control.createAtObject(
            self.ball_ikName,
            self.side,
            orig=True,
            hideAttrs=["v", "t", "s"],
            size=self.size,
            color="blue",
            parent=self.controlHierarchy,
            shape="cube",
            shapeAim="x",
            xformObj=self.ballGuide,
        )
        self.toesIk = control.createAtObject(
            self.toes_ikName,
            self.side,
            orig=True,
            hideAttrs=["v", "t", "s"],
            size=self.size,
            color="blue",
            parent=self.controlHierarchy,
            shape="cube",
            shapeAim="x",
            xformObj=self.toeGuide,
        )
        self.footPivotControls = [self.heelIk.name, self.ballIk.name, self.toesIk.name]
        self.ikControls += self.footPivotControls

    def _rigSetup(self):
        """Add the rig setup"""
        super(Leg, self)._rigSetup()
        # setup the foot Ik
        self.footIkFk = ikfk.IkFkFoot(
            jointList=self.input[3:],
            heelPivot=self.heelGuide,
            innPivot=self.innGuide,
            outPivot=self.outGuide,
        )
        self.footIkFk.setGroup(self.ikfk.getGroup())
        self.footIkFk.create(params=self.paramsHierarchy)
        ikfk.IkFkFoot.createFootRoll(
            self.footIkFk.getPivotDict(),
            self.footIkFk.getGroup(),
            params=self.paramsHierarchy,
        )

        # connect the Foot IKFK to the ankle IK
        cmds.parent(self._ikEndTgt, self.footIkFk.getPivotDict()["ankle"])
        cmds.parent(self.footIkFk.getPivotDict()["root"], self.limbGimbleIk.name)
        cmds.delete(cmds.listRelatives(self._ikEndTgt, ad=True, type="pointConstraint"))

        # add in the foot roll controllers
        cmds.parent(self.heelIk.orig, self.footIkFk.getPivotDict()["heel"])
        cmds.parent(self.footIkFk.getPivotDict()["ballSwivel"], self.heelIk.name)

        cmds.parent(self.toesIk.orig, self.footIkFk.getPivotDict()["end"])
        cmds.parent(self.footIkFk.getPivotDict()["ball"], self.toesIk.name)
        cmds.parent(self.footIkFk.getPivotDict()["toe"], self.toesIk.name)

        cmds.parent(self.ballIk.orig, self.footIkFk.getPivotDict()["ball"])
        cmds.parent(self.footIkFk.getPivotDict()["ankle"], self.ballIk.name, relative=True)

        # setup the toes
        transform.connectOffsetParentMatrix(
            self.footIkFk.getBlendJointList()[2], self.toesFk.orig, mo=True
        )
        # TODO: this is alittle hacky... maybe fix it later
        cmds.setAttr(
            "{}.{}".format(self.footIkFk.getIkJointList()[1], "segmentScaleCompensate"),
            0,
        )

    def _postRigSetup(self):
        """Connect the blend chain to the bind chain"""
        blendJoints = self.ikfk.getBlendJointList() + [self.toesFk.name]
        joint.connectChains(blendJoints, self.input[1:-1])
        attr.lock(self.input[-1], attr.TRANSFORMS + ["v"])
        ikfk.IkFkBase.connectVisibility(
            self.paramsHierarchy, "ikfk", ikList=self.ikControls, fkList=self.fkControls
        )

        if self.addTwistJoints:
            for jnt in [self.input[1], self.input[2]]:
                cmds.setAttr("{}.{}".format(jnt, "drawStyle"), 2)

        # connect the base to the main bind chain
        joint.connectChains(self.limbBase.name, self.input[0])

    def _setupAnimAttrs(self):
        """setup animation attributes"""


        # connect the foot ik attributes to the foot control
        attr.addSeparator(self.limbIk.name, "----")
        attr.driveAttribute("roll", self.paramsHierarchy, self.limbIk.name)
        if self.side == 'l':
            attr.driveAttribute("bank", self.paramsHierarchy, self.limbIk.name)
            attr.driveAttribute("ballSwivel", self.paramsHierarchy, self.limbIk.name)
        else:
            attr.driveAttribute("bank", self.paramsHierarchy, self.limbIk.name, multiplier=-1)
            attr.driveAttribute("ballSwivel", self.paramsHierarchy, self.limbIk.name, multiplier=-1)
        attr.driveAttribute("ballAngle", self.paramsHierarchy, self.limbIk.name)
        attr.driveAttribute("toeStraightAngle", self.paramsHierarchy, self.limbIk.name)

        attr.createAttr(
            self.limbIk.name,
            "footPivots",
            "bool",
            value=0,
            keyable=False,
            channelBox=True,
        )
        control.connectControlVisiblity(
            self.limbIk.name, "footPivots", self.footPivotControls
        )

        super(Leg, self)._setupAnimAttrs()

    def _connect(self):
        """Create the connection"""
        super(Leg, self)._connect()

    def _finalize(self):
        """Lock some attributes we don't want to see"""
        super(Leg, self)._finalize()
