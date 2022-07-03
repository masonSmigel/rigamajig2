#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: limb/build.py
    author: masonsmigel
    date: 07/2022

"""
import maya.cmds as cmds
import rigamajig2.sandbox.cmpts.base.build as build
import rigamajig2.maya.rig.control as control
import rigamajig2.maya.transform as transform
import rigamajig2.maya.mathUtils as mathUtils
import rigamajig2.maya.joint as joint
import rigamajig2.maya.meta as meta


class ComponentBuild(build.ComponentBuild):
    def __init__(self, container):
        super(ComponentBuild, self).__init__(container=container)

    def createRigSetup(self):
        self.initalHierarchy()
        self.rigSetup()

    def createBindJoints(self):
        """ create the bind joints"""
        guides = self.getGuides()
        bindJointNames = ["{}_{}_bind".format(jnt.split("_")[0], self.side) for jnt in guides[0:4]]

        bindJoints = joint.duplicateChain(guides[0:4], names=bindJointNames)

        meta.tag(bindJoints, "bind")
        self.bindJoints = bindJoints

    def initalHierarchy(self):
        """
        Build the inital heirarchy of the rig.
        """
        self.addDefaultHeirarchy()
        self.setupControls()

        self.fkControls = [self.joint1_fk[-1], self.joint2_fk[-1], self.joint3_fk[-1], self.joint3Gimble_fk[-1]]
        self.ikControls = [self.limb_ik[-1], self.limbGimble_ik[-1], self.limb_pv[-1]]
        self.controlers = [self.limbBase[-1], self.limbSwing[-1]] + self.fkControls + self.ikControls

        if self.addTwistJoints and self.addBendies:
            self.setupBendControls()
            self.bendControls = [b[-1] for b in [self.bend1, self.bend2, self.bend3, self.bend4, self.bend5]]

    def setupControls(self):
        """setup the controls"""
        guides = self.getGuides()
        guideBaseNames = [g.split("_")[0] for g in guides]
        basename = self.name.split("_")[0]

        hideAttrs = []
        if not self.addScale:
            hideAttrs = ['s']

        self.limbBase = control.createAtObject(name=guideBaseNames[0],
                                               side=self.side,
                                               hierarchy=['trsBuffer'],
                                               hideAttrs=['v'] + hideAttrs,
                                               size=self.size,
                                               color='blue',
                                               parent=self.control_hrc,
                                               shape='square',
                                               xformObj=guides[0])

        self.limbSwing = control.createAtObject(name=guideBaseNames[1] + "Swing",
                                                side=self.side,
                                                hierarchy=['trsBuffer', 'spaces_trs'],
                                                hideAttrs=['v', 's'],
                                                size=self.size,
                                                color='blue',
                                                parent=self.limbBase[-1],
                                                shape='square',
                                                xformObj=guides[1])
        # fk Controls
        self.joint1_fk = control.createAtObject(name=guideBaseNames[1] + "_fk",
                                                side=self.side,
                                                hierarchy=['trsBuffer', 'spaces_trs'],
                                                hideAttrs=['v', 't'] + hideAttrs,
                                                size=self.size,
                                                color='blue',
                                                parent=self.control_hrc,
                                                shape='circle',
                                                shapeAim='x',
                                                xformObj=guides[1])

        self.joint2_fk = control.createAtObject(name=guideBaseNames[2] + "_fk",
                                                side=self.side,
                                                hierarchy=['trsBuffer'],
                                                hideAttrs=['v', 't'] + hideAttrs,
                                                size=self.size,
                                                color='blue',
                                                parent=self.joint1_fk[-1],
                                                shape='circle',
                                                shapeAim='x',
                                                xformObj=guides[2])

        self.joint3_fk = control.createAtObject(name=guideBaseNames[3] + "_fk",
                                                side=self.side,
                                                hierarchy=['trsBuffer'],
                                                hideAttrs=['v', 't'] + hideAttrs,
                                                size=self.size,
                                                color='blue',
                                                parent=self.joint2_fk[-1],
                                                shape='circle',
                                                shapeAim='x',
                                                xformObj=guides[3])

        self.joint3Gimble_fk = control.createAtObject(name=guideBaseNames[3] + "Gimble_fk",
                                                      side=self.side,
                                                      hierarchy=['trsBuffer'],
                                                      hideAttrs=['v', 't', 's'],
                                                      size=self.size * 0.8,
                                                      color='blue',
                                                      parent=self.joint3_fk[-1],
                                                      shape='circle',
                                                      shapeAim='x',
                                                      xformObj=guides[3])

        # ikControls
        self.limb_ik = control.create(name=basename + "_ik",
                                      side=self.side,
                                      hierarchy=['trsBuffer', 'spaces_trs'],
                                      hideAttrs=['v'] + hideAttrs,
                                      size=self.size,
                                      color='blue',
                                      parent=self.control_hrc,
                                      shape='cube',
                                      position=cmds.xform(guides[3], q=True, ws=True, t=True))

        self.limbGimble_ik = control.create(name=basename + "Gimble_ik",
                                            side=self.side,
                                            hierarchy=['trsBuffer'],
                                            hideAttrs=['v'] + hideAttrs,
                                            size=self.size * 0.8,
                                            color='blue',
                                            parent=self.limb_ik[-1],
                                            shape='cube',
                                            position=cmds.xform(guides[3], q=True, ws=True, t=True))

        self.limb_pv = control.create(name=basename + "_pv",
                                      side=self.side,
                                      hierarchy=['trsBuffer', 'spaces_trs'],
                                      hideAttrs=['r', 's', 'v'],
                                      size=self.size,
                                      color='blue',
                                      shape='diamond',
                                      position=cmds.xform(guides[4], q=True, ws=True, t=True),
                                      parent=self.control_hrc,
                                      shapeAim='z')
        if not self.addProxyAttrs:
            self.ikfk_control = control.createAtObject(basename,
                                                       side=self.side,
                                                       hierarchy=['trsBuffer'],
                                                       hideAttrs=['t', 'r', 's', 'v'],
                                                       size=self.size,
                                                       color='lightorange',
                                                       shape='peakedCube',
                                                       xformObj=guides[3],
                                                       parent=self.control_hrc,
                                                       shapeAim='x')

    def setupBendControls(self):
        """ Setup the bend controls """
        guides = self.getGuides()
        basename = self.name.split("_")[0]

        self.bend_ctl_hrc = cmds.createNode("transform", n=self.name + "_bendControl", parent=self.control_hrc)

        self.bend1 = control.create(basename + "_1_bend",
                                    self.side,
                                    hierarchy=['trsBuffer'],
                                    hideAttrs=['v', 'r', 's'],
                                    size=self.size,
                                    color='blue',
                                    shape='circle',
                                    shapeAim='x',
                                    position=cmds.xform(guides[1], q=True, ws=True, t=True),
                                    parent=self.bend_ctl_hrc)

        self.bend2 = control.create(basename + "_2_bend",
                                    self.side,
                                    hierarchy=['trsBuffer'],
                                    hideAttrs=['v', 'r', 's'],
                                    size=self.size,
                                    color='blue',
                                    shape='circle',
                                    shapeAim='x',
                                    position=mathUtils.nodePosLerp(guides[1], guides[2], 0.5),
                                    parent=self.bend_ctl_hrc)

        self.bend3 = control.create(basename + "_3_bend",
                                    self.side,
                                    hierarchy=['trsBuffer'],
                                    hideAttrs=['v', 'r', 's'],
                                    size=self.size,
                                    color='blue',
                                    shape='circle',
                                    shapeAim='x',
                                    position=cmds.xform(guides[2], q=True, ws=True, t=True),
                                    parent=self.bend_ctl_hrc)

        self.bend4 = control.create(basename + "_4_bend",
                                    self.side,
                                    hierarchy=['trsBuffer'],
                                    hideAttrs=['v', 'r', 's'],
                                    size=self.size,
                                    color='blue',
                                    shape='circle',
                                    shapeAim='x',
                                    position=mathUtils.nodePosLerp(guides[2], guides[3], 0.5),
                                    parent=self.bend_ctl_hrc)

        self.bend5 = control.create(basename + "_5_bend",
                                    self.side,
                                    hierarchy=['trsBuffer'],
                                    hideAttrs=['v', 'r', 's'],
                                    size=self.size,
                                    color='blue',
                                    shape='circle',
                                    shapeAim='x',
                                    position=cmds.xform(guides[3], q=True, ws=True, t=True),
                                    parent=self.bend_ctl_hrc)

        # orient the bend controls
        bendAimList = [b[0] for b in [self.bend1, self.bend2, self.bend3, self.bend4, self.bend5]]
        aimAxis = transform.getAimAxis(guides[1], allowNegative=True)
        aimVector = transform.getVectorFromAxis(aimAxis)
        for i in range(len(bendAimList)):
            upVector = (0, 0, 1)
            if i == 4:
                aimVector = mathUtils.scalarMult(aimVector, -1)
                aimTgt = bendAimList[i - 1]
            else:
                aimTgt = bendAimList[i + 1]

            tmp = cmds.aimConstraint(aimTgt, bendAimList[i], aim=aimVector, u=upVector, wut='object',
                                     wuo=self.limb_pv[0], mo=False)
            cmds.delete(tmp)

    def rigSetup(self):
        """build the rig setup"""


if __name__ == '__main__':
    c = ComponentBuild("limb_l_container")
    c.initalHierarchy()
    print c.getGuides()
