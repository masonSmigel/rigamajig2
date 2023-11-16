#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: test_base.py
    author: masonsmigel
    date: 07/2022
    discription: 

"""

import os

from rigamajig2.maya import file
from rigamajig2.maya.builder import builder

ARCHETYPES_PATH = os.path.abspath(os.path.join(__file__, "../../../", "archetypes"))


def test_baseBuild():
    file.new(f=True)
    b = builder.Builder(os.path.join(ARCHETYPES_PATH, "base", "base.rig"))
    b.run()


def test_bipedBuild():
    file.new(f=True)
    b = builder.Builder(os.path.join(ARCHETYPES_PATH, "biped", "biped.rig"))
    b.run()


def test_propBuild():
    file.new(f=True)
    b = builder.Builder(os.path.join(ARCHETYPES_PATH, "prop", "prop.rig"))
    b.run()


def test_faceBuild():
    file.new(f=True)
    b = builder.Builder(os.path.join(ARCHETYPES_PATH, "face", "face.rig"))
    b.run()
