#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: pytestUtils.py.py
    author: masonsmigel
    date: 11/2023
    description: 

"""
from pathlib import Path
from typing import List, Any, Union


def getTempFilePath(tmp_path: str, filename: str) -> str:
    """
    Get a temp file path using the tmp_path fixture from pytest

    :param tmp_path: tmp_path fixture
    :param filename: filename to add to the tmp_path
    """

    return str(Path(tmp_path) / filename)


def assertListsAlmostEqual(list1: List[Any], list2: List[Any], tolerance: float = 1e-6) -> bool:
    """
    Check if two lists are almost equal element-wise within a specified tolerance.

    :param list1: First list
    :param list2: Second list
    :param tolerance: Tolerance level for the element-wise comparison
    :return: True if lists are almost equal, False otherwise
    """
    if len(list1) != len(list2):
        return False

    for a, b in zip(list1, list2):
        if abs(a - b) > tolerance:
            return False

    return True


def assertAlmostEqual(value1: Union[int, float], value2: Union[int, float], tolerance: float = 1e-3):
    """
    Assert that two values are almost equal within a specified tolerance.

    :param value1: First value
    :param value2: Second value
    :param tolerance: Tolerance level for the comparison
    """
    if abs(value1 - value2) > tolerance:
        raise AssertionError(f"Values are not almost equal: {value1} and {value2}")

    return True
