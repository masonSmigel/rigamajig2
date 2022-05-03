"""This module contains performance Utils """
import maya.cmds as cmds

import random
import rigamajig2.maya.meta as meta
import rigamajig2.shared.common as common
import rigamajig2.maya.transform as rig_transform

SKIPS    = {"bool", "enum"}


def has_scale_token(node, attr):
    # attr = common.getFirstIndex(attr)
    scale_tokens = ["Mult", "Thickness", "Scale", "Factor"]
    result = filter(lambda x: x in cmds.attributeName("{}.{}".format(node, attr), l=True ), scale_tokens)
    return bool(len(result))


def generateRandomAnim(nodes=None, start=None, end=None, keysIncriment=10):
    """
    Generate random animation channels for nodes.
    If no nodes are provided use all controls in the scne
    :param nodes: nodes to animate
    :param start: Start time for random animation
    :param end: End time for random animation
    :param keysIncriment: incriment for how often keyframes are generated
    :return:
    """
    start = start or cmds.playbackOptions(q=True, ast=True)
    end = end or cmds.playbackOptions(q=True, aet=True)

    key_frames = range(int(start), int(end + 1), keysIncriment)

    nodes = nodes or meta.getTagged("control")

    if not isinstance(nodes, (list, tuple)):
        nodes = [nodes]

    for node in nodes:
        keyables = filter(lambda x: not cmds.getAttr("{}.{}".format(node, x), type=True) in SKIPS,
                          cmds.listAttr(node, k=True))
        translates = cmds.attributeQuery("translate", node=node, listChildren=True)
        rotates = cmds.attributeQuery("rotate", node=node, listChildren=True)
        scales = cmds.attributeQuery("scale", node=node, listChildren=True)

        for attr in keyables:
            if attr in scales or has_scale_token(node, attr):
                r_start, r_end = 1.0, 1.2
            elif attr in rotates or "Angle" in cmds.getAttr("{}.{}".format(node, attr), type=True):
                r_start, r_end = -10, 10
            elif attr in translates:
                r_start, r_end = -1, 1
            else:
                r_start, r_end = 0, 1

            r_start, r_end = map(float, [r_start, r_end])
            for frame in key_frames:
                value = random.uniform(r_start, r_end)
                cmds.setKeyframe(node, attribute=attr, v=value, t=frame)

    print("Generated Test animation for {} nodes with time range of {}-{}.".format(len(nodes), start, end))
