#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: test_base_component.py
    author: masonsmigel
    date: 09/2023
    discription: 

"""

from rigamajig2.maya.components import base
from rigamajig2.maya.test.mayaTestCase import TestCase


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
