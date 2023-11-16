import os
from pathlib import Path

import maya.cmds as cmds

import rigamajig2.maya.data.curveData as curve_data


def test_saveAndLoad(tmp_path):
    """
    Test the import and export of curve data
    """
    print(tmp_path)

    file_path = str(Path(tmp_path) / "testCurveData.json")
    cmds.circle(name="testCircle")

    d = curve_data.CurveData()
    d.gatherData("testCircle")
    d.write(file_path)

    assert os.path.exists(file_path)

    cmds.delete("testCircle")
    cmds.createNode("transform", name="testCircle")

    d = curve_data.CurveData()
    d.read(file_path)
    d.applyData(["testCircle"], create=True)

    assert True
