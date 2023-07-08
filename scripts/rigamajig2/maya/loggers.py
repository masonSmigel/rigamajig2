#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: loggers.py
    author: masonsmigel
    date: 07/2023
    discription: some utilities for working with loggers made in rigamajig

"""
import logging

logger = logging.getLogger(__name__)


def getAllRigamajigLoggers():
    """
    Return a list of all rigamajig loggers
    :return:
    """
    loggers = [logging.getLogger(name) for name in logging.root.manager.loggerDict]

    returnList = list()
    for logger in loggers:
        if logger.name.startswith("rigamajig2"):
            returnList.append(logger)
    return returnList


def setLoggingLevel(level):
    """
    Set the logging level of all rigamajig loggers
    :return:
    """

    for logger in getAllRigamajigLoggers():
        logger.setLevel(level=level)
        logger.info(f"Logging Level Changed to: {level}")
