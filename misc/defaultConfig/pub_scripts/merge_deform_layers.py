#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: merge_deform_layers.py.py
    author: masonsmigel
    date: 10/2023
    description: merge deformation layers for all meshes in the scene

"""
from rigamajig2.maya import meta
from rigamajig2.maya.rig import deformLayer


def mergeDeformLayers() -> None:
    """Merge all deformation layers for all models"""

    if len(meta.getTagged("hasDeformLayers")) > 0:
        for mesh in meta.getTagged("hasDeformLayers"):
            layer = deformLayer.DeformLayer(mesh)
            layer.stackDeformLayers(cleanup=True)

mergeDeformLayers()