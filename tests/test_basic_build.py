import os
import rigamajig2.maya.data.curve_data as curve_data
import maya.cmds as cmds

from rigamajig2.maya.test.mayaunittest import TestCase

import rigamajig2.maya.rig.builder as buider


class TestBasicRigBuild(TestCase):

    def test_simple_biped(self):
        """
        build a simple biped rig
        """

        self.load_plugin('quatNodes')
        self.load_plugin('matrixNodes')
        import rigamajig2.maya.cmpts.arm as arm
        import rigamajig2.maya.cmpts.leg as leg
        import rigamajig2.maya.cmpts.limb as limb
        import rigamajig2.maya.cmpts.main as main
        import rigamajig2.maya.cmpts.spine as spine
        import rigamajig2.maya.cmpts.neck as neck
        import rigamajig2.maya.cmpts.hand as hand

        archetype_path = (os.path.abspath(os.path.join(os.path.dirname(__file__),"../archetypes/biped/biped.rig")))

        main = main.Main('main', size=15)
        spine = spine.Spine('spine', input=['hips_bind', 'spine_0_bind', 'spine_1_bind', 'spine_2_bind', 'spine_3_bind', 'spine_4_bind', 'spine_5_bind', 'chest_bind'], size=4)
        neck = neck.Neck('neck', input=['neck_0_bind', 'neck_1_bind', 'neck_2_bind', 'neck_3_bind', 'head_bind'], size=4, rigParent='chestTop')
        arm_R = arm.Arm('arm_r', input=['clavical_r_bind', 'shoulder_r_bind', 'elbow_r_bind', 'wrist_r_bind'], size=4)
        arm_L = arm.Arm('arm_l', input=['clavical_l_bind', 'shoulder_l_bind', 'elbow_l_bind', 'wrist_l_bind'], size=4)
        leg_L = leg.Leg('leg_l', input=['pelivs_l_bind', 'thigh_l_bind', 'knee_l_bind', 'ankle_l_bind', 'ball_l_bind', 'toes_l_bind'], size=4)
        leg_R = leg.Leg('leg_r', input=['pelivs_r_bind', 'thigh_r_bind', 'knee_r_bind', 'ankle_r_bind', 'ball_r_bind', 'toes_r_bind'], size=4)

        hand_l = hand.Hand('hand_l', input=['pinky_0_l_bind', 'ring_0_l_bind', 'middle_0_l_bind', 'index_0_l_bind', 'thumb_0_l_bind'], rigParent='wrist_l_bind')
        hand_r = hand.Hand('hand_r', input=['pinky_0_r_bind', 'ring_0_r_bind', 'middle_0_r_bind', 'index_0_r_bind', 'thumb_0_r_bind'], rigParent='wrist_r_bind')

        b = buider.Builder(archetype_path)
        b.set_cmpts([main, spine, neck, arm_L, arm_R, leg_L, leg_R, hand_l, hand_r])
        b.run()

        self.assertTrue(True)



