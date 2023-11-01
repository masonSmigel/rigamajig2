#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: configureLoggers.py.py
    author: masonsmigel
    date: 10/2023
    description: setup all loggers for rigamajig

"""
import json
import logging
import logging.config
import logging.handlers
import os


def configureLoggers():
    # Get the absolute path of the script's directory
    rootDirectory = os.path.dirname(os.path.abspath(__file__))
    loggerConfigFilePath = os.path.join(rootDirectory, 'logging_config.json')

    with open(loggerConfigFilePath, 'r') as f:
        config = json.load(f)

    # this helps us save logs into the log directory
    # set the current working directory to the project root
    projectRoot = os.path.join(rootDirectory, "../../")
    os.chdir(projectRoot)

    # we need to ensure the log file exists
    logFilePath = os.path.join(projectRoot, "logs")
    if not os.path.exists(logFilePath):
        os.makedirs(os.path.join(projectRoot, "logs"))

    logging.config.dictConfig(config)
