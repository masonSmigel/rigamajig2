#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: __init__.py.py
    author: masonsmigel
    date: 07/2022

"""

from rigamajig2.shared import logger


class Builder_Logger(logger.Logger):
    LOGGER_NAME = __name__
