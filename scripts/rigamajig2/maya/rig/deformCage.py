#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: deformCage.py
    author: masonsmigel
    date: 12/2022
    discription: This module can be used to build a deformation cage for model

    NOTE: This function requires ngSkinTools

"""

import maya.cmds as cmds
import maya.api.OpenMaya as om2
import logging

from rigamajig2.maya.rig import control
from rigamajig2.shared import common
from rigamajig2.maya import meta
from rigamajig2.maya import mesh
from rigamajig2.maya import skinCluster
from rigamajig2.maya import joint
from rigamajig2.maya import transform
from rigamajig2.maya import mathUtils
from rigamajig2.maya import meshnav
from rigamajig2.maya import hierarchy

logger = logging.getLogger(__name__)


def createCageControlPoint(name, side=None, size=1, position=None, color='slategray', rotation=None, parent=None):
    """
    Build a single cageControlPoint

    :param name: name of the control point
    :param str side: Optional name of the side
    :param int float size: Optional- Size of the control
    :param list tuple position: Optional- Point in world space to position the control.
    :param list tuple rotation: Optional- Rotation in world space to rotate the control.
    :param str parent: Optional- Parent the control under this node in the hierarchy
    :param str int color: Optional- Color of the control

    return: control, bindJoint, bpmJoint
    """

    ctl = control.create(name, side, shape='sphere', orig=True, trs=True, parent=parent,
                         size=size, position=position, rotation=rotation, color=color)

    # create the bind joint and tag it
    bindJoint = cmds.createNode("joint", name="{}_bind".format(name), parent=ctl.name)
    meta.tag(bindJoint, "bind", type="cage")
    meta.createMessageConnection(ctl.name, bindJoint, "bindJoint")
    joint.setRadius(bindJoint, size * 0.5)

    # create the bpm joint and tag it
    bpmJoint = cmds.createNode("joint", name="{}_bpm".format(name), parent=ctl.trs)
    meta.tag(bpmJoint, "bpm", type="cage")
    meta.createMessageConnection(ctl.name, bpmJoint, "bpmJoint")
    joint.setRadius(bpmJoint, size * 0.5)
    joint.hideJoints([bpmJoint, bindJoint])

    return ctl, bindJoint, bpmJoint


def smoothSkinCluster(polyMesh, intensity=0.1, itterations=30):
    """
    Try to import Ngskintools and smooth the skin cluster

    :param polyMesh: name of the poly mesh to smooth
    :param intensity: set the intensity of the smooth value
    :param itterations: number of times to run the smooth
    :return:
    """

    try:
        pluginLoaded = cmds.pluginInfo("ngSkinTools2", q=True, loaded=True)
        if not pluginLoaded:
            cmds.loadPlugin("ngSkinTools2")
        import ngSkinTools2.api as ngst
    except:
        raise Warning("Unable to load ngSkinTools2 python module. Cannot smooth mesh {}".format(polyMesh))

    # we need a layer reference for this, so we'll take first layer from our sample mesh
    layers = ngst.init_layers(polyMesh)
    layer = layers.add("base weights")

    # build settings for the flood
    settings = ngst.FloodSettings()

    # smoothing does not require current influence
    settings.mode = ngst.PaintMode.smooth
    settings.intensity = intensity
    settings.iterations = itterations
    ngst.flood_weights(layer=layer, settings=settings)

    # delete the NGskin tools data from the scene
    skinClusterNode = skinCluster.getSkinCluster(polyMesh)
    ngSkinNodes = cmds.listConnections(skinClusterNode, type="ngst2SkinLayerData")
    cmds.delete(ngSkinNodes)


class DeformationCage(object):
    """
    Class to manage and create a deformation cage
    """

    def __init__(self, name, cageMesh, parent=None):
        """

        :param name: name of the deformation cage to build
        :param cageMesh: poly geometry that has been skinned to the skeleton
        :param parent: parent for the cageMesh hierarchy
        """
        self.name = name
        self.cageMesh = cageMesh
        self.parent = parent

        self.controlList = list()
        self.bindJointList = list()
        self.bpmJointList = list()

    def initalHierarchy(self):
        """
        Create the inital hierarchy for a deformation cage
        """
        rootName = "{}_cage".format(self.name)
        controlsName = "{}_cageControls".format(self.name)
        outputGeoName = "{}_output_cageGeo".format(self.name)

        # store the heirarchy into class variables to reuse later
        self.rootHierarchy = cmds.createNode("transform", name=rootName, parent=self.parent)
        self.controlsHierarchy = cmds.createNode("transform", name=controlsName, parent=self.rootHierarchy)
        self.outputGeoHierarchy = cmds.createNode("transform", name=outputGeoName, parent=self.rootHierarchy)

    def createCageControlPoints(self, size=1, color='slategray', orientToNormal=True):
        """
        Create a system of cage points for a given mesh
        :param size: set the size of the controls
        :param color:  set the color of the control points
        :param orientToNormal: orient the controls to the vertex normals
        """
        if not mesh.isMesh(self.cageMesh):
            raise ValueError("The provided mesh MUST be a polyMesh. {} is not a poly mesh".format(self.cageMesh))
        skin = skinCluster.getSkinCluster(self.cageMesh)
        if not skin:
            raise Exception("the input mesh: {} must have a skincluster.".format(self.cageMesh))

        # check the max influences for a skin cluster
        # if len(cmds.skinCluster(skin, q=True, mi=True)) > 2:
        #     raise Exception("The input mesh: {} must have a maximum influence of 2 or lower".format(self.cageMesh))

        # get a list of all the influences to use later
        influences = skinCluster.getInfluenceJoints(skin)

        # create a list to store the controls in
        controlsList = list()

        for vtx in mesh.getVerts(self.cageMesh):
            # first lets retreive the vertex weights for each vertex
            vertexWeights = cmds.skinPercent(skin, vtx, q=True, v=True)

            # next we can loop through each list of weights anf get the influences and their values.
            # then we'll build a dictionary of influences and their weights for each vertex.
            # Keep in mind this should be limited to TWO influences per joint
            weightDict = dict()
            for i in range(len(vertexWeights)):
                weight = vertexWeights[i]
                if weight > 0:
                    influence = influences[i]
                    weightDict[influence] = weight

            # now with that lets create out control
            vertexId = vtx.split("[")[-1].split("]")[0]
            componentId = int(vertexId)

            # get the vertex position
            mfnMesh = mesh.getMeshFn(self.cageMesh)

            position = mfnMesh.getPoint(componentId, om2.MSpace.kWorld)

            # if we want to orient the control as well construct a rotation from the vertex normal
            rotation = None
            if orientToNormal:
                vtxNormal = mesh.getVertexNormal(self.cageMesh, componentId, world=True)
                mtxConstruct = (vtxNormal.x, vtxNormal.y, vtxNormal.z, 0,
                                0, 1, 0, 0,
                                0, 0, 1, 0,
                                0, 0, 0, 1
                                )
                vtxMMatrix = om2.MMatrix(mtxConstruct)
                vtxMtransMtx = om2.MTransformationMatrix(vtxMMatrix)
                rotationRadians = vtxMtransMtx.rotation(asQuaternion=False)
                rotation = mathUtils.radToDegree(rotationRadians)

            # create the cage point
            ctl, bind, bpm = createCageControlPoint(
                name="{}_cage_{}".format(self.name, vertexId),
                size=size,
                position=[position.x, position.y, position.z],
                rotation=rotation,
                parent=self.controlsHierarchy,
                color=color
                )

            # connect the control to the influences of the skinCluster
            currentInfluences = list(weightDict.keys())
            if len(currentInfluences) > 1:
                weight = weightDict[currentInfluences[-1]]
                driver1 = currentInfluences[0]
                driver2 = currentInfluences[-1]
                transform.blendedOffsetParentMatrix(driver1, driver2, ctl.orig, mo=True, blend=weight)
            else:
                transform.connectOffsetParentMatrix(currentInfluences[0], ctl.orig, mo=True)

            # add the important data to out lists
            self.controlList.append(ctl)
            self.bindJointList.append(bind)
            self.bpmJointList.append(bpm)

        logger.info("Create a new control cage with {} points".format(len(self.controlList)))

    def createConnectivityDisplay(self):
        """
        Create a connectivity mesh to help display our cage
        """

        conectivityMap = list()
        for i in range(len(mesh.getVerts(self.cageMesh))):
            connectedVerts = meshnav.getConnectedVerticies(self.cageMesh, i)
            # for each connected vert check if there is already a connection between those two verts.
            # we can do this by counting the number of times the inverse appears, if its zero append the point.
            for vert in connectedVerts:
                connectedPoint = [i, vert]
                inversePoint = connectedPoint[::-1]
                if conectivityMap.count(inversePoint) == 0:
                    conectivityMap.append(connectedPoint)

        cageTransform = cmds.createNode("transform", name="{}_cageDisplay".format(self.cageMesh),
                                        parent=self.rootHierarchy)
        cmds.setAttr("{}.overrideEnabled".format(cageTransform), True)
        cmds.setAttr("{}.overrideDisplayType".format(cageTransform), 1)
        for point in conectivityMap:
            # Now we can use the connectivity map to grab controls. The controls are created int he same vertex order as the
            # mesh so the ids will match up with the index in the list.
            control1 = self.controlList[point[0]].name
            control2 = self.controlList[point[1]].name

            lineName = "cageLine_{}_{}".format(point[0], point[1])
            displayLine = control.createDisplayLine(point1=control1, point2=control2, parent=None, name=lineName)
            shape = cmds.listRelatives(displayLine, s=True)[0]
            cmds.parent(shape, cageTransform, r=True, s=True)
            cmds.delete(displayLine)

    def connectToMeshes(self, meshesToBind=None):
        """
        create the output mesh
        """
        meshesToBind = common.toList(meshesToBind)

        lowOutput = cmds.duplicate(self.cageMesh, name="{}_low_output".format(self.name))[0]
        highOutput = cmds.duplicate(self.cageMesh, name="{}_high_output".format(self.name))[0]
        cmds.parent([lowOutput, highOutput], self.outputGeoHierarchy)

        # subdivide the high output a couple times so we can smooth it!
        cmds.polySubdivideFacet(highOutput, dv=1, m=False, ch=False)
        cmds.polySmooth(highOutput, dv=1, ch=False)

        # ensure the cage mesh and low output are hidden and the high output is showing
        cmds.hide(self.cageMesh, lowOutput)
        # cmds.show(highOutput)

        # bind the output meshes to the joints
        cmds.skinCluster(self.bindJointList, lowOutput, dr=1, mi=2, bm=1, name="{}_skinCluster".format(lowOutput))
        skinCluster.copySkinClusterAndInfluences(lowOutput, highOutput)

        # smooth the skin cluster
        smoothSkinCluster(highOutput, intensity=.1, itterations=20)

        # we also need to connect the bpm joints to the skinclusters before we copy it around
        highSkinCluster = skinCluster.getSkinCluster(highOutput)

        # now that we have the bind mesh we can
        for geo in meshesToBind:
            # create a duplicate to store the copied skin data
            tempDup = cmds.duplicate(geo, name="{}_tempToCopy".format(geo), renameChildren=True)
            cmds.parent(tempDup, world=True)

            # copy the skin data to the duplicate
            skinCluster.copySkinClusterAndInfluences(highOutput, tempDup)
            tempSkinCluster = skinCluster.getSkinCluster(tempDup)
            skinCluster.connectExistingBPMs(tempSkinCluster)

            cmds.rename(tempSkinCluster, "{}_cage_skinCluster".format(geo))

            # create a skincluster on the geo and move the influences there
            skinCluster.stackSkinCluster(tempDup, geo)

            # now we can delete the duplicate and move on to the next item
            cmds.delete(tempDup)

        logger.info("Connected and autoSkinned {} meshes".format(len(geo)))
