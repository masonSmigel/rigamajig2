"""
main component
"""
import maya.cmds as cmds
import rigamajig2.maya.cmpts.limb
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


class Leg(rigamajig2.maya.cmpts.limb.Limb):
    def __init__(self, name, input=[], size=1, ikSpaces=dict(), pvSpaces=dict(), useProxyAttrs=True, useScale=True, rigParent=str()):
        """
        Create a main control
        :param name: name of the components
        :type name: str
        :param input: list of input joints. This must be a length of 4
        :type input: list
        :param size: default size of the controls:
        :type size: float
        :param: ikSpaces: dictionary of key and space for the ik control.
        :type ikSpaces: dict
        :param: pvSpaces: dictionary of key and space for the pv control.
        :type pvSpaces: dict
        """
        super(Leg, self).__init__(name, input=input, size=size, ikSpaces=ikSpaces, pvSpaces=pvSpaces,
                                  useProxyAttrs=useProxyAttrs,useScale=useScale, rigParent=rigParent)
        self.cmptSettings['toes_fkName'] = 'toes_fk'
        self.cmptSettings['toes_ikName'] = 'toes_ik'
        self.cmptSettings['ball_ikName'] = 'ball_ik'
        self.cmptSettings['heel_ikName'] = 'heel_ik'
        # noinspection PyTypeChecker
        if len(self.input) != 6:
            raise RuntimeError('Input list must have a length of 6')

    def setInitalData(self):
        self.cmptSettings['ikSpaces']['hip'] = self.cmptSettings['limbSwingName'] + '_' + self.side
        self.cmptSettings['pvSpaces']['foot'] = self.cmptSettings['limb_ikName'] + '_' + self.side

    def createBuildGuides(self):
        """ create build guides_hrc """
        super(Leg, self).createBuildGuides()

        self._heel_piv = rig_control.createGuide("{}_heel".format(self.name), parent=self.guides_hrc)
        self._inn_piv = rig_control.createGuide("{}_inn".format(self.name), parent=self.guides_hrc)
        self._out_piv = rig_control.createGuide("{}_out".format(self.name), parent=self.guides_hrc)
        self._ball_piv = rig_control.createGuide("{}_ball".format(self.name), parent=self.guides_hrc)
        self._toe_piv = rig_control.createGuide("{}_toe".format(self.name), parent=self.guides_hrc)

    def initalHierachy(self):
        """Build the initial hirarchy"""
        super(Leg, self).initalHierachy()
        self.toes_fk = rig_control.createAtObject(self.toes_fkName, self.side,
                                                  hierarchy=['trsBuffer'],
                                                  hideAttrs=['v', 't', 's'], size=self.size, color='blue',
                                                  parent=self.control_hrc, shape='square', shapeAim='x',
                                                  xformObj=self.input[4])
        # create ik piviot controls
        self.heel_ik = rig_control.createAtObject(self.heel_ikName, self.side,
                                                  hierarchy=['trsBuffer'],
                                                  hideAttrs=['v', 't', 's'], size=self.size, color='blue',
                                                  parent=self.control_hrc, shape='cube', shapeAim='x',
                                                  xformObj=self._heel_piv)
        self.ball_ik = rig_control.createAtObject(self.ball_ikName, self.side,
                                                  hierarchy=['trsBuffer'],
                                                  hideAttrs=['v', 't', 's'], size=self.size, color='blue',
                                                  parent=self.control_hrc, shape='cube', shapeAim='x',
                                                  xformObj=self._ball_piv)
        self.toes_ik = rig_control.createAtObject(self.toes_ikName, self.side,
                                                  hierarchy=['trsBuffer'],
                                                  hideAttrs=['v', 't', 's'], size=self.size, color='blue',
                                                  parent=self.control_hrc, shape='cube', shapeAim='x',
                                                  xformObj=self._toe_piv)

        self.ikControls += [self.heel_ik[-1], self.ball_ik[-1], self.toes_ik[-1]]

    def rigSetup(self):
        """Add the rig setup"""
        super(Leg, self).rigSetup()
        # setup the foot Ik
        self.footikfk = ikfk.IkFkFoot(jointList=self.input[3:],
                                      heelPivot=self._heel_piv, innPivot=self._inn_piv, outPivot=self._out_piv)
        self.footikfk.setGroup(self.ikfk.getGroup())
        self.footikfk.create()
        ikfk.IkFkFoot.createFootRoll(self.footikfk.getPivotList(), self.footikfk.getGroup())

        # connect the Foot IKFK to the ankle IK
        cmds.parent(self._ikEndTgt, self.footikfk.getPivotList()[6])
        cmds.parent(self.footikfk.getPivotList()[0], self.limbGimble_ik[-1])
        cmds.delete(cmds.listRelatives(self._ikEndTgt, ad=True, type='pointConstraint'))

        # add in the foot roll controllers
        cmds.parent(self.heel_ik[0], self.footikfk.getPivotList()[1])
        cmds.parent(self.footikfk.getPivotList()[2], self.heel_ik[-1])

        cmds.parent(self.toes_ik[0], self.footikfk.getPivotList()[4])
        cmds.parent(self.footikfk.getPivotList()[5], self.toes_ik[-1])
        cmds.parent(self.footikfk.getPivotList()[7], self.toes_ik[-1])

        cmds.parent(self.ball_ik[0], self.footikfk.getPivotList()[5])
        cmds.parent(self.footikfk.getPivotList()[6], self.ball_ik[-1])

        # setup the toes
        rig_transform.connectOffsetParentMatrix(self.footikfk.getBlendJointList()[2], self.toes_fk[0], mo=True)
        # TODO: this is alittle hacky... maybe fix it later
        cmds.setAttr("{}.{}".format(self.footikfk.getIkJointList()[1], 'segmentScaleCompensate'), 0)
        # Delete the proxy guides_hrc:
        cmds.delete(self.guides_hrc)

    def postRigSetup(self):
        """ Connect the blend chain to the bind chain"""
        blendedJointlist = self.ikfk.getBlendJointList() + [self.toes_fk[-1]]
        rigamajig2.maya.joint.connectChains(blendedJointlist, self.input[1:-1])
        rigamajig2.maya.attr.lock(self.input[-1], rigamajig2.maya.attr.TRANSFORMS + ['v'])
        ikfk.IkFkBase.connectVisibility(self.ikfk.getGroup(), 'ikfk', ikList=self.ikControls, fkList=self.fkControls)

        # connect the base to the main bind chain
        rigamajig2.maya.joint.connectChains(self.limbBase[-1], self.input[0])

    def setupAnimAttrs(self):
        """ setup animation attributes"""
        super(Leg, self).setupAnimAttrs()
        # connect the fook ik attributes to the foot control
        rigamajig2.maya.attr.addSeparator(self.limb_ik[-1], '----')
        rigamajig2.maya.attr.driveAttribute('roll', self.ikfk.getGroup(), self.limb_ik[-1])
        rigamajig2.maya.attr.driveAttribute('bank', self.ikfk.getGroup(), self.limb_ik[-1])
        rigamajig2.maya.attr.driveAttribute('ballAngle', self.ikfk.getGroup(), self.limb_ik[-1])
        rigamajig2.maya.attr.driveAttribute('toeStraightAngle', self.ikfk.getGroup(), self.limb_ik[-1])

    def connect(self):
        """Create the connection"""
        super(Leg, self).connect()

    def finalize(self):
        """ Lock some attributes we dont want to see"""
        super(Leg, self).finalize()
