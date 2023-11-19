import maya.cmds as cmds

from rigamajig2.maya import file


def main():
    file.new(f=True)
    cmds.setAttr('perspShape.focalLength', 55)


if __name__ == "__main__":
    main()

