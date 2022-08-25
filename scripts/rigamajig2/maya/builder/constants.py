#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: constants.py
    author: masonsmigel
    date: 08/2022
    discription: 

"""
import os
# BUILD ENVIORNMENT GLOBLALS


CMPT_PATH = os.path.abspath(os.path.join(__file__, '../../cmpts'))
_EXCLUDED_FOLDERS = ['face']
_EXCLUDED_FILES = ['__init__.py', 'base.py']

# RIG FILE KEYS
BASE_ARCHETYPE = 'archetype_parent'
PRE_SCRIPT = 'pre_script'
POST_SCRIPT = 'post_script'
PUB_SCRIPT = 'pub_script'
RIG_NAME = 'rig_name'
MODEL_FILE = "model_file"
SKELETON_FILE = "skeleton_file"
SKELETON_POS = "skeleton_pos"
CONTROL_SHAPES = "control_shapes"
GUIDES = "guides"
COMPONENTS = "components"
SKINS = 'skins'
PSD = 'psd'
OUTPUT_RIG = 'output_file'
OUTPUT_RIG_FILE_TYPE = 'output_file_type'