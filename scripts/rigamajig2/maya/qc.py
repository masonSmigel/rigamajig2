"""This module contains performance Utils for quality control"""
import maya.cmds as cmds

import random
import rigamajig2.maya.meta as meta
import rigamajig2.shared.common as common
import rigamajig2.maya.transform as rig_transform

SKIPS = {"bool", "enum"}

SCALE_TOKENS = ["Mult", "Thickness", "Scale", "Factor"]


def hasScaleToken(node, attr):
    """
    Check if an attribute has a scale token.
    Scale tokens are specified within the SCALE_TOKENS constant.

    :param str node: node to check on
    :param str attr: attribute to check
    :return: bool if the attribute has a scale token
    """
    attr = cmds.attributeName("{}.{}".format(node, attr), l=True)
    for token in SCALE_TOKENS:
        if token in attr:
            return True
    return False


def generateRandomAnim(nodes=None, start=None, end=None, keysIncriment=10):
    """
    Generate random animation channels for nodes.
    If no nodes are provided use all controls in the scne

    :param list nodes: nodes to animate
    :param int start: Start time for random animation
    :param int end: End time for random animation
    :param int keysIncriment: incriment for how often keyframes are generated
    """
    start = start or cmds.playbackOptions(q=True, ast=True)
    end = end or cmds.playbackOptions(q=True, aet=True)

    keyFrames = range(int(start), int(end + 1), keysIncriment)

    nodes = nodes or meta.getTagged("control")

    if not isinstance(nodes, (list, tuple)):
        nodes = [nodes]

    for node in nodes:
        keyableAttrs = cmds.listAttr(node, k=True)
        if not keyableAttrs:
            continue
        keyables = [x for x in keyableAttrs if cmds.getAttr("{}.{}".format(node, x), type=True) not in SKIPS]

        translates = cmds.attributeQuery("translate", node=node, listChildren=True)
        rotates = cmds.attributeQuery("rotate", node=node, listChildren=True)
        scales = cmds.attributeQuery("scale", node=node, listChildren=True)

        for attr in keyables:
            if attr in scales or hasScaleToken(node, attr):
                timeStart, timeEnd = 1.0, 1.2
            elif attr in rotates or "Angle" in cmds.getAttr("{}.{}".format(node, attr), type=True):
                timeStart, timeEnd = -10, 10
            elif attr in translates:
                timeStart, timeEnd = -1, 1
            else:
                timeStart, timeEnd = 0, 1

            timeStart, timeEnd = map(float, [timeStart, timeEnd])
            for frame in keyFrames:
                value = random.uniform(timeStart, timeEnd)
                cmds.setKeyframe(node, attribute=attr, v=value, t=frame)

    print("Generated Test animation for {} nodes with time range of {}-{}.".format(len(nodes), start, end))


def runPerformanceTest():
    """
    wrapper to run the performace test within the maya evaluation toolkit.
    """
    import maya.app.evaluationToolkit.evaluationToolkit as et
    # query the playback speed, so we can set it back to default after the performace test.
    playbackSpeed = cmds.playbackOptions(q=True, ps=True)
    cmds.playbackOptions(ps=0.0)
    et.runEMPerformanceTest()
    cmds.playbackOptions(ps=playbackSpeed)
