"""
Spaces module
"""

import maya.cmds as cmds

import rigamajig2.maya.attr as rig_attr
import rigamajig2.maya.matrix
import rigamajig2.maya.meta as meta
import rigamajig2.maya.node as rig_node
import rigamajig2.maya.transform as rig_transform
import rigamajig2.shared.common as common


def create(
    node, attrHolder=None, parent=None, spaceAttrName="space", defaultName="local"
):
    """
    Create a space switcher
    :param node: node to be constrained
    :type node: str
    :param attrHolder: node that holds the 'space' attribute
    :type attrHolder: str
    :param parent: parent for the transforms created
    :type parent: str
    :param spaceAttrName: name of the attribute to hold the spaces. Default - 'space'
    :type spaceAttrName: str
    :param defaultName: name of the default space. Default - 'local'
    :type defaultName: str
    :return: Spaces group
    """
    if attrHolder is None:
        attrHolder = node

    if cmds.objExists("{}.spaceGroup".format(node)):
        raise RuntimeError(
            "node '{}' already has spaces attatched to it. use addSpace instead".format(
                node
            )
        )

    # Create our spaces group. This will store all our new spaces.
    grp = cmds.createNode("transform", n="{}_{}".format(node, "spaces"), parent=parent)
    cmds.setAttr("{}.{}".format(grp, "inheritsTransform"), 0)

    rig_node.decomposeMatrix(
        "{}.{}".format(node, "parentMatrix"),
        outputs=grp,
        translate=True,
        rotate=True,
        scale=True,
        name="{}_{}".format(node, "spaces"),
    )

    # Add the local space. This node that will inherit transform from the spaceGroup (parentNode.worldMatrix)
    rig_attr.createEnum(
        attrHolder,
        longName="space",
        niceName=spaceAttrName,
        enum=[defaultName],
        keyable=True,
    )
    localSpace = cmds.createNode(
        "transform", name="{}_{}".format(node, defaultName), parent=grp
    )
    rig_transform.matchTransform(node, localSpace)
    rig_attr.lockAndHide(localSpace, ["t", "r", "s", "v"])

    choice = rig_node.choice(
        selector="{}.{}".format(attrHolder, "space"),
        choices=["{}.{}".format(localSpace, "worldMatrix")],
        name="{}_{}".format(node, "spaces"),
    )

    multMatrix, _ = rig_node.multMatrix(
        inputs=[
            "{}.{}".format(choice, "output"),
            "{}.{}".format(node, "parentInverseMatrix"),
        ],
        outputs=node,
        translate=True,
        rotate=True,
        name="{}_{}".format(node, "spaces"),
    )

    # make some meta data connections
    meta.createMessageConnection(attrHolder, node, "attrHolder")
    meta.createMessageConnection(choice, node, "choiceNode")
    meta.createMessageConnection(multMatrix, node, "multMatrixNode")
    meta.createMessageConnection(grp, node, "spaceGroup")

    rig_attr.lockAndHide(grp, ["t", "r", "s", "v"])
    return grp


def addSpace(node, targetList, nameList, constraintType="parent"):
    """
    Add a new space to the space switcher
    :param node:  node to be constrained
    :type node: str
    :param targetList: list of target spaces
    :type targetList: str| list
    :param nameList: list of names for the enum attribute
    :type nameList: str| list
    :param constraintType: constraining method. Valid Values are 'parent', 'orient'
    :type constraintType: str
    """
    if not isinstance(nameList, list):
        nameList = list(nameList)

    if cmds.objExists("{}.spaceGroup".format(node)):
        spaceGroup = meta.getMessageConnection(node + ".spaceGroup")
        attrHolder = meta.getMessageConnection(node + ".attrHolder")
        choice = meta.getMessageConnection(node + ".choiceNode")

    targetList = common.toList(targetList)
    nameList = common.toList(nameList)
    for target, name in zip(targetList, nameList):
        # Edit our enum attribute
        existingSpaces = cmds.attributeQuery("space", node=attrHolder, listEnum=True)[
            0
        ].split(":")
        if name in existingSpaces or target in existingSpaces:
            raise RuntimeError(
                'There is a space with that name in "{}.{}"'.format(attrHolder, "space")
            )
        cmds.addAttr(
            "{}.{}".format(attrHolder, "space"),
            e=True,
            enumName=":".join(existingSpaces + [name]),
        )

        # create a new space
        newSpace = cmds.createNode(
            "transform", name="{}_{}".format(node, name), parent=spaceGroup
        )
        rig_transform.matchTransform(node, newSpace)

        # connect the newspace
        offset = rigamajig2.maya.matrix.matrixMult(
            cmds.getAttr("{}.worldMatrix".format(newSpace)),
            cmds.getAttr("{}.worldInverseMatrix".format(target)),
        )
        if constraintType == "orient":
            rig_node.multMatrix(
                [offset, target + ".worldMatrix", spaceGroup + ".worldInverseMatrix"],
                newSpace,
                rotate=True,
                name="{}_{}".format(node, name),
            )
        else:
            rig_node.multMatrix(
                [offset, target + ".worldMatrix", spaceGroup + ".worldInverseMatrix"],
                newSpace,
                translate=True,
                rotate=True,
                name="{}_{}".format(node, name),
            )

        # connect the world matrix of the new space to our choice node.
        choiceInput = rig_attr.getNextAvailableElement(choice + ".input")
        cmds.connectAttr(newSpace + ".worldMatrix", choiceInput)

        # lock and hide attrs we dont need
        rig_attr.lockAndHide(newSpace, ["t", "r", "s", "v"])
