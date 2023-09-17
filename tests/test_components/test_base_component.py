#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: test_base_component.py
    author: masonsmigel
    date: 09/2023
    discription: 

"""

import os
import rigamajig2.maya.data.curve_data as curve_data
import maya.cmds as cmds

from rigamajig2.maya.test.mayaunittest import TestCase
from rigamajig2.maya.cmpts import base


class TestBaseComponent(TestCase):

    def test_rebuild_from_container(self):
        """
        This test will ensure that data is abstractly being maintained when build from the container
        :return:
        """
        name = "test"
        input = ["1", "2", "3"]
        size = 4
        rigParent = "thisControl"
        componentTag = None

        sourceComponent = base.Base(name=name, input=input, size=size, rigParent=rigParent, componentTag=componentTag)

        targetComponent = base.Base.fromContainer(sourceComponent.getContainer())

        assert targetComponent.name == sourceComponent.name
        assert targetComponent.input == sourceComponent.input
        assert targetComponent.size == sourceComponent.size
        assert targetComponent.rigParent == sourceComponent.rigParent
        assert targetComponent.componentTag == sourceComponent.componentTag
